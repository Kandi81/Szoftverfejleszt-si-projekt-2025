"""
Email storage module for managing offline email data in CSV format.
Handles saving, loading, and syncing email data.
"""

import csv
import os
from typing import List, Dict, Optional


class EmailStorage:
    def __init__(self, data_dir: str = "data"):
        """
        Initialize email storage.

        Args:
            data_dir: Directory where emails.csv will be stored (default: 'data')
        """
        self.data_dir = data_dir
        self.csv_path = os.path.join(data_dir, "emails.csv")
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def save_emails(self, emails: List[Dict]) -> None:
        """
        Save emails to CSV file.

        Args:
            emails: List of email dictionaries with keys:
                   message_id, sender, subject, datetime,
                   attachment_count, attachment_names, tag, is_last_downloaded
        """
        fieldnames = [
            "message_id", "sender", "subject", "datetime",
            "attachment_count", "attachment_names", "tag", "is_last_downloaded"
        ]

        with open(self.csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

            for email_item in emails:
                # Convert attachment_names list to semicolon-separated string
                if isinstance(email_item.get("attachment_names"), list):
                    email_item["attachment_names"] = ";".join(email_item["attachment_names"])

                writer.writerow(email_item)

    def load_emails(self) -> List[Dict]:
        """
        Load emails from CSV file.

        Returns:
            List of email dictionaries. Returns empty list if file doesn't exist.
        """
        if not os.path.exists(self.csv_path):
            return []

        email_list = []
        with open(self.csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert attachment_names back to list
                if row.get("attachment_names"):
                    row["attachment_names"] = row["attachment_names"].split(";")
                else:
                    row["attachment_names"] = []

                # Convert attachment_count to int
                try:
                    row["attachment_count"] = int(row.get("attachment_count", 0))
                except (ValueError, TypeError):
                    row["attachment_count"] = 0

                # Convert is_last_downloaded to int (0 or 1)
                try:
                    row["is_last_downloaded"] = int(row.get("is_last_downloaded", 0))
                except (ValueError, TypeError):
                    row["is_last_downloaded"] = 0

                email_list.append(row)

        return email_list

    def sync_emails(self, gmail_emails: List[Dict]) -> List[Dict]:
        """
        Sync downloaded Gmail emails with existing offline storage.

        Args:
            gmail_emails: List of email dicts from Gmail API

        Returns:
            Merged and synced list of emails
        """
        # Load existing emails
        existing_emails = self.load_emails()

        # Create a map of existing emails by message_id
        existing_map = {item["message_id"]: item for item in existing_emails}

        # Create a set of Gmail message IDs
        gmail_ids = {item["message_id"] for item in gmail_emails}

        # Clear all is_last_downloaded flags
        for existing_item in existing_emails:
            existing_item["is_last_downloaded"] = 0

        # Process Gmail emails
        synced_emails = []
        for gmail_item in gmail_emails:
            msg_id = gmail_item["message_id"]

            if msg_id in existing_map:
                # Email exists - preserve tag, update other fields
                existing_item = existing_map[msg_id]
                gmail_item["tag"] = existing_item.get("tag", "----")
            else:
                # New email - set default tag
                gmail_item["tag"] = "----"

            # Mark as part of last download
            gmail_item["is_last_downloaded"] = 1

            # Convert attachment_names to list if it's a string
            if isinstance(gmail_item.get("attachment_names"), str):
                gmail_item["attachment_names"] = gmail_item["attachment_names"].split(";")

            synced_emails.append(gmail_item)

        # Add existing emails that are still in Gmail (not in current batch but weren't deleted)
        for existing_item in existing_emails:
            msg_id = existing_item["message_id"]
            if msg_id not in gmail_ids and msg_id not in [e["message_id"] for e in synced_emails]:
                # Keep old emails that weren't in this download batch
                synced_emails.append(existing_item)

        # Save synced emails
        self.save_emails(synced_emails)

        return synced_emails

    def update_email_tag(self, message_id: str, tag: str) -> bool:
        """
        Update the tag for a specific email.

        Args:
            message_id: The message ID to update
            tag: New tag value

        Returns:
            True if successful, False if message not found
        """
        email_list = self.load_emails()
        updated = False

        for email_item in email_list:
            if email_item["message_id"] == message_id:
                email_item["tag"] = tag
                updated = True
                break

        if updated:
            self.save_emails(email_list)

        return updated

    def get_email_by_id(self, message_id: str) -> Optional[Dict]:
        """
        Get a specific email by message ID.

        Args:
            message_id: The message ID to find

        Returns:
            Email dict if found, None otherwise
        """
        email_list = self.load_emails()
        for email_item in email_list:
            if email_item["message_id"] == message_id:
                return email_item
        return None


# Example usage
if __name__ == "__main__":
    storage = EmailStorage()

    # Example: Save some test emails
    test_emails = [
        {
            "message_id": "12345",
            "sender": "test@example.com",
            "subject": "Test Email 1",
            "datetime": "2025.11.16 18:00",
            "attachment_count": 2,
            "attachment_names": ["document.pdf", "image.png"],
            "tag": "----",
            "is_last_downloaded": 1
        },
        {
            "message_id": "67890",
            "sender": "another@example.com",
            "subject": "Test Email 2, with comma",
            "datetime": "2025.11.16 17:30",
            "attachment_count": 0,
            "attachment_names": [],
            "tag": "moodle",
            "is_last_downloaded": 1
        }
    ]

    storage.save_emails(test_emails)
    print("Emails saved!")

    # Load emails
    loaded = storage.load_emails()
    print(f"\nLoaded {len(loaded)} emails:")
    for email_data in loaded:
        print(f"  - {email_data['subject']} (Tag: {email_data['tag']}, Attachments: {email_data['attachment_count']})")
