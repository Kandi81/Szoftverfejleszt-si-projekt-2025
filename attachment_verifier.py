"""
DEPRECATED: This module is deprecated and will be removed in v0.5.0
Please use: from services import verify_attachments
"""
import warnings

warnings.warn(
    "attachment_verifier.py is deprecated. Use 'from services import verify_attachments' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from new location
from services.verification_service import verify_attachments

# Backward compatibility alias
verify_emails_batch = verify_attachments

__all__ = ['verify_emails_batch', 'verify_attachments']
