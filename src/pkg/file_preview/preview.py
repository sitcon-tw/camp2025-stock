"""
File Preview Module

Main interface for file preview functionality with automatic fallback
support for terminals that don't support sixel graphics.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union, List
from PIL import Image

from .sixel import SixelRenderer
from .terminal import TerminalDetector
from .ascii_art import AsciiArtRenderer


class FilePreview:
    """Main file preview class with automatic terminal detection and fallback."""
    
    SUPPORTED_IMAGE_FORMATS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
        '.webp', '.ico', '.ppm', '.pgm', '.pbm'
    }
    
    def __init__(self, max_width: int = 800, max_height: int = 600):
        """
        Initialize file preview with terminal detection.
        
        Args:
            max_width: Maximum image width in pixels
            max_height: Maximum image height in pixels
        """
        self.terminal = TerminalDetector()
        self.sixel_renderer = SixelRenderer(max_width, max_height)
        self.ascii_renderer = AsciiArtRenderer()
        
        # Get optimal size for current terminal
        optimal_width, optimal_height = self.terminal.get_optimal_image_size()
        self.max_width = min(max_width, optimal_width)
        self.max_height = min(max_height, optimal_height)
    
    def preview_file(self, file_path: Union[str, Path], width: Optional[int] = None,
                    height: Optional[int] = None, force_format: Optional[str] = None) -> bool:
        """
        Preview a file using the best available method for current terminal.
        
        Args:
            file_path: Path to the file to preview
            width: Target width (optional)
            height: Target height (optional)  
            force_format: Force specific preview format ('sixel', 'ascii', 'text')
            
        Returns:
            True if preview was successful, False otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"Error: File '{file_path}' not found.")
            return False
        
        if not file_path.is_file():
            print(f"Error: '{file_path}' is not a file.")
            return False
        
        # Determine preview method
        if self._is_image(file_path):
            return self._preview_image(file_path, width, height, force_format)
        else:
            return self._preview_text_file(file_path)
    
    def _is_image(self, file_path: Path) -> bool:
        """Check if file is a supported image format."""
        return file_path.suffix.lower() in self.SUPPORTED_IMAGE_FORMATS
    
    def _preview_image(self, image_path: Path, width: Optional[int],
                      height: Optional[int], force_format: Optional[str]) -> bool:
        """Preview an image file using the best available method."""
        try:
            # Display file information
            self._print_file_info(image_path)
            
            # Use forced format if specified
            if force_format == 'sixel':
                if self.terminal.supports_sixel():
                    return self._preview_image_sixel(image_path, width, height)
                else:
                    print("Warning: Sixel format requested but not supported by terminal.")
                    return False
            elif force_format == 'ascii':
                return self._preview_image_ascii(image_path, width, height)
            elif force_format == 'text':
                return True  # File info already printed
            
            # Auto-detect best method
            if self.terminal.supports_sixel():
                return self._preview_image_sixel(image_path, width, height)
            else:
                print("Sixel graphics not supported. Using ASCII art fallback.")
                return self._preview_image_ascii(image_path, width, height)
                
        except Exception as e:
            print(f"Error previewing image: {e}")
            return False
    
    def _preview_image_sixel(self, image_path: Path, width: Optional[int],
                            height: Optional[int]) -> bool:
        """Preview image using sixel graphics."""
        try:
            print("Displaying image using sixel graphics...")
            self.sixel_renderer.display_image(str(image_path), width, height)
            print()  # Add newline after image
            return True
        except Exception as e:
            print(f"Sixel rendering failed: {e}")
            return False
    
    def _preview_image_ascii(self, image_path: Path, width: Optional[int],
                            height: Optional[int]) -> bool:
        """Preview image using ASCII art."""
        try:
            print("Displaying image using ASCII art...")
            
            # Calculate ASCII dimensions based on terminal size
            cols, lines = self.terminal.get_terminal_size()
            
            if width is None:
                width = min(80, int(cols * 0.8))
            if height is None:
                height = min(40, int(lines * 0.6))
            
            ascii_art = self.ascii_renderer.image_to_ascii(
                str(image_path), width, height, 
                colored=self.terminal.supports_color()
            )
            
            print(ascii_art)
            return True
        except Exception as e:
            print(f"ASCII art rendering failed: {e}")
            return False
    
    def _preview_text_file(self, file_path: Path) -> bool:
        """Preview a text file."""
        try:
            self._print_file_info(file_path)
            
            # Get terminal size to determine how much to show
            _, lines = self.terminal.get_terminal_size()
            max_lines = max(10, lines - 10)  # Leave space for UI
            
            print(f"\nFirst {max_lines} lines:")
            print("-" * 50)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        print("... (file continues)")
                        break
                    print(line.rstrip())
            
            return True
        except Exception as e:
            print(f"Error reading text file: {e}")
            return False
    
    def _print_file_info(self, file_path: Path) -> None:
        """Print basic file information."""
        stat = file_path.stat()
        
        print(f"File: {file_path.name}")
        print(f"Path: {file_path}")
        print(f"Size: {self._format_file_size(stat.st_size)}")
        print(f"Modified: {self._format_timestamp(stat.st_mtime)}")
        
        if self._is_image(file_path):
            # Get image-specific info
            try:
                info = self.sixel_renderer.get_image_info(str(file_path))
                if 'error' not in info:
                    print(f"Dimensions: {info['width']}x{info['height']} pixels")
                    print(f"Format: {info['format']}")
                    print(f"Mode: {info['mode']}")
            except Exception:
                pass
        
        print()
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp in human-readable format."""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def list_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return sorted(list(self.SUPPORTED_IMAGE_FORMATS))
    
    def print_terminal_capabilities(self) -> None:
        """Print information about terminal capabilities."""
        print("Terminal Capabilities:")
        print("=" * 50)
        self.terminal.print_terminal_info()
        print()
        
        optimal_size = self.terminal.get_optimal_image_size()
        print(f"Optimal image size for this terminal: {optimal_size[0]}x{optimal_size[1]} pixels")
        
        if not self.terminal.supports_sixel():
            fallbacks = self.terminal.suggest_fallback_formats()
            print(f"Available fallback formats: {', '.join(fallbacks)}")
    
    def batch_preview(self, directory: Union[str, Path], pattern: str = "*",
                     recursive: bool = False) -> int:
        """
        Preview multiple files in a directory.
        
        Args:
            directory: Directory path to scan
            pattern: File pattern to match (default: "*")
            recursive: Scan subdirectories recursively
            
        Returns:
            Number of files successfully previewed
        """
        directory = Path(directory)
        
        if not directory.exists() or not directory.is_dir():
            print(f"Error: Directory '{directory}' not found.")
            return 0
        
        # Find matching files
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        # Filter for supported files
        supported_files = [f for f in files if f.is_file() and 
                          (self._is_image(f) or f.suffix.lower() in {'.txt', '.md', '.py', '.js', '.json'})]
        
        if not supported_files:
            print(f"No supported files found in '{directory}' matching pattern '{pattern}'")
            return 0
        
        print(f"Found {len(supported_files)} supported files")
        print("=" * 50)
        
        success_count = 0
        for i, file_path in enumerate(supported_files):
            print(f"\n[{i+1}/{len(supported_files)}]")
            if self.preview_file(file_path):
                success_count += 1
            
            # Pause between files (except for last one)
            if i < len(supported_files) - 1:
                try:
                    input("\nPress Enter to continue to next file (Ctrl+C to stop)...")
                except KeyboardInterrupt:
                    print("\nBatch preview stopped by user.")
                    break
        
        print(f"\nBatch preview complete. Successfully previewed {success_count}/{len(supported_files)} files.")
        return success_count