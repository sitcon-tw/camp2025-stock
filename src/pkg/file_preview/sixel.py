"""
Sixel Graphics Protocol Implementation

This module implements the sixel graphics protocol for rendering images
in compatible terminals. Sixel (six-pixel) is a bitmap graphics format
that allows displaying images directly in terminal emulators.

Supported terminals:
- XTerm (with sixel support)
- MLterm
- Konsole
- iTerm2 (limited support)
- Wezterm
- Alacritty (with sixel feature enabled)
"""

import sys
import io
from typing import Optional, Tuple, Union
from PIL import Image, ImageOps


class SixelRenderer:
    """Sixel graphics renderer for terminal image display."""
    
    def __init__(self, max_width: int = 800, max_height: int = 600):
        """
        Initialize the sixel renderer.
        
        Args:
            max_width: Maximum image width in pixels
            max_height: Maximum image height in pixels
        """
        self.max_width = max_width
        self.max_height = max_height
        
    def render_image(self, image_path: str, width: Optional[int] = None, 
                    height: Optional[int] = None) -> str:
        """
        Render an image as sixel graphics data.
        
        Args:
            image_path: Path to the image file
            width: Target width (optional, will maintain aspect ratio)
            height: Target height (optional, will maintain aspect ratio)
            
        Returns:
            Sixel graphics escape sequence as string
        """
        try:
            # Open and process the image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Resize image if needed
                img = self._resize_image(img, width, height)
                
                # Convert to sixel format
                return self._convert_to_sixel(img)
                
        except Exception as e:
            raise RuntimeError(f"Failed to render image {image_path}: {e}")
    
    def render_image_from_data(self, image_data: bytes, width: Optional[int] = None,
                              height: Optional[int] = None) -> str:
        """
        Render an image from raw image data as sixel graphics.
        
        Args:
            image_data: Raw image data as bytes
            width: Target width (optional)
            height: Target height (optional)
            
        Returns:
            Sixel graphics escape sequence as string
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                img = self._resize_image(img, width, height)
                return self._convert_to_sixel(img)
                
        except Exception as e:
            raise RuntimeError(f"Failed to render image from data: {e}")
    
    def _resize_image(self, img: Image.Image, width: Optional[int], 
                     height: Optional[int]) -> Image.Image:
        """Resize image maintaining aspect ratio within bounds."""
        original_width, original_height = img.size
        
        # Determine target dimensions
        if width and height:
            target_width, target_height = width, height
        elif width:
            aspect_ratio = original_height / original_width
            target_width, target_height = width, int(width * aspect_ratio)
        elif height:
            aspect_ratio = original_width / original_height
            target_width, target_height = int(height * aspect_ratio), height
        else:
            target_width, target_height = original_width, original_height
        
        # Apply maximum size constraints
        if target_width > self.max_width:
            aspect_ratio = target_height / target_width
            target_width = self.max_width
            target_height = int(self.max_width * aspect_ratio)
            
        if target_height > self.max_height:
            aspect_ratio = target_width / target_height
            target_height = self.max_height
            target_width = int(self.max_height * aspect_ratio)
        
        # Resize using high-quality resampling
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    def _convert_to_sixel(self, img: Image.Image) -> str:
        """Convert PIL Image to sixel graphics format."""
        # Convert to indexed color mode with optimal palette
        # Sixel supports up to 256 colors
        img_indexed = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        
        width, height = img_indexed.size
        palette = img_indexed.getpalette()
        
        # Start sixel sequence
        sixel_data = ["\033Pq"]  # Device Control String + sixel introducer
        
        # Define color palette
        colors_used = set()
        pixels = list(img_indexed.getdata())
        colors_used.update(pixels)
        
        for color_index in sorted(colors_used):
            if color_index < len(palette) // 3:
                r = palette[color_index * 3]
                g = palette[color_index * 3 + 1] 
                b = palette[color_index * 3 + 2]
                
                # Convert RGB to percentages for sixel
                r_pct = int((r / 255) * 100)
                g_pct = int((g / 255) * 100)
                b_pct = int((b / 255) * 100)
                
                sixel_data.append(f"#{color_index};2;{r_pct};{g_pct};{b_pct}")
        
        # Process image data in sixel format
        # Sixel processes 6 rows at a time
        for y in range(0, height, 6):
            for color_index in sorted(colors_used):
                sixel_data.append(f"#{color_index}")
                
                sixel_line = ""
                for x in range(width):
                    # Collect 6 pixels vertically
                    sixel_char = 0
                    for bit in range(6):
                        pixel_y = y + bit
                        if pixel_y < height:
                            pixel_index = pixel_y * width + x
                            if pixel_index < len(pixels) and pixels[pixel_index] == color_index:
                                sixel_char |= (1 << bit)
                    
                    # Convert to sixel character (offset by 63)
                    sixel_line += chr(sixel_char + 63)
                
                if sixel_line.strip(chr(63)):  # Only add non-empty lines
                    sixel_data.append(sixel_line)
            
            # Add carriage return and line feed for next sixel row
            if y + 6 < height:
                sixel_data.append("$-")  # CR + LF
        
        # End sixel sequence
        sixel_data.append("\033\\")  # String terminator
        
        return "".join(sixel_data)
    
    def display_image(self, image_path: str, width: Optional[int] = None,
                     height: Optional[int] = None, output_stream=None) -> None:
        """
        Display an image directly to terminal using sixel graphics.
        
        Args:
            image_path: Path to the image file
            width: Target width (optional)
            height: Target height (optional)
            output_stream: Output stream (default: sys.stdout)
        """
        if output_stream is None:
            output_stream = sys.stdout
            
        sixel_data = self.render_image(image_path, width, height)
        output_stream.write(sixel_data)
        output_stream.flush()
    
    def get_image_info(self, image_path: str) -> dict:
        """
        Get information about an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with image information
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'size_bytes': len(img.tobytes())
                }
        except Exception as e:
            return {'error': str(e)}