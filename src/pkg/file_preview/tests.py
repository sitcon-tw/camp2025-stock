"""
Test Suite for File Preview Package

Tests for sixel graphics protocol implementation and fallback functionality.
"""

import unittest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pkg.file_preview import FilePreview, SixelRenderer, TerminalDetector
from pkg.file_preview.ascii_art import AsciiArtRenderer


class TestSixelRenderer(unittest.TestCase):
    """Test cases for SixelRenderer class."""
    
    def setUp(self):
        self.renderer = SixelRenderer(max_width=400, max_height=300)
    
    def test_init(self):
        """Test SixelRenderer initialization."""
        self.assertEqual(self.renderer.max_width, 400)
        self.assertEqual(self.renderer.max_height, 300)
    
    def test_image_resize_calculation(self):
        """Test image resize calculations."""
        # Create a mock image
        mock_img = MagicMock()
        mock_img.size = (800, 600)
        
        # Test resize with width constraint
        resized = self.renderer._resize_image(mock_img, width=200, height=None)
        mock_img.resize.assert_called_once()
        
        # Verify resize was called with correct dimensions
        resize_args = mock_img.resize.call_args[0][0]
        self.assertEqual(resize_args[0], 200)  # width
        self.assertEqual(resize_args[1], 150)  # height (aspect ratio maintained)


class TestTerminalDetector(unittest.TestCase):
    """Test cases for TerminalDetector class."""
    
    def setUp(self):
        self.detector = TerminalDetector()
    
    def test_terminal_detection(self):
        """Test basic terminal detection."""
        self.assertIsInstance(self.detector.get_terminal_name(), str)
        self.assertIsInstance(self.detector.supports_color(), bool)
        self.assertIsInstance(self.detector.get_color_depth(), int)
    
    @patch.dict('os.environ', {'TERM': 'xterm-256color'})
    def test_xterm_detection(self):
        """Test XTerm detection from environment."""
        detector = TerminalDetector()
        self.assertEqual(detector.get_terminal_name(), 'xterm')
        self.assertTrue(detector.supports_color())
        self.assertEqual(detector.get_color_depth(), 256)
    
    @patch.dict('os.environ', {'TERM_PROGRAM': 'iTerm.app', 'TERM_PROGRAM_VERSION': '3.4.0'})
    def test_iterm_detection(self):
        """Test iTerm2 detection."""
        detector = TerminalDetector()
        self.assertEqual(detector.get_terminal_name(), 'iterm2')
    
    def test_optimal_image_size(self):
        """Test optimal image size calculation."""
        size = self.detector.get_optimal_image_size()
        self.assertIsInstance(size, tuple)
        self.assertEqual(len(size), 2)
        self.assertGreater(size[0], 0)
        self.assertGreater(size[1], 0)
    
    def test_fallback_suggestions(self):
        """Test fallback format suggestions."""
        fallbacks = self.detector.suggest_fallback_formats()
        self.assertIsInstance(fallbacks, list)
        if not self.detector.supports_sixel():
            self.assertGreater(len(fallbacks), 0)


class TestAsciiArtRenderer(unittest.TestCase):
    """Test cases for AsciiArtRenderer class."""
    
    def setUp(self):
        self.renderer = AsciiArtRenderer()
    
    def test_init(self):
        """Test AsciiArtRenderer initialization."""
        self.assertIsInstance(self.renderer.ascii_chars, str)
        self.assertGreater(len(self.renderer.ascii_chars), 0)
    
    def test_gradient_test(self):
        """Test gradient test pattern generation."""
        gradient = self.renderer.create_gradient_test(width=20)
        self.assertIsInstance(gradient, str)
        self.assertIn('\n', gradient)
    
    def test_gradient_test_colored(self):
        """Test colored gradient test pattern."""
        gradient = self.renderer.create_gradient_test(width=20, colored=True)
        self.assertIsInstance(gradient, str)
        self.assertIn('\033[', gradient)  # Should contain ANSI escape codes
    
    def test_text_box_rendering(self):
        """Test text box rendering."""
        text = "Test message"
        box = self.renderer.render_text_box(text, width=20)
        self.assertIsInstance(box, str)
        self.assertIn(text, box)
        lines = box.split('\n')
        self.assertGreaterEqual(len(lines), 3)  # At least top, content, bottom
    
    def test_nearest_ansi_color(self):
        """Test ANSI color matching."""
        # Test pure red
        color = self.renderer._get_nearest_ansi_color(255, 0, 0)
        self.assertIn('\033[', color)  # Should be ANSI escape sequence
        
        # Test black
        color = self.renderer._get_nearest_ansi_color(0, 0, 0)
        self.assertIn('\033[', color)


class TestFilePreview(unittest.TestCase):
    """Test cases for FilePreview class."""
    
    def setUp(self):
        self.preview = FilePreview(max_width=400, max_height=300)
    
    def test_init(self):
        """Test FilePreview initialization."""
        self.assertIsInstance(self.preview.terminal, TerminalDetector)
        self.assertIsInstance(self.preview.sixel_renderer, SixelRenderer)
        self.assertIsInstance(self.preview.ascii_renderer, AsciiArtRenderer)
    
    def test_supported_formats(self):
        """Test supported file format detection."""
        formats = self.preview.list_supported_formats()
        self.assertIsInstance(formats, list)
        self.assertIn('.jpg', formats)
        self.assertIn('.png', formats)
        self.assertIn('.gif', formats)
    
    def test_is_image_detection(self):
        """Test image file detection."""
        self.assertTrue(self.preview._is_image(Path('test.jpg')))
        self.assertTrue(self.preview._is_image(Path('test.PNG')))  # Case insensitive
        self.assertFalse(self.preview._is_image(Path('test.txt')))
    
    def test_file_size_formatting(self):
        """Test file size formatting."""
        self.assertEqual(self.preview._format_file_size(1024), "1.0 KB")
        self.assertEqual(self.preview._format_file_size(1024 * 1024), "1.0 MB")
        self.assertEqual(self.preview._format_file_size(500), "500.0 B")
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent files."""
        result = self.preview.preview_file("nonexistent_file.jpg")
        self.assertFalse(result)
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_file_read_error(self, mock_open):
        """Test handling of file read errors."""
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            result = self.preview.preview_file(tmp.name)
            self.assertFalse(result)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete file preview system."""
    
    def test_terminal_capabilities_display(self):
        """Test terminal capabilities display."""
        preview = FilePreview()
        # This should not raise an exception
        try:
            preview.print_terminal_capabilities()
        except Exception as e:
            self.fail(f"Terminal capabilities display failed: {e}")
    
    def test_batch_preview_empty_directory(self):
        """Test batch preview with empty directory."""
        preview = FilePreview()
        with tempfile.TemporaryDirectory() as tmp_dir:
            count = preview.batch_preview(tmp_dir)
            self.assertEqual(count, 0)
    
    def test_batch_preview_nonexistent_directory(self):
        """Test batch preview with nonexistent directory."""
        preview = FilePreview()
        count = preview.batch_preview("nonexistent_directory")
        self.assertEqual(count, 0)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)