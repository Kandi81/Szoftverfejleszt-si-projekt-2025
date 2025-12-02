"""
Fix for tkhtmlview compatibility with newer Pillow versions
"""
from PIL import Image

# Add ANTIALIAS as alias for LANCZOS if it doesn't exist
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
