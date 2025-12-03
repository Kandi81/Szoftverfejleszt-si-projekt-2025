"""
DEPRECATED: This module is deprecated and will be removed in v0.5.0
Please use: from services import PerplexityService
"""
import warnings

warnings.warn(
    "perplexity_client.py is deprecated. Use 'from services import PerplexityService' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from new location
from services.perplexity_service import PerplexityService

# Backward compatibility alias
PerplexityClient = PerplexityService

__all__ = ['PerplexityClient', 'PerplexityService']
