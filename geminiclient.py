import time
from typing import Optional
from google import genai
from google.genai import errors  # APIError and others live here
from google.genai.errors import ServerError  # transient server-side errors

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        # Read api_key param or GEMINI_API_KEY/GOOGLE_API_KEY env vars if None.  [2][5]
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.fallback_model = "gemini-2.5-flash-lite"

    def summarize_hu(self, text: str, max_words: int = 10, max_retries: int = 5) -> str:
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
                # Retry on transient overloads (503 UNAVAILABLE).  [9]
                msg = str(e)
                if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                    time.sleep(delay)
                    delay = min(delay * 2, 30.0)
                    if attempt >= 2 and model != self.fallback_model:
                        model = self.fallback_model
                    continue
                raise
            except errors.APIError:
                # Non-transient API errors (4xx/other 5xx): surface to caller.  [1][5]
                raise

        # Final attempt on fallback if not tried yet.
        if model != self.fallback_model:
            resp = self.client.models.generate_content(model=self.fallback_model, contents=prompt)
            return getattr(resp, "text", "") or ""
        return ""
