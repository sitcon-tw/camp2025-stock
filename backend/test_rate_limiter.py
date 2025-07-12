#!/usr/bin/env python3
"""
Simple test for rate limiter functionality
"""
import time
from collections import defaultdict, deque
from typing import Dict

# Mock the rate limiter core logic without FastAPI dependencies
class TestRateLimiterCore:
    """Rate limiter core logic for testing"""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, ban_duration_seconds: int = 1800):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.ban_duration_seconds = ban_duration_seconds
        
        # Track failed attempts per IP
        self.failed_attempts: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Track banned IPs with ban timestamp
        self.banned_ips: Dict[str, float] = {}
        
        # Track total attempts per IP (for general rate limiting)
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
    
    def is_ip_banned(self, ip: str) -> bool:
        """Check if IP is currently banned"""
        if ip not in self.banned_ips:
            return False
        
        # Check if ban has expired
        ban_time = self.banned_ips[ip]
        if time.time() - ban_time > self.ban_duration_seconds:
            del self.banned_ips[ip]
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
            print(f"IP {ip} banned for {self.ban_duration_seconds} seconds after {attempt_count} failed attempts")
            
            # Clear failed attempts since IP is now banned
            self.failed_attempts[ip].clear()
    
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
            "max_attempts": self.max_attempts,
            "window_seconds": self.window_seconds,
            "ban_duration_seconds": self.ban_duration_seconds
        }

def test_rate_limiter():
    """Test rate limiter basic functionality"""
    print("Testing Rate Limiter Core Logic...")
    
    # Create limiter with test settings
    limiter = TestRateLimiterCore(max_attempts=3, window_seconds=60, ban_duration_seconds=300)
    
    # Test IP
    ip = '192.168.1.100'
    print(f"Testing IP: {ip}")
    
    # Check initial state
    assert not limiter.is_ip_banned(ip), "IP should not be banned initially"
    print("✓ Initial state: IP not banned")
    
    # Record failed attempts (under threshold)
    for i in range(2):
        limiter.record_failed_attempt(ip, '/api/admin/login')
        assert not limiter.is_ip_banned(ip), f"IP should not be banned after {i+1} attempts"
    print("✓ IP not banned after 2 failed attempts")
    
    # Record the attempt that should trigger ban
    limiter.record_failed_attempt(ip, '/api/admin/login')
    assert limiter.is_ip_banned(ip), "IP should be banned after 3 attempts"
    print("✓ IP banned after 3 failed attempts")
    
    # Check stats
    stats = limiter.get_stats()
    assert stats['active_bans'] == 1, "Should have 1 active ban"
    print("✓ Stats show 1 active ban")
    
    print("✅ All rate limiter tests passed!")

if __name__ == "__main__":
    test_rate_limiter()