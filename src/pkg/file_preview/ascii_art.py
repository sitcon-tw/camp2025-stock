"""
ASCII Art Renderer Module

This module provides fallback image display using ASCII art for terminals
that don't support sixel graphics. Includes both monochrome and colored
ASCII art generation.
"""

import sys
from typing import Optional, Tuple
from PIL import Image, ImageEnhance


class AsciiArtRenderer:
    """Convert images to ASCII art for terminal display."""
    
    # ASCII characters ordered by density (lightest to darkest)
    ASCII_CHARS_DETAILED = "@%#*+=-:. "
    ASCII_CHARS_SIMPLE = "@#*+=-:. "
    
    # ANSI color codes
    ANSI_COLORS = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bright_black': '\033[90m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
        'reset': '\033[0m'
    }
    
    def __init__(self, ascii_chars: str = None):
        """
        Initialize ASCII art renderer.
        
        Args:
            ascii_chars: Custom ASCII character set for rendering
        """
        self.ascii_chars = ascii_chars or self.ASCII_CHARS_DETAILED
    
    def image_to_ascii(self, image_path: str, width: int = 80, height: int = 40,
                      colored: bool = False, high_contrast: bool = False) -> str:
        """
        Convert an image to ASCII art.
        
        Args:
            image_path: Path to the image file
            width: Target width in characters
            height: Target height in characters  
            colored: Whether to use ANSI colors
            high_contrast: Enhance contrast for better ASCII conversion
            
        Returns:
            ASCII art as string
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Enhance contrast if requested
                if high_contrast:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.5)
                
                # Resize image for ASCII conversion
                # Characters are taller than wide, so adjust aspect ratio
                aspect_ratio = img.width / img.height
                ascii_width = width
                ascii_height = int(height)
                
                # Adjust for character aspect ratio (typically 1:2)
                ascii_height = int(ascii_height * 0.5)
                
                img_resized = img.resize((ascii_width, ascii_height), Image.Resampling.LANCZOS)
                
                if colored:
                    return self._image_to_colored_ascii(img_resized)
                else:
                    return self._image_to_mono_ascii(img_resized)
                    
        except Exception as e:
            return f"Error converting image to ASCII: {e}"
    
    def _image_to_mono_ascii(self, img: Image.Image) -> str:
        """Convert image to monochrome ASCII art."""
        # Convert to grayscale
        img_gray = img.convert('L')
        pixels = list(img_gray.getdata())
        
        ascii_art = []
        width, height = img_gray.size
        
        for y in range(height):
            row = ""
            for x in range(width):
                pixel_index = y * width + x
                pixel_value = pixels[pixel_index]
                
                # Map pixel value to ASCII character
                char_index = int((pixel_value / 255) * (len(self.ascii_chars) - 1))
                row += self.ascii_chars[char_index]
            
            ascii_art.append(row)
        
        return '\n'.join(ascii_art)
    
    def _image_to_colored_ascii(self, img: Image.Image) -> str:
        """Convert image to colored ASCII art using ANSI escape codes."""
        # Convert to RGB
        img_rgb = img.convert('RGB')
        width, height = img_rgb.size
        
        ascii_art = []
        
        for y in range(height):
            row = ""
            for x in range(width):
                r, g, b = img_rgb.getpixel((x, y))
                
                # Calculate luminance for ASCII character selection
                luminance = int(0.299 * r + 0.587 * g + 0.114 * b)
                char_index = int((luminance / 255) * (len(self.ascii_chars) - 1))
                char = self.ascii_chars[char_index]
                
                # Get nearest ANSI color
                color_code = self._get_nearest_ansi_color(r, g, b)
                
                # Add colored character
                row += f"{color_code}{char}"
            
            # Reset color at end of line
            row += self.ANSI_COLORS['reset']
            ascii_art.append(row)
        
        return '\n'.join(ascii_art)
    
    def _get_nearest_ansi_color(self, r: int, g: int, b: int) -> str:
        """Get the nearest ANSI color code for RGB values."""
        # Simple color mapping to basic ANSI colors
        colors = [
            (0, 0, 0, 'black'),
            (128, 0, 0, 'red'),
            (0, 128, 0, 'green'),
            (128, 128, 0, 'yellow'),
            (0, 0, 128, 'blue'),
            (128, 0, 128, 'magenta'),
            (0, 128, 128, 'cyan'),
            (192, 192, 192, 'white'),
            (128, 128, 128, 'bright_black'),
            (255, 0, 0, 'bright_red'),
            (0, 255, 0, 'bright_green'),
            (255, 255, 0, 'bright_yellow'),
            (0, 0, 255, 'bright_blue'),
            (255, 0, 255, 'bright_magenta'),
            (0, 255, 255, 'bright_cyan'),
            (255, 255, 255, 'bright_white')
        ]
        
        min_distance = float('inf')
        nearest_color = 'white'
        
        for cr, cg, cb, color_name in colors:
            # Calculate Euclidean distance in RGB space
            distance = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_color = color_name
        
        return self.ANSI_COLORS[nearest_color]
    
    def create_gradient_test(self, width: int = 50, colored: bool = False) -> str:
        """Create a gradient test pattern for ASCII character testing."""
        if colored:
            result = []
            for i in range(len(self.ascii_chars)):
                char = self.ascii_chars[i]
                # Create rainbow gradient
                if i < len(self.ascii_chars) // 6:
                    color = self.ANSI_COLORS['red']
                elif i < len(self.ascii_chars) // 3:
                    color = self.ANSI_COLORS['yellow']
                elif i < len(self.ascii_chars) // 2:
                    color = self.ANSI_COLORS['green']
                elif i < 2 * len(self.ascii_chars) // 3:
                    color = self.ANSI_COLORS['cyan']
                elif i < 5 * len(self.ascii_chars) // 6:
                    color = self.ANSI_COLORS['blue']
                else:
                    color = self.ANSI_COLORS['magenta']
                
                line = color + char * width + self.ANSI_COLORS['reset']
                result.append(line)
            return '\n'.join(result)
        else:
            result = []
            for char in self.ascii_chars:
                result.append(char * width)
            return '\n'.join(result)
    
    def render_text_box(self, text: str, width: int = 60, 
                       colored: bool = False, border_char: str = '*') -> str:
        """Render text in an ASCII art box."""
        lines = text.split('\n')
        
        # Ensure all lines fit within width
        wrapped_lines = []
        for line in lines:
            if len(line) <= width - 4:  # Account for border and padding
                wrapped_lines.append(line)
            else:
                # Simple word wrapping
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) <= width - 4:
                        current_line += (" " if current_line else "") + word
                    else:
                        if current_line:
                            wrapped_lines.append(current_line)
                        current_line = word
                if current_line:
                    wrapped_lines.append(current_line)
        
        # Create the box
        color_start = self.ANSI_COLORS['cyan'] if colored else ""
        color_end = self.ANSI_COLORS['reset'] if colored else ""
        
        result = []
        
        # Top border
        result.append(color_start + border_char * width + color_end)
        
        # Content lines
        for line in wrapped_lines:
            padding = width - len(line) - 2
            left_pad = padding // 2
            right_pad = padding - left_pad
            
            content = (color_start + border_char + color_end + 
                      " " * left_pad + line + " " * right_pad + 
                      color_start + border_char + color_end)
            result.append(content)
        
        # Bottom border
        result.append(color_start + border_char * width + color_end)
        
        return '\n'.join(result)