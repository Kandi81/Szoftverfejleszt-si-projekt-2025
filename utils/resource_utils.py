"""
Resource path utilities for PyInstaller compatibility
"""
import sys
import os


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller
    
    Args:
        relative_path: Relative path to resource file
        
    Returns:
        str: Absolute path to resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
