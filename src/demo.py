#!/usr/bin/env python3
"""
Example demonstration of the file preview package with sixel graphics.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from pkg.file_preview import FilePreview, TerminalDetector

def main():
    """Demonstrate file preview functionality."""
    print("File Preview Package Demonstration")
    print("=" * 50)
    
    # Initialize components
    detector = TerminalDetector()
    preview = FilePreview()
    
    # Show terminal capabilities
    print("\n1. Terminal Capabilities:")
    print("-" * 30)
    detector.print_terminal_info()
    
    # Show supported formats
    print("\n2. Supported Image Formats:")
    print("-" * 30)
    formats = preview.list_supported_formats()
    print(f"Total formats supported: {len(formats)}")
    print(f"Examples: {', '.join(formats[:6])}")
    
    # Test ASCII art with a simple pattern
    print("\n3. ASCII Art Demonstration:")
    print("-" * 30)
    from pkg.file_preview.ascii_art import AsciiArtRenderer
    ascii_renderer = AsciiArtRenderer()
    
    # Create gradient test
    gradient = ascii_renderer.create_gradient_test(width=30, colored=detector.supports_color())
    print("Gradient test pattern:")
    print(gradient)
    
    # Test text box
    print("\nText box example:")
    text_box = ascii_renderer.render_text_box(
        "This is a demonstration of ASCII art text box rendering with the file preview package.",
        width=60,
        colored=detector.supports_color()
    )
    print(text_box)
    
    # Preview test image if it exists
    print("\n4. Image Preview Test:")
    print("-" * 30)
    test_image = Path("test_image.png")
    if test_image.exists():
        print(f"Previewing {test_image}...")
        preview.preview_file(test_image)
    else:
        print("No test image found. Run the following to create one:")
        print("python -c \"from PIL import Image; Image.new('RGB', (100,100), 'red').save('test_image.png')\"")
    
    print("\n5. Command Line Usage Examples:")
    print("-" * 30)
    print("# Basic image preview:")
    print("python src/pkg/file_preview/cli.py image.jpg")
    print()
    print("# Force ASCII art mode:")
    print("python src/pkg/file_preview/cli.py --ascii image.png")
    print()
    print("# Batch preview directory:")
    print("python src/pkg/file_preview/cli.py --batch /path/to/images")
    print()
    print("# Check terminal capabilities:")
    print("python src/pkg/file_preview/cli.py --terminal-info")
    
    print(f"\nDemo complete! Terminal supports sixel: {detector.supports_sixel()}")

if __name__ == '__main__':
    main()