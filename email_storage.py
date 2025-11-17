"""
Email storage for offline email data (CSV, non-backward compatible).
Supports normal mode (emails.csv) and test mode (emails_mod.csv).
"""

import csv
import os
from typing import List, Dict, Optional


CSV_FIELDS = [
    "message_id",
    "sender",          # raw "From" header
    "sender_name",     # parsed display name only
    "sender_domain",   # domain part of email
    "subject",
    "datetime",        # YYYY.MM.DD HH:MM
    "attachment_count",
    "attachment_names",  # semicolon-separated
    "mime_types",        # semicolon-separated
    "tag",
    "is_last_downloaded",
    "needs_more_info",   # student triage flag (0/1)
    "rule_applied"       # e.g., vezetosegi/tanszek/...
]


class EmailStorage:
    """
    Storage facade. If emails_mod.csv exists, storage operates in test mode:
    - Loads from emails_mod.csv
    - Does NOT write back to emails_mod.csv (read-only test dataset)
    - Writes normal sync results to emails.csv as usual
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.csv_path = os.path.join(data_dir, "emails.csv")
        self.test_csv_path = os.path.join(data_dir, "emails_mod.csv")

    # -------- mode helpers --------

    def is_test_mode(self) -> bool:
        """Return True if test dataset emails_mod.csv is present."""
        return os.path.exists(self.test_csv_path)

    # -------- load/save helpers --------

    def _load_from_path(self, path: str) -> List[Dict]:
        if not os.path.exists(path):
            return []
        out: List[Dict] = []
        with open(path, "r", newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                item = {k: row.get(k, "") for k in CSV_FIELDS}
                item["attachment_names"] = item["attachment_names"].split(";") if item["attachment_names"] else []
                item["mime_types"] = item["mime_types"].split(";") if item["mime_types"] else []
                try:
                    item["attachment_count"] = int(item["attachment_count"] or 0)
                except ValueError:
                    item["attachment_count"] = 0
                for k in ("is_last_downloaded", "needs_more_info"):
                    try:
                        item[k] = int(item[k] or 0)
                    except ValueError:
                        item[k] = 0
                out.append(item)
        return out

    def _save_to_path(self, path: str, emails: List[Dict]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS, quoting=csv.QUOTE_MINIMAL)
            w.writeheader()
            for e in emails:
                row = {k: "" for k in CSV_FIELDS}
                row.update(e)
                if isinstance(row.get("attachment_names"), list):
                    row["attachment_names"] = ";".join(row["attachment_names"])
                if isinstance(row.get("mime_types"), list):
                    row["mime_types"] = ";".join(row["mime_types"])
                row["attachment_count"] = int(row.get("attachment_count", 0))
                row["is_last_downloaded"] = int(row.get("is_last_downloaded", 0))
                row["needs_more_info"] = int(row.get("needs_more_info", 0))
                w.writerow(row)

    # -------- public API --------

    def load_emails(self) -> List[Dict]:
        """
        Load emails.
        - In test mode: load emails_mod.csv (read-only test dataset).
        - Otherwise: load emails.csv.
        """
        if self.is_test_mode():
            return self._load_from_path(self.test_csv_path)
        return self._load_from_path(self.csv_path)

    def save_emails(self, emails: List[Dict]) -> None:
        """
        Save emails.
        - NEVER overwrite emails_mod.csv (test dataset is read-only).
        - Always write to emails.csv.
        """
        self._save_to_path(self.csv_path, emails)

    def sync_emails(self, gmail_emails: List[Dict]) -> List[Dict]:
        """
        Merge Gmail emails into local storage.
        - Preserves existing tags from emails.csv (NOT from emails_mod.csv).
        - Writes merged set to emails.csv.
        - In test mode, this does NOT affect what the UI displays by default.
        """
        # Always merge against the real storage CSV, not test dataset.
        existing = self._load_from_path(self.csv_path)
        existing_map = {e["message_id"]: e for e in existing}

        merged: List[Dict] = []
        for g in gmail_emails:
            msg_id = g["message_id"]
            g["tag"] = existing_map.get(msg_id, {}).get("tag", "----")
            g["is_last_downloaded"] = 1
            g.setdefault("needs_more_info", 0)
            g.setdefault("rule_applied", "")
            for k in CSV_FIELDS:
                g.setdefault(
                    k,
                    "" if k not in ("attachment_count", "is_last_downloaded", "needs_more_info") else 0,
                )
            merged.append(g)

        self.save_emails(merged)
        return merged

    def update_email_tag(self, message_id: str, tag: str) -> bool:
        emails = self.load_emails()
        ok = False
        for e in emails:
            if e["message_id"] == message_id:
                e["tag"] = tag
                ok = True
                break
        if ok and not self.is_test_mode():
            # Only persist tag changes in real mode
            self.save_emails(emails)
        return ok

    def get_email_by_id(self, message_id: str) -> Optional[Dict]:
        for e in self.load_emails():
            if e["message_id"] == message_id:
                return e
        return None
