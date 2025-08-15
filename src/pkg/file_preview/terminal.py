"""
Terminal Detection and Capability Module

This module detects terminal capabilities and provides fallback options
for terminals that don't support sixel graphics.
"""

import os
import sys
import subprocess
import re
from typing import Optional, Dict, List


class TerminalDetector:
    """Detect terminal capabilities and support for graphics protocols."""
    
    def __init__(self):
        self.terminal_info = self._detect_terminal()
        
    def _detect_terminal(self) -> Dict[str, any]:
        """Detect current terminal and its capabilities."""
        info = {
            'name': 'unknown',
            'supports_sixel': False,
            'supports_color': False,
            'color_depth': 0,
            'size': (80, 24)  # default terminal size
        }
        
        # Get terminal name from environment
        term = os.environ.get('TERM', '').lower()
        term_program = os.environ.get('TERM_PROGRAM', '').lower()
        
        # Detect terminal type
        if 'xterm' in term:
            info['name'] = 'xterm'
            # XTerm with sixel support
            if self._check_sixel_support():
                info['supports_sixel'] = True
        elif 'mlterm' in term:
            info['name'] = 'mlterm'
            info['supports_sixel'] = True
        elif term_program == 'iterm.app':
            info['name'] = 'iterm2'
            info['supports_sixel'] = self._check_iterm_sixel()
        elif term_program == 'wezterm':
            info['name'] = 'wezterm'
            info['supports_sixel'] = True
        elif 'konsole' in term:
            info['name'] = 'konsole'
            info['supports_sixel'] = True
        elif 'alacritty' in term:
            info['name'] = 'alacritty'
            # Alacritty only supports sixel if compiled with feature
            info['supports_sixel'] = self._check_alacritty_sixel()
        
        # Check color support
        info['supports_color'] = self._check_color_support()
        info['color_depth'] = self._detect_color_depth()
        
        # Get terminal size
        info['size'] = self._get_terminal_size()
        
        return info
    
    def _check_sixel_support(self) -> bool:
        """Check if terminal supports sixel graphics by querying device attributes."""
        try:
            # Save current terminal settings
            old_settings = subprocess.run(['stty', '-g'], capture_output=True, text=True)
            if old_settings.returncode != 0:
                return False
                
            # Set terminal to raw mode for query
            subprocess.run(['stty', 'raw', '-echo'], check=True)
            
            try:
                # Query device attributes (DA1)
                sys.stdout.write('\033[c')
                sys.stdout.flush()
                
                # Read response with timeout
                import select
                if select.select([sys.stdin], [], [], 1.0)[0]:
                    response = sys.stdin.read(50)
                    # Look for sixel support indicator (4;...)
                    if '4;' in response or ';4;' in response:
                        return True
            finally:
                # Restore terminal settings
                subprocess.run(['stty'] + old_settings.stdout.strip().split(), check=True)
                
        except (subprocess.CalledProcessError, OSError, ImportError):
            pass
        
        return False
    
    def _check_iterm_sixel(self) -> bool:
        """Check if iTerm2 supports sixel (version 3.0+)."""
        try:
            # iTerm2 sets TERM_PROGRAM_VERSION
            version = os.environ.get('TERM_PROGRAM_VERSION', '')
            if version:
                major_version = int(version.split('.')[0])
                return major_version >= 3
        except (ValueError, IndexError):
            pass
        return False
    
    def _check_alacritty_sixel(self) -> bool:
        """Check if Alacritty was compiled with sixel support."""
        try:
            # Try to run alacritty with version flag to check features
            result = subprocess.run(['alacritty', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Look for sixel feature in version output
                return 'sixel' in result.stdout.lower()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False
    
    def _check_color_support(self) -> bool:
        """Check if terminal supports colors."""
        colorterm = os.environ.get('COLORTERM', '').lower()
        term = os.environ.get('TERM', '').lower()
        
        # Check for explicit color terminal indicators
        if colorterm in ('truecolor', '24bit'):
            return True
        if 'color' in term or 'xterm' in term:
            return True
        if os.environ.get('TERM_PROGRAM') in ('iTerm.app', 'WezTerm'):
            return True
            
        return False
    
    def _detect_color_depth(self) -> int:
        """Detect color depth support (8, 256, or 16777216 colors)."""
        colorterm = os.environ.get('COLORTERM', '').lower()
        term = os.environ.get('TERM', '').lower()
        
        # True color support
        if colorterm in ('truecolor', '24bit'):
            return 16777216
        
        # 256 color support
        if '256color' in term or 'xterm' in term:
            return 256
        
        # Basic 8 color support
        if 'color' in term:
            return 8
            
        return 0
    
    def _get_terminal_size(self) -> tuple:
        """Get terminal size in characters."""
        try:
            import shutil
            size = shutil.get_terminal_size()
            return (size.columns, size.lines)
        except (OSError, AttributeError):
            # Fallback to environment variables
            try:
                cols = int(os.environ.get('COLUMNS', '80'))
                lines = int(os.environ.get('LINES', '24'))
                return (cols, lines)
            except (ValueError, TypeError):
                return (80, 24)
    
    def supports_sixel(self) -> bool:
        """Check if current terminal supports sixel graphics."""
        return self.terminal_info['supports_sixel']
    
    def supports_color(self) -> bool:
        """Check if current terminal supports colors."""
        return self.terminal_info['supports_color']
    
    def get_terminal_name(self) -> str:
        """Get the detected terminal name."""
        return self.terminal_info['name']
    
    def get_color_depth(self) -> int:
        """Get the color depth (number of colors supported)."""
        return self.terminal_info['color_depth']
    
    def get_terminal_size(self) -> tuple:
        """Get terminal size as (columns, lines)."""
        return self.terminal_info['size']
    
    def get_optimal_image_size(self, max_width_ratio: float = 0.8, 
                              max_height_ratio: float = 0.6) -> tuple:
        """
        Get optimal image size for current terminal.
        
        Args:
            max_width_ratio: Maximum width as ratio of terminal width
            max_height_ratio: Maximum height as ratio of terminal height
            
        Returns:
            Tuple of (width_pixels, height_pixels)
        """
        cols, lines = self.get_terminal_size()
        
        # Estimate pixel size (common terminal font sizes)
        # Most terminals use 6-10 pixels per character width, 12-20 pixels per line
        char_width = 8  # pixels per character
        char_height = 16  # pixels per line
        
        max_width_pixels = int(cols * char_width * max_width_ratio)
        max_height_pixels = int(lines * char_height * max_height_ratio)
        
        return (max_width_pixels, max_height_pixels)
    
    def suggest_fallback_formats(self) -> List[str]:
        """Suggest fallback image display formats for non-sixel terminals."""
        fallbacks = []
        
        if not self.supports_sixel():
            if self.supports_color():
                if self.get_color_depth() >= 256:
                    fallbacks.extend(['ascii_color_256', 'ascii_color_8'])
                else:
                    fallbacks.append('ascii_color_8')
            else:
                fallbacks.append('ascii_mono')
            
            # Always include basic text description as last resort
            fallbacks.append('text_description')
        
        return fallbacks
    
    def print_terminal_info(self) -> None:
        """Print detailed terminal information."""
        info = self.terminal_info
        print(f"Terminal: {info['name']}")
        print(f"Sixel Support: {'Yes' if info['supports_sixel'] else 'No'}")
        print(f"Color Support: {'Yes' if info['supports_color'] else 'No'}")
        print(f"Color Depth: {info['color_depth']} colors")
        print(f"Terminal Size: {info['size'][0]}x{info['size'][1]} characters")
        
        if not info['supports_sixel']:
            fallbacks = self.suggest_fallback_formats()
            print(f"Suggested Fallbacks: {', '.join(fallbacks)}")