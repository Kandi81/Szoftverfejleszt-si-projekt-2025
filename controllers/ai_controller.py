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
        """Promptot küld az AI-nak kategória választáshoz (NEM összefoglaláshoz!)"""
        if not self.ai_client:
            return ""

        try:
            # Közvetlenül a Perplexity chat.completions API-t hívjuk
            if hasattr(self.ai_client, 'client') and self.ai_client.client:
                response = self.ai_client.client.chat.completions.create(
                    model="sonar",
                    messages=[
                        {
                            "role": "system",
                            "content": "Te egy email kategorizáló asszisztens vagy. Válaszolj CSAK a kategória nevével, semmi mással!"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=15,  # maximum 1-2 szó
                    temperature=0.2  # determinisztikus válasz
                )

                raw = response.choices[0].message.content.strip()
                print(f"[AI-LABEL-DEBUG] Perplexity nyers válasz: '{raw}'")
                return raw
            else:
                # Fallback: ha nincs közvetlen client
                print("[AI-LABEL] Nincs közvetlen Perplexity client, fallback...")
                return self.ai_client.summarize_email(
                    subject="Kategória választás",
                    body_text=prompt,
                    sender=""
                ) or ""

        except Exception as e:
            print(f"[AI] Error during label call: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def auto_label_email(self, email_data: dict) -> None:
        """Kiválasztott email AI-alapú újracímkézése (dict alapú)."""

        print(f"[AI-LABEL] ========== KATEGORIZÁLÁS KEZDÉS ==========")

        if not email_data:
            print(f"[AI-LABEL] ✗ email_data üres!")
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
        #body_preview = email_data.get("body_plain", "") or email_data.get("preview_text", "")
        body_plain = email_data.get("body_plain", "")
        body_html = email_data.get("body_html", "")
        preview_text = email_data.get("preview_text", "")

        # Próbáljuk sorban
        if body_plain and body_plain.strip():
            body_preview = body_plain
        elif body_html and body_html.strip():
            # HTML-ből kivesszük a tag-eket egyszerűen
            import re
            body_preview = re.sub(r'<[^>]+>', '', body_html)  # strip HTML tags
        elif preview_text and preview_text.strip():
            body_preview = preview_text
        else:
            body_preview = ""

        print(f"[AI-LABEL-DEBUG] body_plain: {len(body_plain)} kar")
        print(f"[AI-LABEL-DEBUG] body_html: {len(body_html)} kar")
        print(f"[AI-LABEL-DEBUG] body_preview használt: {len(body_preview)} kar")
        sender_name = email_data.get("sender_name", "")
        message_id = email_data.get("message_id")

        print(f"[AI-LABEL] Email: '{subject}'")
        print(f"[AI-LABEL] Message ID: '{message_id}'")
#################DEBUG############
        print(f"[AI-LABEL-DEBUG] Email adatok:")
        print(f"  sender_name: '{sender_name}'")
        print(f"  sender: '{email_data.get('sender', 'N/A')}'")
        print(f"  sender_domain: '{email_data.get('sender_domain', 'N/A')}'")
        print(f"  subject: '{subject}'")
        print(f"  body_preview (első 100 kar): '{body_preview[:100] if body_preview else '[ÜRES]'}'")

        prompt = (
            f"Kategorizálj egy egyetemi oktatónak címzett emailt!\n\n"

            f"=== KATEGÓRIÁK ===\n\n"

            f"TANULÓI\n"
            f"- Hallgató ír tanárnak (kérdés, beadandó, konzultáció)\n"
            f"- Bármilyen email cím (gmail, freemail, stb.)\n"
            f"- Példa tárgy: 'Kérdés a vizsgáról', 'Beadandó'\n\n"

            f"VEZETŐSÉG\n"
            f"- Feladó: grajczjar.istvan@uni-milton.hu, toth.tamas@uni-milton.hu\n"
            f"- Rektori/dékáni hivatalos levelek\n\n"

            f"TANSZÉK\n"
            f"- Feladó: honfi@uni-milton.hu, barkanyi.pal@uni-milton.hu\n"
            f"- Tanszéki kollégák levelei\n\n"

            f"NEPTUN\n"
            f"- Feladó: noreply@uni-milton.hu\n"
            f"- Tárgy VAGY tartalom tartalmazza: 'Neptun'\n"
            f"- Jegyek, vizsgák, beiratkozás\n\n"

            f"MOODLE\n"
            f"- Feladó: noreply@uni-milton.hu\n"
            f"- Tárgy VAGY tartalom tartalmazza: 'Moodle'\n"
            f"- Kurzus értesítések, feladatok\n\n"

            f"MILTON\n"
            f"- Feladó domain: @milt-on.hu\n\n"

            f"HÍRLEVÉL\n"
            f"- Marketing, promóciók, reklámok\n"
            f"- Newsletter feliratkozás\n\n"

            f"HIÁNYOS\n"
            f"- CSAK hallgatói levél, DE hiányzik:\n"
            f"  - tárgy VAGY\n"
            f"  - törzs VAGY\n"

            f"EGYÉB\n"
            f"- Minden más\n\n"

            f"=== EMAIL ===\n"
            f"Feladó: {email_data.get('sender', 'N/A')}\n"
            f"Domain: {email_data.get('sender_domain', 'N/A')}\n"
            f"Tárgy: {subject if subject else '[NINCS]'}\n"
            f"Törzs: {body_preview[:600] if body_preview else '[NINCS]'}\n\n"

            f"=== DÖNTÉSI SOR ===\n"
            f"1. Ha 'Neptun' van a tárgyban/törzsben → NEPTUN\n"
            f"2. Ha 'Moodle' van a tárgyban/törzsben → MOODLE\n"
            f"3. Ha domain @milt-on.hu → MILTON\n"
            f"4. Ha hallgató jellegű (kérdez/beadandó) ÉS van tárgy+törzs+név → TANULÓI\n"
            f"6. Ha vezetőségi email cím → VEZETŐSÉG\n"
            f"7. Ha tanszéki email cím → TANSZÉK\n"
            f"8. Ha marketing → HÍRLEVÉL\n"
            f"9. Különben → EGYÉB\n\n"

            f"VÁLASZ (CSAK 1 SZÓ!):\n"
            f"Tanulói | Vezetőség | Tanszék | Neptun | Moodle | Milton | Hírlevél | Hiányos | Egyéb\n\n"
        )

        print(f"[AI-LABEL] AI hívás indítása...")
        raw_category = (self._call_ai_for_label(prompt) or "").strip()

        print(f"[AI-LABEL] Nyers válasz: '{raw_category}'")

        category = "Egyéb"
        for allowed in allowed_categories:
            if allowed.lower() in raw_category.lower():
                category = allowed
                print(f"[AI-LABEL] Találat: '{allowed}' a válaszban")
                break

        print(f"[AI-LABEL] Végső kategória: '{category}'")

        # Lokális adat frissítése (NE lower()!)
        email_data["tag"] = category
        print(f"[AI-LABEL] email_data['tag'] beállítva: '{category}'")

        # Gmail címke ráírása
        if message_id:
            print(f"[AI-LABEL] Gmail címke alkalmazás kezdése...")
            print(f"[AI-LABEL]   message_id: '{message_id}'")
            print(f"[AI-LABEL]   category: '{category}'")
            try:
                from services.gmailcimke import apply_label_to_message
                apply_label_to_message(message_id, category)
                print(f"[AI-LABEL] ✓ Gmail címke SIKERESEN alkalmazva!")
            except Exception as e:
                print(f"[AI-LABEL] ✗ HIBA Gmail címke alkalmazáskor: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[AI-LABEL] ✗ NINCS message_id, címke NEM írható vissza!")

        print(f"[AI-LABEL] ========== KATEGORIZÁLÁS VÉGE ==========")

    # =========================================
