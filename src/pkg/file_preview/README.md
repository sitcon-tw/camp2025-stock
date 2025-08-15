# File Preview Package with Sixel Graphics Protocol

A comprehensive terminal-based file preview system with support for the sixel graphics protocol, enabling high-definition image display directly in compatible terminals.

## Features

- **Sixel Graphics Support**: Display HD images directly in compatible terminals using the sixel graphics protocol
- **Automatic Terminal Detection**: Detects terminal capabilities and provides appropriate fallback options
- **ASCII Art Fallback**: High-quality ASCII art generation for terminals without sixel support
- **Multiple Image Formats**: Support for JPG, PNG, GIF, BMP, TIFF, WebP, ICO, PPM, PGM, PBM
- **Batch Processing**: Preview multiple files in directories with recursive scanning
- **CLI Interface**: Complete command-line tool for easy integration
- **Color Support**: Colored ASCII art for color-capable terminals

## Supported Terminals

### Sixel Graphics Support
- **XTerm** (with sixel support enabled)
- **MLterm**
- **Konsole**
- **iTerm2** (version 3.0+, limited support)
- **WezTerm**
- **Alacritty** (when compiled with sixel feature)

### ASCII Art Fallback
- All other terminals with color/monochrome ASCII art fallback

## Installation

1. Install dependencies:
```bash
pip install Pillow>=9.0.0
```

2. The package is ready to use directly from the source directory.

## Usage

### Command Line Interface

```bash
# Basic image preview (auto-detects best method)
python src/pkg/file_preview/cli.py image.jpg

# Force sixel graphics (if supported)
python src/pkg/file_preview/cli.py --sixel image.png

# Force ASCII art
python src/pkg/file_preview/cli.py --ascii image.gif

# Specify dimensions
python src/pkg/file_preview/cli.py --width 400 --height 300 image.jpg

# Batch preview all images in directory
python src/pkg/file_preview/cli.py --batch /path/to/images

# Recursive batch preview
python src/pkg/file_preview/cli.py --batch --recursive /path/to/images

# Show terminal capabilities
python src/pkg/file_preview/cli.py --terminal-info

# List supported formats
python src/pkg/file_preview/cli.py --supported-formats

# Test ASCII character rendering
python src/pkg/file_preview/cli.py --test-ascii
```

### Python API

```python
from pkg.file_preview import FilePreview, SixelRenderer, TerminalDetector

# Basic usage
preview = FilePreview()
preview.preview_file("image.jpg")

# Check terminal capabilities
detector = TerminalDetector()
if detector.supports_sixel():
    print("Sixel graphics supported!")
else:
    print("Using ASCII art fallback")

# Direct sixel rendering
renderer = SixelRenderer(max_width=800, max_height=600)
sixel_data = renderer.render_image("image.jpg", width=400)
print(sixel_data)

# Batch processing
preview.batch_preview("/path/to/images", recursive=True)
```

## Sixel Graphics Protocol

The sixel graphics protocol is a bitmap graphics format that encodes images as text sequences, allowing them to be displayed directly in terminal emulators. This implementation:

- Converts images to indexed color mode (up to 256 colors)
- Uses optimal color quantization for best quality
- Handles transparency and various image formats
- Automatically resizes images to fit terminal constraints
- Maintains aspect ratios during scaling

### How Sixel Works

1. **Color Palette**: The image is quantized to a 256-color palette
2. **Sixel Encoding**: Groups of 6 vertical pixels are encoded as single characters
3. **Escape Sequences**: ANSI escape sequences control color definitions and positioning
4. **Terminal Display**: Compatible terminals decode and display the image inline

## Architecture

```
src/pkg/file_preview/
├── __init__.py          # Package initialization
├── sixel.py             # Sixel graphics protocol implementation
├── terminal.py          # Terminal detection and capabilities
├── preview.py           # Main file preview interface
├── ascii_art.py         # ASCII art rendering fallback
├── cli.py               # Command-line interface
├── tests.py             # Test suite
├── requirements.txt     # Dependencies
└── README.md           # This documentation
```

### Key Components

- **SixelRenderer**: Core sixel graphics implementation
- **TerminalDetector**: Automatic terminal capability detection
- **FilePreview**: Main interface with fallback logic
- **AsciiArtRenderer**: High-quality ASCII art generation
- **CLI**: Complete command-line tool

## Testing

Run the test suite:

```bash
cd src/pkg/file_preview
python tests.py
```

Test sixel support in your terminal:

```bash
python cli.py --terminal-info
python cli.py --test-ascii
```

## Examples

### Display an Image

```bash
# Auto-detect best method
python cli.py photo.jpg

# Force specific format
python cli.py --sixel photo.png
python cli.py --ascii photo.gif --ascii-width 120
```

### Batch Preview

```bash
# Preview all images in current directory
python cli.py --batch .

# Recursive preview with pattern matching
python cli.py --batch --recursive --pattern "*.jpg" /home/user/photos
```

### Check Terminal Capabilities

```bash
python cli.py --terminal-info
```

Example output:
```
Terminal Capabilities:
==================================================
Terminal: xterm
Sixel Support: Yes
Color Support: Yes
Color Depth: 256 colors
Terminal Size: 120x30 characters

Optimal image size for this terminal: 768x384 pixels
```

## Performance Considerations

- **Image Size**: Large images are automatically resized for optimal performance
- **Color Quantization**: Uses high-quality algorithms for best visual results
- **Memory Usage**: Processes images efficiently with minimal memory footprint
- **Terminal Compatibility**: Graceful fallback ensures compatibility across terminals

## Troubleshooting

### Sixel Not Working

1. Check if your terminal supports sixel:
   ```bash
   python cli.py --terminal-info
   ```

2. For XTerm, ensure sixel support is enabled:
   ```bash
   xterm -xrm 'XTerm*decTerminalID: vt340'
   ```

3. Try forcing ASCII art mode:
   ```bash
   python cli.py --ascii image.jpg
   ```

### Poor Image Quality

1. Try adjusting image dimensions:
   ```bash
   python cli.py --width 600 image.jpg
   ```

2. For ASCII art, use high contrast mode:
   ```bash
   python cli.py --ascii --high-contrast image.jpg
   ```

### Terminal Detection Issues

The package includes fallback mechanisms, but you can force specific formats:

```bash
# Force sixel even if not detected
python cli.py --sixel image.jpg

# Force ASCII art
python cli.py --ascii image.jpg
```

## Contributing

This implementation focuses on:
- Standards compliance with sixel graphics protocol
- Robust terminal detection and fallback mechanisms
- High-quality image processing and rendering
- Comprehensive error handling and user feedback

## License

This package is part of the SITCON Camp 2025 project.