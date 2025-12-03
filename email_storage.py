"""
DEPRECATED: This module is deprecated and will be removed in v0.5.0
Please use: from services import StorageService
"""
import warnings

warnings.warn(
    "email_storage.py is deprecated. Use 'from services import StorageService' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from new location
from services.storage_service import StorageService

# Backward compatibility alias
EmailStorage = StorageService

__all__ = ['EmailStorage', 'StorageService']
