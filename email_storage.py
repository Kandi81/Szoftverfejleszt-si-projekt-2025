import csv
import os
from typing import List, Dict


class EmailStorage:
    def __init__(self, csv_path: str = "data/emails.csv"):
        self.default_csv_path = csv_path
        self.test_csv_path = "data/emails_mod.csv"

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        self._update_mode()

    def _update_mode(self):
        """Check and update test mode status"""
        if os.path.exists(self.test_csv_path):
            self.test_mode = True
            self.csv_path = self.test_csv_path
            print(f"[STORAGE] Test mode detected - using {self.csv_path}")
        else:
            self.test_mode = False
            self.csv_path = self.default_csv_path
            print(f"[STORAGE] Production mode - using {self.csv_path}")

    def is_test_mode(self) -> bool:
        """Check if running in test mode (emails_mod.csv exists)"""
        # Re-check in case file was created/deleted
        self._update_mode()
        return self.test_mode

    def load_emails(self) -> List[Dict]:
        """Load emails from CSV file"""
        # Update mode before loading
        self._update_mode()

        if not os.path.exists(self.csv_path):
            print(f"[STORAGE] CSV file not found: {self.csv_path}")
            return []

        emails = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Safely convert numeric fields with defaults
                    try:
                        row['attachment_count'] = int(row.get('attachment_count', 0) or 0)
                    except (ValueError, TypeError):
                        row['attachment_count'] = 0

                    try:
                        row['is_last_downloaded'] = int(row.get('is_last_downloaded', 0) or 0)
                    except (ValueError, TypeError):
                        row['is_last_downloaded'] = 0

                    try:
                        row['needs_more_info'] = int(row.get('needs_more_info', 0) or 0)
                    except (ValueError, TypeError):
                        row['needs_more_info'] = 0

                    # Parse lists from strings (support both ; and | separators)
                    if row.get('attachment_names'):
                        # Try semicolon first (your format), then pipe (our format)
                        if ';' in row['attachment_names']:
                            row['attachment_names'] = [name.strip() for name in row['attachment_names'].split(';') if
                                                       name.strip()]
                        elif '|' in row['attachment_names']:
                            row['attachment_names'] = [name.strip() for name in row['attachment_names'].split('|') if
                                                       name.strip()]
                        else:
                            row['attachment_names'] = [row['attachment_names']] if row['attachment_names'] else []
                    else:
                        row['attachment_names'] = []

                    if row.get('mime_types'):
                        # Try semicolon first (your format), then pipe (our format)
                        if ';' in row['mime_types']:
                            row['mime_types'] = [mt.strip() for mt in row['mime_types'].split(';') if mt.strip()]
                        elif '|' in row['mime_types']:
                            row['mime_types'] = [mt.strip() for mt in row['mime_types'].split('|') if mt.strip()]
                        else:
                            row['mime_types'] = [row['mime_types']] if row['mime_types'] else []
                    else:
                        row['mime_types'] = []

                    # Ensure required fields exist
                    row.setdefault('message_id', '')
                    row.setdefault('sender', '')
                    row.setdefault('sender_name', '')
                    row.setdefault('sender_domain', '')
                    row.setdefault('subject', '')
                    row.setdefault('datetime', '')
                    row.setdefault('tag', '----')
                    row.setdefault('rule_applied', '')

                    emails.append(row)

            print(f"[STORAGE] Loaded {len(emails)} emails from {self.csv_path}")
        except Exception as e:
            print(f"[STORAGE] Error loading emails: {e}")
            import traceback
            traceback.print_exc()
            return []

        return emails

    def sync_emails(self, gmail_emails: List[Dict]) -> List[Dict]:
        """
        Sync Gmail emails with local storage.
        - Marks all existing emails as not last downloaded
        - Adds new emails from Gmail
        - Updates existing emails if they've changed
        - Returns the complete updated list
        """
        existing_emails = self.load_emails()
        existing_map = {e['message_id']: e for e in existing_emails}

        # Mark all as not last downloaded
        for email in existing_emails:
            email['is_last_downloaded'] = 0

        # Process Gmail emails
        for gmail_email in gmail_emails:
            gmail_email['is_last_downloaded'] = 1
            message_id = gmail_email['message_id']

            if message_id in existing_map:
                # Update existing email
                existing_map[message_id].update(gmail_email)
            else:
                # Add new email
                existing_emails.append(gmail_email)
                existing_map[message_id] = gmail_email

        # Save to CSV
        self._save_to_path(self.csv_path, existing_emails)
        return existing_emails

    def save_emails(self, emails: List[Dict]) -> None:
        """
        Save emails to storage (respects test mode - won't save to emails_mod.csv).
        """
        # Re-check test mode
        self._update_mode()

        if self.is_test_mode():
            print("[STORAGE] Test mode active - changes not saved to emails_mod.csv")
            return

        self._save_to_path(self.csv_path, emails)
        print(f"[STORAGE] Saved {len(emails)} emails to {self.csv_path}")

    def _save_to_path(self, path: str, emails: List[Dict]) -> None:
        """Internal method to save emails to a specific path"""
        fieldnames = [
            'message_id', 'sender', 'sender_name', 'sender_domain', 'subject', 'datetime',
            'attachment_count', 'attachment_names', 'mime_types', 'tag',
            'is_last_downloaded', 'needs_more_info', 'rule_applied'
        ]

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)

            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for email in emails:
                    # Convert lists to pipe-separated strings
                    email_copy = email.copy()
                    if isinstance(email_copy.get('attachment_names'), list):
                        email_copy['attachment_names'] = '|'.join(email_copy['attachment_names'])
                    if isinstance(email_copy.get('mime_types'), list):
                        email_copy['mime_types'] = '|'.join(email_copy['mime_types'])

                    # Ensure all fields exist with proper defaults
                    for field in fieldnames:
                        if field not in email_copy:
                            if field in ['attachment_count', 'is_last_downloaded', 'needs_more_info']:
                                email_copy[field] = 0
                            else:
                                email_copy[field] = ''

                    writer.writerow(email_copy)

            print(f"[STORAGE] Successfully wrote {len(emails)} emails to {path}")
        except Exception as e:
            print(f"[STORAGE] Error saving to {path}: {e}")
            import traceback
            traceback.print_exc()
