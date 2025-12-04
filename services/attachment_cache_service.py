"""
Attachment verification cache service
Stores attachment verification results per email to avoid redundant checks
"""
import json
import os
from typing import Dict, Optional
from datetime import datetime


class AttachmentCacheService:
    """Service for caching attachment verification results"""

    def __init__(self, cache_file: str = "data/attachment_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load attachment cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save attachment cache: {e}")

    def get_verification(self, email_id: str, filename: str) -> Optional[dict]:
        """Get cached verification result

        Args:
            email_id: Unique email identifier
            filename: Attachment filename

        Returns:
            dict with 'is_safe', 'checked_at', 'reason' or None if not cached
        """
        key = f"{email_id}:{filename}"
        return self.cache.get(key)

    def store_verification(self, email_id: str, filename: str, is_safe: bool, reason: str = None):
        """Store verification result

        Args:
            email_id: Unique email identifier
            filename: Attachment filename
            is_safe: True if attachment is safe, False if suspicious
            reason: Reason why attachment is suspicious (if applicable)
        """
        key = f"{email_id}:{filename}"
        self.cache[key] = {
            'is_safe': is_safe,
            'checked_at': datetime.now().isoformat(),
            'reason': reason
        }
        self._save_cache()

    def is_verified(self, email_id: str, filename: str) -> bool:
        """Check if attachment already verified

        Args:
            email_id: Unique email identifier
            filename: Attachment filename

        Returns:
            True if verification result exists in cache
        """
        return self.get_verification(email_id, filename) is not None

    def clear_cache(self):
        """Clear all cache entries"""
        self.cache = {}
        self._save_cache()

    def get_stats(self) -> dict:
        """Get cache statistics

        Returns:
            dict with 'total', 'safe', 'suspicious'
        """
        total = len(self.cache)
        safe = sum(1 for v in self.cache.values() if v.get('is_safe'))
        suspicious = total - safe

        return {
            'total': total,
            'safe': safe,
            'suspicious': suspicious
        }
