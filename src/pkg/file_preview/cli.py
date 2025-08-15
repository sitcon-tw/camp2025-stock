#!/usr/bin/env python3
"""
File Preview CLI Tool

Command-line interface for the file preview package with sixel graphics support.
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pkg.file_preview import FilePreview, TerminalDetector


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Preview files in terminal with sixel graphics support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s image.jpg                    # Preview image using best available method
  %(prog)s image.png --width 400        # Preview with specific width
  %(prog)s --sixel image.gif            # Force sixel graphics (if supported)
  %(prog)s --ascii image.jpg            # Force ASCII art
  %(prog)s --batch /path/to/images      # Preview all images in directory
  %(prog)s --terminal-info              # Show terminal capabilities
  
Supported image formats: JPG, PNG, GIF, BMP, TIFF, WebP, ICO, PPM, PGM, PBM
        """
    )
    
    # File/directory arguments
    parser.add_argument('path', nargs='?', help='Path to file or directory to preview')
    
    # Display options
    parser.add_argument('--width', '-w', type=int, help='Target width in pixels')
    parser.add_argument('--height', type=int, help='Target height in pixels')
    
    # Format options
    parser.add_argument('--sixel', action='store_true', help='Force sixel graphics format')
    parser.add_argument('--ascii', action='store_true', help='Force ASCII art format')
    parser.add_argument('--text', action='store_true', help='Show text description only')
    
    # Batch processing
    parser.add_argument('--batch', '-b', action='store_true', 
                       help='Batch preview all supported files in directory')
    parser.add_argument('--pattern', '-p', default='*', 
                       help='File pattern for batch processing (default: *)')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Recursive directory scanning for batch processing')
    
    # ASCII options
    parser.add_argument('--ascii-width', type=int, default=80,
                       help='ASCII art width in characters (default: 80)')
    parser.add_argument('--ascii-height', type=int, default=40,
                       help='ASCII art height in characters (default: 40)')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable colored ASCII art')
    parser.add_argument('--high-contrast', action='store_true',
                       help='Enable high contrast for ASCII conversion')
    
    # Info and testing
    parser.add_argument('--terminal-info', '-i', action='store_true',
                       help='Show terminal capabilities and exit')
    parser.add_argument('--supported-formats', action='store_true',
                       help='List supported file formats and exit')
    parser.add_argument('--test-ascii', action='store_true',
                       help='Show ASCII character test pattern')
    
    # Advanced options
    parser.add_argument('--max-width', type=int, default=800,
                       help='Maximum image width in pixels (default: 800)')
    parser.add_argument('--max-height', type=int, default=600,
                       help='Maximum image height in pixels (default: 600)')
    
    args = parser.parse_args()
    
    # Handle info commands that don't require a file
    if args.terminal_info:
        show_terminal_info()
        return 0
    
    if args.supported_formats:
        show_supported_formats()
        return 0
    
    if args.test_ascii:
        test_ascii_chars(args.no_color)
        return 0
    
    # Validate path argument
    if not args.path:
        parser.error("Path argument is required (use --help for more information)")
    
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path '{path}' does not exist.", file=sys.stderr)
        return 1
    
    # Initialize file preview
    preview = FilePreview(max_width=args.max_width, max_height=args.max_height)
    
    # Determine format
    force_format = None
    if args.sixel:
        force_format = 'sixel'
    elif args.ascii:
        force_format = 'ascii'
    elif args.text:
        force_format = 'text'
    
    try:
        if args.batch:
            if not path.is_dir():
                print(f"Error: Path '{path}' is not a directory for batch processing.", file=sys.stderr)
                return 1
            
            success_count = preview.batch_preview(path, args.pattern, args.recursive)
            return 0 if success_count > 0 else 1
        else:
            # Single file preview
            success = preview.preview_file(path, args.width, args.height, force_format)
            return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def show_terminal_info():
    """Display terminal capability information."""
    detector = TerminalDetector()
    
    print("Terminal Capabilities Report")
    print("=" * 50)
    detector.print_terminal_info()
    
    print("\nOptimal Image Sizes:")
    optimal_size = detector.get_optimal_image_size()
    print(f"  Default (80% x 60%): {optimal_size[0]}x{optimal_size[1]} pixels")
    
    # Show different ratios
    for ratio_name, width_ratio, height_ratio in [
        ("Conservative", 0.6, 0.4),
        ("Large", 0.9, 0.8)
    ]:
        size = detector.get_optimal_image_size(width_ratio, height_ratio)
        print(f"  {ratio_name} ({int(width_ratio*100)}% x {int(height_ratio*100)}%): {size[0]}x{size[1]} pixels")
    
    if not detector.supports_sixel():
        print("\nFallback Options:")
        fallbacks = detector.suggest_fallback_formats()
        for fallback in fallbacks:
            print(f"  - {fallback}")


def show_supported_formats():
    """Display supported file formats."""
    preview = FilePreview()
    formats = preview.list_supported_formats()
    
    print("Supported Image Formats:")
    print("=" * 30)
    for fmt in formats:
        print(f"  {fmt}")
    
    print(f"\nTotal: {len(formats)} formats supported")
    
    print("\nSupported Text Formats:")
    print("=" * 30)
    text_formats = ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.xml', '.html', '.css']
    for fmt in text_formats:
        print(f"  {fmt}")


def test_ascii_chars(no_color: bool = False):
    """Display ASCII character test patterns."""
    from pkg.file_preview.ascii_art import AsciiArtRenderer
    
    renderer = AsciiArtRenderer()
    
    print("ASCII Character Test Pattern")
    print("=" * 50)
    
    # Test basic characters
    print("Character set (light to dark):")
    print(f"'{renderer.ascii_chars}'")
    print()
    
    # Test gradient
    print("Gradient test:")
    gradient = renderer.create_gradient_test(40, colored=not no_color)
    print(gradient)
    print()
    
    # Test text box
    print("Text box test:")
    test_text = "This is a test of the ASCII art text box rendering functionality."
    text_box = renderer.render_text_box(test_text, 60, colored=not no_color)
    print(text_box)


if __name__ == '__main__':
    sys.exit(main())