"""
Rate limiting middleware with IP-based blocking for Fail2Ban protection
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Set
import time
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiterMiddleware:
    """Rate limiter with IP-based blocking and automatic ban management"""
    
    def __init__(self, 
                 max_attempts: int = 5,
                 window_seconds: int = 300,  # 5 minutes
                 ban_duration_seconds: int = 1800):  # 30 minutes
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.ban_duration_seconds = ban_duration_seconds
        
        # Track failed attempts per IP
        self.failed_attempts: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Track banned IPs with ban timestamp
        self.banned_ips: Dict[str, float] = {}
        
        # Track total attempts per IP (for general rate limiting)
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_old_records())
            except RuntimeError:
                # No event loop running, cleanup task will be started when middleware is used
                self._cleanup_task = None
    
    async def _cleanup_old_records(self):
        """Cleanup old records periodically"""
        while True:
            try:
                current_time = time.time()
                
                # Clean up expired bans
                expired_ips = [
                    ip for ip, ban_time in self.banned_ips.items()
                    if current_time - ban_time > self.ban_duration_seconds
                ]
                for ip in expired_ips:
                    del self.banned_ips[ip]
                    logger.info(f"IP {ip} unbanned after {self.ban_duration_seconds} seconds")
                
                # Clean up old failed attempts
                cutoff_time = current_time - self.window_seconds
                for ip in list(self.failed_attempts.keys()):
                    attempts = self.failed_attempts[ip]
                    while attempts and attempts[0] < cutoff_time:
                        attempts.popleft()
                    if not attempts:
                        del self.failed_attempts[ip]
                
                # Clean up old request counts
                for ip in list(self.request_counts.keys()):
                    requests = self.request_counts[ip]
                    while requests and requests[0] < cutoff_time:
                        requests.popleft()
                    if not requests:
                        del self.request_counts[ip]
                
                # Sleep for 60 seconds before next cleanup
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check X-Forwarded-For header first (for reverse proxy)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Get first IP in case of multiple proxies
            return forwarded_for.split(',')[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    def is_ip_banned(self, ip: str) -> bool:
        """Check if IP is currently banned"""
        if ip not in self.banned_ips:
            return False
        
        # Check if ban has expired
        ban_time = self.banned_ips[ip]
        if time.time() - ban_time > self.ban_duration_seconds:
            del self.banned_ips[ip]
            logger.info(f"IP {ip} unbanned after {self.ban_duration_seconds} seconds")
            return False
        
        return True
    
    def record_failed_attempt(self, ip: str, endpoint: str = None):
        """Record a failed authentication attempt"""
        current_time = time.time()
        self.failed_attempts[ip].append(current_time)
        
        # Clean old attempts
        cutoff_time = current_time - self.window_seconds
        while self.failed_attempts[ip] and self.failed_attempts[ip][0] < cutoff_time:
            self.failed_attempts[ip].popleft()
        
        # Check if IP should be banned
        attempt_count = len(self.failed_attempts[ip])
        if attempt_count >= self.max_attempts:
            self.banned_ips[ip] = current_time
            logger.warning(f"IP {ip} banned for {self.ban_duration_seconds} seconds after {attempt_count} failed attempts on {endpoint or 'unknown endpoint'}")
            
            # Clear failed attempts since IP is now banned
            self.failed_attempts[ip].clear()
    
    def record_request(self, ip: str):
        """Record a general request for rate limiting"""
        current_time = time.time()
        self.request_counts[ip].append(current_time)
        
        # Clean old requests
        cutoff_time = current_time - self.window_seconds
        while self.request_counts[ip] and self.request_counts[ip][0] < cutoff_time:
            self.request_counts[ip].popleft()
    
    def check_rate_limit(self, ip: str, max_requests: int = 100) -> bool:
        """Check if IP exceeds general rate limit"""
        return len(self.request_counts[ip]) < max_requests
    
    async def __call__(self, request: Request, call_next):
        """Middleware function"""
        # Start cleanup task if not running
        if self._cleanup_task is None:
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_old_records())
            except RuntimeError:
                pass  # Event loop not available
        
        ip = self.get_client_ip(request)
        
        # Check if IP is banned
        if self.is_ip_banned(ip):
            remaining_time = int(self.ban_duration_seconds - (time.time() - self.banned_ips[ip]))
            logger.warning(f"Blocked request from banned IP {ip}, {remaining_time} seconds remaining")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "IP temporarily banned due to too many failed attempts",
                    "retry_after": remaining_time
                }
            )
        
        # Record request for general rate limiting
        self.record_request(ip)
        
        # Check general rate limit (100 requests per 5 minutes)
        if not self.check_rate_limit(ip, max_requests=100):
            logger.warning(f"Rate limit exceeded for IP {ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": self.window_seconds
                }
            )
        
        response = await call_next(request)
        
        # Check for failed admin login
        if (request.url.path == "/api/admin/login" and 
            response.status_code == 401):
            self.record_failed_attempt(ip, "/api/admin/login")
        
        return response
    
    def get_stats(self) -> Dict:
        """Get current rate limiter statistics"""
        current_time = time.time()
        active_bans = {
            ip: int(self.ban_duration_seconds - (current_time - ban_time))
            for ip, ban_time in self.banned_ips.items()
            if current_time - ban_time < self.ban_duration_seconds
        }
        
        return {
            "active_bans": len(active_bans),
            "banned_ips": active_bans,
            "failed_attempts_tracked": len(self.failed_attempts),
            "request_counts_tracked": len(self.request_counts),
            "max_attempts": self.max_attempts,
            "window_seconds": self.window_seconds,
            "ban_duration_seconds": self.ban_duration_seconds
        }

# Global instance
rate_limiter = RateLimiterMiddleware()