"""
Gemini AI client for email summarization
"""
import time
import os
from typing import Optional
from google import genai
from google.genai import errors  # APIError and others live here
from google.genai.errors import ServerError  # transient server-side errors


class StorageService:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        """Initialize Gemini client

        Args:
            api_key: API key (or None to use env var GEMINI_API_KEY/GOOGLE_API_KEY)
            model: Primary model to use
        """
        # If no api_key provided, try to load from file
        if api_key is None:
            api_key = self._load_api_key_from_file()

        # Read api_key param or GEMINI_API_KEY/GOOGLE_API_KEY env vars if None
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.fallback_model = "gemini-2.0-flash-exp"

    def _load_api_key_from_file(self, path: str = "resource/gemini_api_key.txt") -> Optional[str]:
        """Load API key from file if exists

        Args:
            path: Path to API key file

        Returns:
            API key string or None
        """
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    key = f.read().strip()
                    if key:
                        print(f"[GEMINI] API key loaded from {path}")
                        return key
            except Exception as e:
                print(f"[GEMINI] Error reading API key from {path}: {e}")
        return None

    def summarize_hu(self, text: str, max_words: int = 10, max_retries: int = 5) -> str:
        """Generic Hungarian summarization (your original implementation)

        Args:
            text: Text to summarize
            max_words: Maximum words in summary
            max_retries: Maximum retry attempts

        Returns:
            Summary string
        """
        if not text or not text.strip():
            return ""

        prompt = (
            f"Kérlek, foglald össze tömören, magyarul (max ~{max_words} szóban). "
            f"Adj 3–6 lényegi pontot vagy egy rövid bekezdést.\n\nSzöveg:\n{text}"
        )

        delay = 2.0
        model = self.model
        for attempt in range(max_retries):
            try:
                resp = self.client.models.generate_content(model=model, contents=prompt)
                return getattr(resp, "text", "") or ""
            except ServerError as e:
                # Retry on transient overloads (503 UNAVAILABLE)
                msg = str(e)
                if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                    print(f"[GEMINI] Retry {attempt + 1}/{max_retries} after {delay}s (server overload)")
                    time.sleep(delay)
                    delay = min(delay * 2, 30.0)
                    if attempt >= 2 and model != self.fallback_model:
                        print(f"[GEMINI] Switching to fallback model: {self.fallback_model}")
                        model = self.fallback_model
                    continue
                raise
            except errors.APIError as e:
                # Non-transient API errors (4xx/other 5xx): surface to caller
                print(f"[GEMINI] API Error: {e}")
                raise

        # Final attempt on fallback if not tried yet
        if model != self.fallback_model:
            print(f"[GEMINI] Final retry with fallback model: {self.fallback_model}")
            resp = self.client.models.generate_content(model=self.fallback_model, contents=prompt)
            return getattr(resp, "text", "") or ""
        return ""

    def summarize_email(self, subject: str, body_text: str, sender: str = "", max_retries: int = 5) -> str:
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

        # Build structured prompt
        prompt = f"""Készíts egy rövid, 2-3 mondatos összefoglalót a következő emailről magyar nyelven.
Az összefoglaló legyen tömör, informatív, és tartalmazza a legfontosabb információkat vagy kéréseket.

Feladó: {sender if sender else 'N/A'}
Tárgy: {subject}

Email szövege:
{body_excerpt}

Összefoglaló (2-3 mondat, magyarul):"""

        delay = 2.0
        model = self.model

        for attempt in range(max_retries):
            try:
                resp = self.client.models.generate_content(model=model, contents=prompt)
                summary = getattr(resp, "text", "") or ""

                # Clean up markdown formatting
                summary = summary.replace('**', '').replace('*', '').strip()

                return summary if summary else "[Hiba: üres válasz a Gemini-től]"

            except ServerError as e:
                msg = str(e)
                if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                    print(f"[GEMINI] Email summary retry {attempt + 1}/{max_retries} after {delay}s")
                    time.sleep(delay)
                    delay = min(delay * 2, 30.0)
                    if attempt >= 2 and model != self.fallback_model:
                        model = self.fallback_model
                    continue
                raise

            except errors.APIError as e:
                print(f"[GEMINI] Email summary API error: {e}")
                return f"[Hiba az összefoglaló generálása során: {e}]"

        # Final fallback attempt
        if model != self.fallback_model:
            try:
                resp = self.client.models.generate_content(model=self.fallback_model, contents=prompt)
                summary = getattr(resp, "text", "") or ""
                return summary.replace('**', '').replace('*', '').strip()
            except Exception as e:
                print(f"[GEMINI] Final fallback failed: {e}")

        return "[Hiba: nem sikerült összefoglalót generálni]"

    def summarize_emails_batch(self, emails: list, max_retries: int = 5) -> dict:
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
                    # Simple HTML stripping (basic, Gemini can handle some HTML)
                    import re
                    body_plain = re.sub(r'<[^>]+>', '', body_html)

            sender = email.get('sender_name', '')

            # Skip if already has summary
            if email.get('ai_summary'):
                print(f"[GEMINI] {idx}/{len(emails)}: Skipping {message_id} (already has summary)")
                continue

            print(f"[GEMINI] {idx}/{len(emails)}: Generating summary for '{subject}'...")

            summary = self.summarize_email(subject, body_plain, sender, max_retries)
            summaries[message_id] = summary

            # Small delay between requests to avoid rate limiting
            if idx < len(emails):
                time.sleep(0.5)

        return summaries
