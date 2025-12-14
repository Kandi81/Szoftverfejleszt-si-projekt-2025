"""
Perplexity AI client for email summarization
OpenAI-compatible Chat Completions API
"""
import time
import os
from pathlib import Path
import sys
from typing import Optional
from perplexity import Perplexity

class PerplexityService:
    def __init__(self, api_key: Optional[str] = None, model: str = "sonar"):
        """Initialize Perplexity client

        Args:
            api_key: API key (or None to load from file/env var)
            model: Model to use (sonar, sonar-pro, sonar-reasoning)
        """
        # If no api_key provided, try to load from file
        if api_key is None:
            api_key = self._load_api_key_from_file()

        # Initialize client with API key
        self.client = Perplexity(api_key=api_key)
        self.model = model
        self.fallback_model = "sonar"  # Fallback to basic sonar if errors

    from pathlib import Path
    import sys

    def _load_api_key_from_file(self, path: str = "resource/perp_api_key.txt") -> Optional[str]:
        """Load API key from file if exists

        Args:
            path: Path to API key file (relative to exe/script dir)

        Returns:
            API key string or None
        """
        # Get base directory - works in both dev and PyInstaller exe
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).resolve().parent.parent  # Go up from services/ to project root

        full_path = base_dir / path

        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    key = f.read().strip()
                    if key and key.startswith('pplx-'):
                        print(f"[PERPLEXITY] API key loaded from {full_path}")
                        return key
                    else:
                        print(f"[PERPLEXITY] Invalid API key format in {full_path}")
            except Exception as e:
                print(f"[PERPLEXITY] Error reading API key from {full_path}: {e}")
        else:
            print(f"[PERPLEXITY] API key file not found: {full_path}")

        # Fallback to environment variable
        env_key = os.getenv('PERPLEXITY_API_KEY')
        if env_key:
            print("[PERPLEXITY] API key loaded from PERPLEXITY_API_KEY env var")
            return env_key

        return None

    def summarize_email(self, subject: str, body_text: str, sender: str = "", max_retries: int = 3) -> str:
        """Generate email summary in Hungarian (2-3 sentences)

        Args:
            subject: Email subject
            body_text: Email body (plain text, will be truncated to 2000 chars)
            sender: Email sender name (optional)
            max_retries: Maximum retry attempts

        Returns:
            str: 2-3 sentence summary in Hungarian
        """
        if not body_text or not body_text.strip():
            return "[Üres email törzs]"

        # Truncate body to avoid token limits
        body_excerpt = body_text[:2000]

        # Build structured prompt with system message
        system_prompt = """Te egy professzionális email asszisztens vagy. 
A feladatod rövid, tömör összefoglalókat készíteni emailekről magyar nyelven.
Az összefoglaló 2-3 mondatból álljon, és tartalmazza a legfontosabb információkat vagy kéréseket."""

        user_prompt = f"""Készíts egy rövid, 2-3 mondatos összefoglalót a következő emailről.

Feladó: {sender if sender else 'N/A'}
Tárgy: {subject}

Email szövege:
{body_excerpt}

Összefoglaló (2-3 mondat, magyarul):"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        delay = 2.0
        model = self.model

        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    max_tokens=200,  # Limit response length
                    temperature=0.3,  # Low temperature for consistent summaries
                )

                summary = completion.choices[0].message.content.strip()

                # Clean up markdown formatting
                summary = summary.replace('**', '').replace('*', '').strip()

                return summary if summary else "[Hiba: üres válasz a Perplexity-től]"

            except Exception as e:
                error_msg = str(e).lower()

                # Retry on rate limit or server errors
                if "rate limit" in error_msg or "429" in error_msg or "503" in error_msg:
                    print(f"[PERPLEXITY] Retry {attempt + 1}/{max_retries} after {delay}s (rate limit/server error)")
                    time.sleep(delay)
                    delay = min(delay * 2, 30.0)

                    # Try fallback model after 2nd retry
                    if attempt >= 1 and model != self.fallback_model:
                        print(f"[PERPLEXITY] Switching to fallback model: {self.fallback_model}")
                        model = self.fallback_model
                    continue
                else:
                    # Non-retryable error
                    print(f"[PERPLEXITY] Email summary error: {e}")
                    return f"[Hiba az összefoglaló generálása során: {e}]"

        return "[Hiba: nem sikerült összefoglalót generálni több próbálkozás után]"

    def summarize_emails_batch(self, emails: list, max_retries: int = 3) -> dict:
        """Generate summaries for multiple emails

        Args:
            emails: List of email dicts with 'message_id', 'subject', 'body_plain', 'sender_name'
            max_retries: Maximum retry attempts per email

        Returns:
            dict: {message_id: summary}
        """
        summaries = {}

        for idx, email in enumerate(emails, 1):
            message_id = email.get('message_id', '')
            subject = email.get('subject', '(no subject)')

            # Use body_plain, or fallback to stripped body_html
            body_plain = email.get('body_plain', '')
            if not body_plain:
                # Fallback: load and strip HTML if only HTML available
                body_html = email.get('body_html', '')
                if body_html:
                    # Simple HTML stripping
                    import re
                    body_plain = re.sub(r'<[^>]+>', '', body_html)

            sender = email.get('sender_name', '')

            # Skip if already has summary
            if email.get('ai_summary'):
                print(f"[PERPLEXITY] {idx}/{len(emails)}: Skipping {message_id} (already has summary)")
                continue

            print(f"[PERPLEXITY] {idx}/{len(emails)}: Generating summary for '{subject}'...")

            summary = self.summarize_email(subject, body_plain, sender, max_retries)
            summaries[message_id] = summary

            # Delay between requests to avoid rate limiting
            if idx < len(emails):
                time.sleep(1.0)  # 1 second delay between emails

        return summaries
