"""
DEPRECATED: This module is deprecated and will be removed in v0.5.0
Please use: from business import apply_rules
"""
import warnings

warnings.warn(
    "rules.py is deprecated. Use 'from business import apply_rules' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from new location
from business.rules_engine import apply_rules

__all__ = ['apply_rules']
