import os
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class GmailClient:
    def __init__(self,
                 credentials_path: str = "resource\credentials.json",
                 token_path: str = "token.json",
                 scopes: Optional[List[str]] = None):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = scopes or SCOPES
        self.creds: Optional[Credentials] = None
        self.service = None

    def _extract_text_from_payload(self, payload: Dict) -> str:
        """
        Recursively extract the text body from a Gmail message payload.
        Prefers text/plain; falls back to text/html (converted to text).
        """
        import base64
        mime_type = payload.get("mimeType", "")
        body = payload.get("body", {})
        data = body.get("data")
        parts = payload.get("parts", [])

        def b64url_decode(b64: str) -> str:
            return base64.urlsafe_b64decode(b64.encode("utf-8")).decode("utf-8", errors="replace")

        # Leaf part: text/plain
        if mime_type == "text/plain" and data:
            return b64url_decode(data).strip()

        # Multipart: search children (text/plain first)
        if parts:
            for p in parts:
                if p.get("mimeType") == "text/plain":
                    txt = self._extract_text_from_payload(p)
                    if txt:
                        return txt
            # Fallback to text/html
            for p in parts:
                if p.get("mimeType") == "text/html":
                    html_txt = self._extract_text_from_payload(p)
                    if html_txt:
                        return self._minimal_html_to_text(html_txt)

        # Leaf part: text/html
        if mime_type == "text/html" and data:
            html = b64url_decode(data)
            return self._minimal_html_to_text(html)

        # If content is not inline (e.g., attachmentId present), skip here.
        return ""

    def _minimal_html_to_text(self, html: str) -> str:
        """
        Very light HTML-to-text conversion for previews.
        Consider a library (html2text, beautifulsoup4) for richer handling.
        """
        import re
        txt = html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        txt = re.sub(r"<style.*?>.*?</style>", "", txt, flags=re.S | re.I)
        txt = re.sub(r"<script.*?>.*?</script>", "", txt, flags=re.S | re.I)
        txt = re.sub(r"<[^>]+>", "", txt)
        return re.sub(r"\n{3,}", "\n\n", txt).strip()

    def authenticate(self):
        # Load existing token
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        # Refresh or run OAuth flow
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.scopes)
                self.creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(self.creds.to_json())
        # Build one reusable service
        self.service = build("gmail", "v1", credentials=self.creds)

    def list_inbox(self, query: str = "", max_results: int = 1000) -> List[Dict]:
        """
        List message ids in INBOX, optionally filtered by Gmail search query (e.g., 'is:unread after:2025/09/01').
        """
        if not self.service:
            raise RuntimeError("Call authenticate() first.")
        msgs = []
        req = self.service.users().messages().list(userId="me",
                                                   labelIds=["INBOX"],
                                                   q=query,
                                                   maxResults=min(500, max_results))
        while req is not None and len(msgs) < max_results:
            resp = req.execute()
            msgs.extend(resp.get("messages", []))
            if len(msgs) >= max_results:
                break
            req = self.service.users().messages().list_next(previous_request=req, previous_response=resp)
        return msgs

    def get_subject(self, message_id: str) -> str:
        """
        Fetch a message's Subject efficiently using metadata format.
        """
        if not self.service:
            raise RuntimeError("Call authenticate() first.")
        msg = self.service.users().messages().get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["Subject"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        return headers.get("Subject", "(no subject)")

    def get_message(self, message_id: str) -> Dict:
        """
        Fetch full message payload if needed later.
        """
        if not self.service:
            raise RuntimeError("Call authenticate() first.")
        return self.service.users().messages().get(userId="me", id=message_id, format="full").execute()

    def get_subject_and_body(self, message_id: str) -> dict:
        if not self.service:
            raise RuntimeError("Call authenticate() first.")
        full = self.get_message(message_id)
        headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        text = self._extract_text_from_payload(full.get("payload", {})) or full.get("snippet", "")
        return {"subject": subject, "text": text}

if __name__ == "__main__":
    try:
        client = GmailClient(credentials_path="resource\credentials.json", token_path="resource/token.json")
        client.authenticate()
        messages = client.list_inbox(query="", max_results=100)
        for m in messages:
            print(m["id"], client.get_subject(m["id"]))
    except HttpError as e:
        print(f"Gmail API error: {e}")
