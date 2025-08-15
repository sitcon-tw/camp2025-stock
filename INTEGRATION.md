# Integration Guide for File Preview Package

## Quick Start

To integrate the sixel graphics file preview into your application:

### 1. Basic Usage

```python
from src.pkg.file_preview import FilePreview

# Initialize preview system
preview = FilePreview()

# Preview a single file
preview.preview_file("image.jpg")

# Batch preview directory
preview.batch_preview("/path/to/images")
```

### 2. Check Terminal Capabilities

```python
from src.pkg.file_preview import TerminalDetector

detector = TerminalDetector()
if detector.supports_sixel():
    print("High-quality sixel graphics available!")
else:
    print("Using ASCII art fallback")
```

### 3. Direct Sixel Rendering

```python
from src.pkg.file_preview import SixelRenderer

renderer = SixelRenderer(max_width=800, max_height=600)
sixel_data = renderer.render_image("image.jpg")
print(sixel_data)  # This will display the image in compatible terminals
```

### 4. CLI Integration

Add to your application's CLI:

```bash
# Check if sixel is supported
python src/pkg/file_preview/cli.py --terminal-info

# Preview files
python src/pkg/file_preview/cli.py image.jpg
```

## Terminal Compatibility

### Sixel Graphics Supported
- XTerm (with sixel enabled)
- MLterm  
- Konsole
- iTerm2 (3.0+)
- WezTerm
- Alacritty (with sixel feature)

### ASCII Art Fallback
- All other terminals with graceful fallback

## Dependencies

```bash
pip install Pillow>=9.0.0
```

## Example Output

The package automatically detects terminal capabilities and provides appropriate preview:

**Sixel-capable terminals**: High-quality images displayed inline
**Other terminals**: Colored ASCII art or monochrome fallback