import csv
import os
import re
from typing import List, Dict


class StorageService:
    def __init__(self, csv_path: str = "data/emails.csv"):
        self.default_csv_path = csv_path
        self.test_csv_path = "data/emails_mod.csv"

        # Ensure data and bodies directories exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/bodies", exist_ok=True)

        self._update_mode()

    def _update_mode(self):
        """Check if test mode is active and set the appropriate CSV path"""
        if os.path.exists(self.test_csv_path):
            self.csv_path = self.test_csv_path
            print(f"[STORAGE] Test mode detected - using {self.test_csv_path}")
        else:
            self.csv_path = self.default_csv_path

    def is_test_mode(self) -> bool:
        """Check if currently in test mode"""
        self._update_mode()
        return self.csv_path == self.test_csv_path

    def save_body_to_file(self, message_id: str, body_plain: str, body_html: str) -> tuple:
        """Save email body to data/bodies/ folder

        Args:
            message_id: Email message ID
            body_plain: Plain text body
            body_html: HTML body

        Returns:
            tuple: (file_path, format) e.g. ('data/bodies/abc123.html', 'html')
        """
        os.makedirs("data/bodies", exist_ok=True)

        # Prefer HTML if available, otherwise use plain text
        if body_html and body_html.strip():
            file_path = f"data/bodies/{message_id}.html"
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(body_html)
                return file_path, 'html'
            except Exception as e:
                print(f"[STORAGE] Error saving HTML body for {message_id}: {e}")

        if body_plain and body_plain.strip():
            file_path = f"data/bodies/{message_id}.txt"
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(body_plain)
                return file_path, 'plain'
            except Exception as e:
                print(f"[STORAGE] Error saving plain body for {message_id}: {e}")

        # No body available
        return '', ''

    def load_body_from_file(self, body_file: str) -> str:
        """Load email body from file

        Args:
            body_file: Path to body file (e.g. 'data/bodies/abc123.html')

        Returns:
            str: Body content (HTML stripped if applicable)
        """
        if not body_file or not os.path.exists(body_file):
            return "Nincs üzenet törzs."

        try:
            with open(body_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # If HTML, strip tags for display
            if body_file.endswith('.html'):
                content = self._strip_html(content)

            return content if content.strip() else "Üres üzenet törzs."

        except Exception as e:
            print(f"[STORAGE] Error loading body from {body_file}: {e}")
            return f"Hiba a törzs betöltése közben: {e}"

    def load_body_from_file_raw(self, body_file: str) -> tuple:
        """Load email body from file WITHOUT stripping HTML

        Args:
            body_file: Path to body file

        Returns:
            tuple: (body_html, body_plain)
        """
        if not body_file or not os.path.exists(body_file):
            return ("", "")

        try:
            with open(body_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if body_file.endswith('.html'):
                return (content, "")  # Return HTML as-is
            else:
                return ("", content)  # Return plain text as-is

        except Exception as e:
            print(f"[STORAGE] Error loading body from {body_file}: {e}")
            return ("", "")

    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags and decode entities

        Args:
            html_content: HTML string

        Returns:
            str: Plain text without HTML tags
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)

        # Decode common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&apos;', "'")

        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r' +', ' ', text)  # Collapse multiple spaces

        return text.strip()

    def load_emails(self) -> List[Dict]:
        """Load emails from CSV file"""
        self._update_mode()

        if not os.path.exists(self.csv_path):
            print(f"[STORAGE] CSV file not found: {self.csv_path}")
            return []

        emails = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse attachment names and MIME types (support both ; and | separators)
                    attachment_names = re.split(r'[;|]', row.get("attachment_names", ""))
                    attachment_names = [a.strip() for a in attachment_names if a.strip()]

                    mime_types = re.split(r'[;|]', row.get("mime_types", ""))
                    mime_types = [m.strip() for m in mime_types if m.strip()]

                    # Convert numeric fields
                    try:
                        attachment_count = int(row.get("attachment_count", 0))
                    except (ValueError, TypeError):
                        attachment_count = 0

                    try:
                        is_last_downloaded = int(row.get("is_last_downloaded", 0))
                    except (ValueError, TypeError):
                        is_last_downloaded = 0

                    try:
                        needs_more_info = int(row.get("needs_more_info", 0))
                    except (ValueError, TypeError):
                        needs_more_info = 0

                    # Build email dict with all fields
                    email = {
                        "message_id": row.get("message_id", ""),
                        "sender": row.get("sender", ""),
                        "sender_name": row.get("sender_name", ""),
                        "sender_domain": row.get("sender_domain", ""),
                        "subject": row.get("subject", ""),
                        "datetime": row.get("datetime", ""),
                        "attachment_count": attachment_count,
                        "attachment_names": attachment_names,
                        "mime_types": mime_types,
                        "tag": row.get("tag", "----"),
                        "is_last_downloaded": is_last_downloaded,
                        "needs_more_info": needs_more_info,
                        "rule_applied": row.get("rule_applied", ""),
                        "body_file": row.get("body_file", ""),
                        "body_format": row.get("body_format", ""),
                        "ai_summary": row.get("ai_summary", "")
                    }

                    # Load body content from file (RAW - don't strip HTML)
                    if email["body_file"]:
                        body_html, body_plain = self.load_body_from_file_raw(email["body_file"])
                        email["body_html"] = body_html
                        email["body_plain"] = body_plain
                    else:
                        email["body_html"] = ""
                        email["body_plain"] = ""

                    emails.append(email)

            print(f"[STORAGE] Loaded {len(emails)} emails from {self.csv_path}")
            return emails

        except Exception as e:
            print(f"[STORAGE] Error loading emails: {e}")
            import traceback
            traceback.print_exc()
            return []

    def sync_emails(self, new_emails: List[Dict]) -> List[Dict]:
        """Sync new emails with existing storage"""
        self._update_mode()

        print(f"[STORAGE] sync_emails() called with {len(new_emails)} new emails")

        # Load existing emails
        existing_emails = self.load_emails()
        existing_ids = {e['message_id'] for e in existing_emails}

        # Reset is_last_downloaded flag for all existing emails
        for email in existing_emails:
            email['is_last_downloaded'] = 0

        # Add new emails and save their bodies
        newly_added = []
        for email in new_emails:
            if email['message_id'] not in existing_ids:
                print(f"[STORAGE] Processing new email: {email['message_id']}")

                # Save body to file
                body_plain = email.pop('body_plain', '')
                body_html = email.pop('body_html', '')

                print(f"[STORAGE]   body_plain length: {len(body_plain)}")
                print(f"[STORAGE]   body_html length: {len(body_html)}")

                body_file, body_format = self.save_body_to_file(
                    email['message_id'],
                    body_plain,
                    body_html
                )

                print(f"[STORAGE]   Saved to: {body_file} (format: {body_format})")

                email['body_file'] = body_file
                email['body_format'] = body_format
                email['is_last_downloaded'] = 1

                # Load body content for in-memory use (RAW - don't strip)
                if body_file:
                    body_html, body_plain = self.load_body_from_file_raw(body_file)
                    email['body_html'] = body_html
                    email['body_plain'] = body_plain
                else:
                    email['body_html'] = ""
                    email['body_plain'] = ""

                newly_added.append(email)
            else:
                print(f"[STORAGE] Email {email['message_id']} already exists, skipping")

        # Combine all emails
        all_emails = existing_emails + newly_added

        # Save to CSV
        self._save_to_csv(all_emails)

        print(f"[STORAGE] Synced {len(newly_added)} new emails. Total: {len(all_emails)}")
        return all_emails

    def save_emails(self, emails: List[Dict]) -> None:
        """Save emails to CSV (used after categorization)

        Args:
            emails: List of email dicts to save
        """
        if self.is_test_mode():
            print("[STORAGE] Test mode - skipping save to prevent overwriting test data")
            return

        self._save_to_csv(emails)
        print(f"[STORAGE] Saved {len(emails)} emails to {self.csv_path}")

    def _save_to_csv(self, emails: List[Dict]) -> None:
        """Internal method to write emails to CSV"""
        fieldnames = [
            "message_id", "sender", "sender_name", "sender_domain",
            "subject", "datetime", "attachment_count", "attachment_names",
            "mime_types", "tag", "is_last_downloaded", "needs_more_info",
            "rule_applied", "body_file", "body_format", "ai_summary"
        ]

        try:
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for email in emails:
                    # Convert lists to pipe-separated strings
                    row = {
                        "message_id": email.get("message_id", ""),
                        "sender": email.get("sender", ""),
                        "sender_name": email.get("sender_name", ""),
                        "sender_domain": email.get("sender_domain", ""),
                        "subject": email.get("subject", ""),
                        "datetime": email.get("datetime", ""),
                        "attachment_count": email.get("attachment_count", 0),
                        "attachment_names": "|".join(email.get("attachment_names", [])) if isinstance(
                            email.get("attachment_names"), list) else email.get("attachment_names", ""),
                        "mime_types": "|".join(email.get("mime_types", [])) if isinstance(email.get("mime_types"),
                                                                                          list) else email.get(
                            "mime_types", ""),
                        "tag": email.get("tag", "----"),
                        "is_last_downloaded": email.get("is_last_downloaded", 0),
                        "needs_more_info": email.get("needs_more_info", 0),
                        "rule_applied": email.get("rule_applied", ""),
                        "body_file": email.get("body_file", ""),
                        "body_format": email.get("body_format", ""),
                        "ai_summary": email.get("ai_summary", "")
                    }
                    writer.writerow(row)

        except Exception as e:
            print(f"[STORAGE] Error saving to CSV: {e}")
            import traceback
            traceback.print_exc()
