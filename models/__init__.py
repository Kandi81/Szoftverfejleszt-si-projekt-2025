"""
Data models for Sortify
"""
from .email_model import Email
from .app_state import AppState, app_state

__all__ = [
    'Email',
    'AppState',
    'app_state',
]
