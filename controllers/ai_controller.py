"""
AI operations controller
Handles AI summary generation and AI-based labeling
"""
from typing import Optional, Dict
from tkinter import messagebox

from models.app_state import app_state
from services import StorageService, AIServiceFactory
from services.gmailcimke import apply_label_to_message  # ← ADDED
from utils import strip_html_tags


class AIController:
    """Controller for AI operations"""

    def __init__(self, storage_service: StorageService, ai_provider: str = "perplexity"):
        """Initialize AI controller

        Args:
            storage_service: Email storage service
            ai_provider: AI provider name ("gemini" or "perplexity")
        """
        self.storage = storage_service
        self.ai_client = AIServiceFactory.create(ai_provider)

    def generate_summary(self, email_data: Dict) -> Optional[str]:
        """Generate AI summary for single email

        Args:
            email_data: Email dictionary

        Returns:
            Generated summary or None if failed
        """
        if not self.ai_client:
            messagebox.showerror("Hiba",
                                 "AI API nem elérhető.\n\n"
                                 "Ellenőrizze az API key konfigurációt.")
            return None

        # Extract data
        subject = email_data.get('subject', '')
        body_plain = email_data.get('body_plain', '')
        body_html = email_data.get('body_html', '')
        sender = email_data.get('sender_name', '')

        # Use plain text or strip HTML
        if not body_plain and body_html:
            body_plain = strip_html_tags(body_html)

        if not body_plain or not body_plain.strip():
            return "[Üres email törzs - nincs mit összefoglalni]"

        # Generate summary
        print(f"[AI] Generating summary for '{subject}'...")

        try:
            summary = self.ai_client.summarize_email(subject, body_plain, sender)

            # Save to storage
            all_emails = self.storage.load_emails()
            email_id_map = {e.get("message_id"): e for e in all_emails}
            message_id = email_data.get('message_id')

            if message_id in email_id_map:
                email_id_map[message_id]['ai_summary'] = summary
                email_data['ai_summary'] = summary

            self.storage.save_emails(all_emails)

            print(f"[AI] Summary generated successfully")
            return summary

        except Exception as e:
            print(f"[AI] Error generating summary: {e}")
            return f"[Hiba: {e}]"

    def generate_batch_summaries(self, emails: list, progress_callback=None) -> Dict[str, str]:
        """Generate AI summaries for multiple emails

        Args:
            emails: List of email dictionaries
            progress_callback: Callback function for progress updates

        Returns:
            Dictionary of {message_id: summary}
        """
        if not self.ai_client:
            messagebox.showerror("Hiba", "AI API nem elérhető.")
            return {}

        # Filter emails without summaries
        emails_to_process = [e for e in emails if not e.get('ai_summary')]

        if not emails_to_process:
            messagebox.showinfo("Info", "Minden email már rendelkezik összefoglalóval.")
            return {}

        # Confirm
        result = messagebox.askyesno("Megerősítés",
                                     f"AI összefoglaló generálása {len(emails_to_process)} emailhez?\n\n"
                                     f"Ez eltarthat egy ideig.")
        if not result:
            return {}

        # Generate
        print(f"[AI] Batch generating {len(emails_to_process)} summaries...")

        summaries = {}
        for idx, email in enumerate(emails_to_process, 1):
            if progress_callback:
                progress_callback(idx, len(emails_to_process))

            summary = self.generate_summary(email)
            if summary:
                summaries[email.get('message_id')] = summary

        messagebox.showinfo("Siker", f"AI összefoglaló generálva {len(summaries)} emailhez!")

        return summaries

    # ========== ADDED from branch1 ==========
    def _call_ai_for_label(self, prompt: str) -> str:
        """Promptot küld az AI kliensnek és visszaadja a szöveges választ."""
        if not self.ai_client:
            return ""

        try:
            return self.ai_client.summarize_email(
                subject="Email kategorizálás",
                body_text=prompt,
                sender=""
            ) or ""
        except Exception as e:
            print(f"[AI] Error during label call: {e}")
            return ""

    def auto_label_email(self, email_data: dict) -> None:
        """Kiválasztott email AI-alapú újracímkézése (dict alapú)."""
        if not email_data:
            return

        allowed_categories = [
            "Vezetőség",
            "Hiányos",
            "Hibás csatolmány",
            "Hírlevél",
            "Neptun",
            "Tanulói",
            "Milton",
            "Moodle",
            "Egyéb",
        ]

        subject = email_data.get("subject", "")
        body_preview = email_data.get("body_plain", "") or email_data.get("preview_text", "")

        prompt = (
                f"Válassz PONTOSAN EGY kategóriát az alábbi listából az email alapján.\n\n"
                f"KATEGÓRIÁK:\n"
                + "\n".join([f"- {cat}" for cat in allowed_categories])
                + f"\n\n"
                  f"EMAIL TÁRGYA: {subject}\n\n"
                  f"EMAIL SZÖVEGE: {body_preview[:1500]}\n\n"
                  f"VÁLASZ: Írd le CSAK a kiválasztott kategória pontos nevét, semmi mást!\n"
                  f"NE adj magyarázatot, NE írj mondatot!"
        )

        raw_category = (self._call_ai_for_label(prompt) or "").strip()

        print(f"[AI-LABEL] Nyers válasz: '{raw_category}'")

        category = "Egyéb"
        for allowed in allowed_categories:
            if allowed.lower() in raw_category.lower():
                category = allowed
                print(f"[AI-LABEL] Találat: '{allowed}' a válaszban")
                break

        print(f"[AI-LABEL] Végső kategória: '{category}'")

        # Lokális adat frissítése
        email_data["tag"] = category.lower()

        # Gmail címke ráírása
        message_id = email_data.get("message_id")
        if message_id:
            try:
                apply_label_to_message(message_id, category)
            except Exception as e:
                print(f"[AI-LABEL] Gmail label write failed: {e}")
    # =========================================
