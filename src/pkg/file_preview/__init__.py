"""
File Preview Package with Sixel Graphics Protocol Support

This package provides terminal-based image preview functionality using
the sixel graphics protocol for high-definition image display in compatible terminals.
"""

from .sixel import SixelRenderer
from .preview import FilePreview
from .terminal import TerminalDetector

__version__ = "1.0.0"
__all__ = ["SixelRenderer", "FilePreview", "TerminalDetector"]