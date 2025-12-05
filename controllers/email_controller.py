"""
Email operations controller
Handles fetching, categorizing, filtering, and sorting emails
"""
from typing import List, Dict, Optional
from tkinter import messagebox
from googleapiclient.errors import HttpError
from email.utils import parseaddr

from models.app_state import app_state
from services import StorageService, GmailService
from business import apply_rules
from utils import format_date_hungarian


class EmailController:
    """Controller for email operations"""
    
    def __init__(self, storage_service: StorageService, gmail_service: Optional[GmailService] = None):
        """Initialize email controller
        
        Args:
            storage_service: Email storage service
            gmail_service: Gmail API service (optional)
        """
        self.storage = storage_service
        self.gmail = gmail_service

    def load_offline_emails(self) -> List[Dict]:
        try:
            emails = self.storage.load_emails()
            if emails:
                # csak azokra futtatunk szabályt, ahol még nincs címke
                uncategorized = [e for e in emails if e.get("tag", "----") == "----"]
                if uncategorized:
                    apply_rules(uncategorized)
                app_state.all_emails = emails
                app_state.update_categorized_counts()
            return emails
        except Exception as e:
            print(f"[ERROR] Failed to load offline emails: {e}")
            messagebox.showerror("Hiba", f"Email betöltési hiba:\n{e}")
            return []

    def fetch_new_emails(self, max_results: int = 100, progress_callback=None) -> List[Dict]:
        """Fetch new emails from Gmail
        
        Args:
            max_results: Maximum number of emails to fetch
            progress_callback: Callback function for progress updates (0-100)
            
        Returns:
            List of synced email dictionaries
        """
        if not self.gmail:
            messagebox.showwarning("Figyelmeztetés", "Kérjük, először jelentkezzen be!")
            return []
        
        if self.storage.is_test_mode():
            messagebox.showinfo("Teszt mód",
                              "Teszt adatállomány (emails_mod.csv) van betöltve.\n"
                              "Frissítés le van tiltva, hogy ne írjuk felül a teszt adatokat.")
            return []
        
        try:
            # Step 1: Fetch message list (0-10%)
            if progress_callback:
                progress_callback(0)
            
            messages = self.gmail.list_inbox(query="", max_results=max_results)
            
            if progress_callback:
                progress_callback(10)
            
            if not messages:
                messagebox.showinfo("Info", "Nincs új email a postaládában.")
                return []
            
            # Step 2: Fetch email details (10-90%)
            gmail_emails = []
            total = len(messages)

            for idx, msg in enumerate(messages, start=1):
                try:
                    details = self.gmail.get_email_full_details(msg["id"])
                    name, addr = parseaddr(details.get("sender", ""))
                    domain = addr.split("@", 1)[-1] if "@" in addr else ""
                    details["sender_name"] = name or addr
                    details["sender_domain"] = domain
                    details.setdefault("mime_types", [])
                    details.setdefault("needs_more_info", 0)
                    details.setdefault("rule_applied", "")

                    # DEBUG 1: Nyers Gmail válasz
                    print(
                        "[DEBUG][GMAIL-RAW]",
                        "id=", details.get("id"),
                        "labels=", details.get("gmail_labels"),
                        "tag=", details.get("tag"),
                    )

                    # GMAIL LABEL → TAG normalizálás (amit már betettél)
                    gmail_tag = details.get("tag")
                    if gmail_tag:
                        norm = gmail_tag.strip().lower()
                        if norm in ["vezetőség", "vezetoseg"]:
                            details["tag"] = "vezetoseg"
                        elif norm in ["tanszék", "tanszek"]:
                            details["tag"] = "tanszek"
                        elif norm == "neptun":
                            details["tag"] = "neptun"
                        elif norm == "moodle":
                            details["tag"] = "moodle"
                        elif norm in ["milt-on", "milton"]:
                            details["tag"] = "milt-on"
                        elif norm in ["hiányos", "hianyos"]:
                            details["tag"] = "hianyos"
                        elif norm in ["egyéb", "egyeb"]:
                            details["tag"] = "egyeb"
                        else:
                            # ismeretlen Gmail tag → NEM erőltetünk semmit, marad ----
                            details["tag"] = "----"
                    else:
                        details.setdefault("tag", "----")

                    # DEBUG 2: Normalizált állapot
                    print(
                        "[DEBUG][GMAIL-NORM]",
                        "id=", details.get("id"),
                        "gmail_labels=", details.get("gmail_labels"),
                        "final_tag=", details.get("tag"),
                    )

                    gmail_emails.append(details)

                except Exception as e:
                    print(f"Hiba az üzenet feldolgozásakor: {e}")
                    continue
                finally:
                    if progress_callback:
                        progress = 10 + int((idx / total) * 80)
                        progress_callback(progress)
            
            # Step 3: Apply rules (90-95%)
            if progress_callback:
                progress_callback(90)
            
            apply_rules(gmail_emails)
            
            if progress_callback:
                progress_callback(95)
            
            # Step 4: Sync with storage (95-100%)
            synced_emails = self.storage.sync_emails(gmail_emails)

            print("[DEBUG][SYNC-OUT][0]", synced_emails[0] if synced_emails else None)
            
            app_state.all_emails = synced_emails
            app_state.update_categorized_counts()
            app_state.reset_filters()
            
            if progress_callback:
                progress_callback(100)
            
            messagebox.showinfo("Siker", f"{len(synced_emails)} email letöltve és szinkronizálva!")
            
            return synced_emails
        
        except HttpError as e:
            messagebox.showerror("Hiba", f"Gmail API hiba: {e}")
            return []
        except Exception as e:
            messagebox.showerror("Hiba", f"Email letöltési hiba: {e}")
            return []
    
    def categorize_selected_emails(self, selected_emails: List[Dict]) -> int:
        """Re-apply categorization rules to selected uncategorized emails
        
        Args:
            selected_emails: List of selected email dictionaries
            
        Returns:
            Number of newly categorized emails
        """
        if not selected_emails:
            messagebox.showinfo("Info",
                              "Nincs kiválasztott email.\n\n"
                              "Válasszon ki egy vagy több emailt a kategorizáláshoz.")
            return 0
        
        # Filter to only uncategorized emails
        uncategorized = [e for e in selected_emails if e.get("tag", "----") == "----"]
        
        if not uncategorized:
            messagebox.showinfo("Info",
                              f"A kiválasztott {len(selected_emails)} email már kategorizálva van.\n\n"
                              f"Csak a '----' címkével rendelkező emailek lesznek újra kategorizálva.")
            return 0
        
        # Apply rules
        apply_rules(uncategorized)
        
        # Count newly categorized
        newly_categorized = sum(1 for email in uncategorized if email.get("tag", "----") != "----")
        
        if newly_categorized == 0:
            messagebox.showinfo("Info",
                              f"A kiválasztott {len(uncategorized)} email nem illeszkedik "
                              f"egyik szabályhoz sem.\n\n"
                              f"Ellenőrizze a config/settings.ini fájlt.")
            return 0
        
        # Save changes
        all_emails = self.storage.load_emails()
        email_id_map = {e.get("message_id"): e for e in all_emails}
        
        for updated_email in uncategorized:
            msg_id = updated_email.get("message_id")
            if msg_id in email_id_map:
                email_id_map[msg_id].update(updated_email)
        
        self.storage.save_emails(all_emails)
        
        app_state.all_emails = all_emails
        app_state.update_categorized_counts()
        
        messagebox.showinfo("Siker",
                          f"Kategorizálva: {newly_categorized}/{len(uncategorized)} email\n\n"
                          f"{'Az új címkék mentésre kerültek.' if not self.storage.is_test_mode() else 'Teszt mód - változások nem mentve.'}")
        
        return newly_categorized
    
    def filter_by_tag(self, tag: str, all_items: List[str], tree_widget) -> List[str]:
        """Filter emails by tag
        
        Args:
            tag: Tag name to filter by
            all_items: List of all treeview item IDs
            tree_widget: Treeview widget
            
        Returns:
            List of visible item IDs
        """
        visible_items = []
        
        for item_id in all_items:
            if tree_widget.exists(item_id):
                email_data = app_state.email_data_map.get(item_id, {})
                item_tag = email_data.get('tag', '----')
                
                if item_tag == tag:
                    try:
                        tree_widget.move(item_id, "", "end")
                        visible_items.append(item_id)
                    except:
                        pass
                else:
                    tree_widget.detach(item_id)
        
        app_state.is_filtered = True
        app_state.current_filter_label = tag.capitalize()
        
        return visible_items
    
    def filter_by_attachment(self, all_items: List[str], tree_widget) -> List[str]:
        """Filter emails with attachments
        
        Args:
            all_items: List of all treeview item IDs
            tree_widget: Treeview widget
            
        Returns:
            List of visible item IDs
        """
        visible_items = []
        
        for item_id in all_items:
            if tree_widget.exists(item_id):
                email_data = app_state.email_data_map.get(item_id, {})
                
                if int(email_data.get("attachment_count", 0)) > 0:
                    try:
                        tree_widget.move(item_id, "", "end")
                        visible_items.append(item_id)
                    except:
                        pass
                else:
                    tree_widget.detach(item_id)
        
        app_state.is_filtered = True
        app_state.attachment_filter_active = True
        app_state.current_filter_label = "Csatolmány"
        
        return visible_items
    
    def clear_filters(self, all_items: List[str], tree_widget):
        """Clear all filters
        
        Args:
            all_items: List of all treeview item IDs
            tree_widget: Treeview widget
        """
        for item_id in all_items:
            if tree_widget.exists(item_id):
                try:
                    tree_widget.move(item_id, "", "end")
                except:
                    pass
        
        app_state.reset_filters()
    
    def sort_emails(self, sort_column: str, reverse: bool = False) -> List[tuple]:
        """Sort emails by column
        
        Args:
            sort_column: Column name to sort by
            reverse: Sort in reverse order
            
        Returns:
            List of (item_id, email_dict) tuples in sorted order
        """
        items = [(item_id, app_state.email_data_map[item_id]) 
                for item_id in app_state.all_tree_items 
                if item_id in app_state.email_data_map]
        
        if sort_column == "Sender":
            items.sort(key=lambda x: x[1].get("sender_name", "").lower(), reverse=reverse)
        elif sort_column == "Subject":
            items.sort(key=lambda x: x[1].get("subject", "").lower(), reverse=reverse)
        elif sort_column == "Tag":
            items.sort(key=lambda x: x[1].get("tag", "").lower(), reverse=reverse)
        elif sort_column == "Attach":
            items.sort(key=lambda x: int(x[1].get("attachment_count", 0)), reverse=reverse)
        elif sort_column == "AI":
            items.sort(key=lambda x: 1 if x[1].get("ai_summary") else 0, reverse=reverse)
        elif sort_column == "Date":
            items.sort(key=lambda x: x[1].get("datetime", ""), reverse=reverse)
        
        return items

    def update_tag_for_email(self, updated_email: Dict, new_tag: str) -> None:
        """Egy email címkéjének frissítése és mentése CSV-be (message_id alapján)."""
        try:
            all_emails = self.storage.load_emails()
        except Exception as e:
            print(f"[ERROR] Cannot load emails for tag update: {e}")
            return

        email_id_map = {e.get("message_id"): e for e in all_emails}
        msg_id = updated_email.get("message_id")

        if not msg_id or msg_id not in email_id_map:
            print(f"[WARN] Email with message_id={msg_id} not found in storage; tag not saved.")
            return

        email_in_storage = email_id_map[msg_id]
        email_in_storage["tag"] = new_tag

        try:
            self.storage.save_emails(all_emails)
            app_state.all_emails = all_emails
            app_state.update_categorized_counts()
            print(f"[INFO] Tag saved for message_id={msg_id}: {new_tag}")
        except Exception as e:
            print(f"[ERROR] Failed to save tag change: {e}")

        # --------- ÚJ: Gmail label szinkron ---------
        if self.gmail:
            try:
                # new_tag: 'vezetoseg' / 'tanszek' / 'neptun' / 'moodle' / 'milt-on' / 'hianyos' / 'egyeb' / '----'
                self.gmail.set_message_label(msg_id, new_tag)
            except Exception as e:
                print(f"[GMAIL] Failed to update label for {msg_id}: {e}")