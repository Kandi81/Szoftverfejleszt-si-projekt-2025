"""
Services module exports
"""

from .storage_service import StorageService
from .gmail_service import GmailService
from .ai_factory import AIServiceFactory, AIProvider  # ← CORRECTED: ai_factory not aifactory
from .verification_service import verify_attachments  # ← CORRECTED: verification_service not attachment_verification

# ========== ADDED: gmailcimke exports ==========
from .gmailcimke import (
    list_labels,
    get_label_map,
    ensure_labels,
    create_default_labels,
    apply_label_to_message,
    apply_label_to_messages,
    remove_label_from_message
)
# =================================================

__all__ = [
    'StorageService',
    'GmailService',
    'AIServiceFactory',
    'AIProvider',
    'verify_attachments',
    'list_labels',
    'get_label_map',
    'ensure_labels',
    'create_default_labels',
    'apply_label_to_message',
    'apply_label_to_messages',
    'remove_label_from_message'
]
