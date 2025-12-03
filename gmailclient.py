"""
DEPRECATED: This module is deprecated and will be removed in v0.5.0
Please use: from services import GmailService
"""
import warnings

warnings.warn(
    "gmailclient.py is deprecated. Use 'from services import GmailService' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from new location
from services.gmail_service import GmailService

# Backward compatibility alias
GmailClient = GmailService

__all__ = ['GmailClient', 'GmailService']
