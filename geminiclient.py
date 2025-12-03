"""
DEPRECATED: This module is deprecated and will be removed in v0.5.0
Please use: from services import GeminiService
"""
import warnings

warnings.warn(
    "geminiclient.py is deprecated. Use 'from services import GeminiService' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from new location
from services.gemini_service import GeminiService

# Backward compatibility alias
GeminiClient = GeminiService

__all__ = ['GeminiClient', 'GeminiService']
