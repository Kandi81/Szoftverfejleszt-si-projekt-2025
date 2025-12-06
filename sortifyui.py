import sys
import os

# Fix tkhtmlview compatibility
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkhtmlview import HTMLScrolledText

from models import app_state
from utils import resource_path, format_date_hungarian, clean_html_for_display
from utils.config_helper import get_ai_consent
from services.attachment_cache_service import AttachmentCacheService
from ui.ai_consent_dialog import show_ai_consent_dialog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

email_controller = None
ai_controller = None
auth_controller = None

detail_widgets = {}
select_all_var = None

attachment_cache = AttachmentCacheService()

AI_ICON = "✨"


def populate_tree_from_emails(emails):
    treeemails.delete(*treeemails.get_children())
    app_state.all_tree_items.clear()
    app_state.email_data_map.clear()

    emails.sort(key=lambda x: x.get("datetime", ""), reverse=True)

    for idx, e in enumerate(emails):
        formatted_date = format_date_hungarian(e.get("datetime", "N/A"))
        ai_indicator = AI_ICON if e.get('ai_summary') else ""

        values = (
            e.get("sender_name", ""),
            e.get("subject", "(no subject)"),
            e.get("tag", "----"),
            e.get("attachment_count", 0),
            ai_indicator,
            formatted_date,
        )

        tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
        item_id = treeemails.insert("", tk.END, values=values, tags=(tag,))
        app_state.all_tree_items.append(item_id)
        app_state.email_data_map[item_id] = e


def update_tag_counts_from_storage(emails):
    """Frissíti a címke gombok számlálóit a megadott email-lista alapján."""
    if emails is None:
        emails = app_state.all_emails or []

    counts = {
        'vezetoseg': 0,
        'tanszek': 0,
        'neptun': 0,
        'moodle': 0,
        'milt-on': 0,
        'hianyos': 0,
        'egyeb': 0,
    }

    for e in emails:
        tag = (e.get('tag') or '').lower()
        if tag in counts:
            counts[tag] += 1

    app_state.categorized_counts = counts

    btntagvezetosegi.config(
        text=f"Vezetőség ({counts['vezetoseg']})",
        state="normal" if counts['vezetoseg'] > 0 else "disabled",
    )
    btntagtanszek.config(
        text=f"Tanszék ({counts['tanszek']})",
        state="normal" if counts['tanszek'] > 0 else "disabled",
    )
    btntagneptun.config(
        text=f"Neptun ({counts['neptun']})",
        state="normal" if counts['neptun'] > 0 else "disabled",
    )
    btntagmoodle.config(
        text=f"Moodle ({counts['moodle']})",
        state="normal" if counts['moodle'] > 0 else "disabled",
    )
    btntagmilton.config(
        text=f"Milt-On ({counts['milt-on']})",
        state="normal" if counts['milt-on'] > 0 else "disabled",
    )
    btntaghianyos.config(
        text=f"Hiányos ({counts['hianyos']})",
        state="normal" if counts['hianyos'] > 0 else "disabled",
    )
    btntagegyeb.config(
        text=f"Egyéb ({counts['egyeb']})",
        state="normal" if counts['egyeb'] > 0 else "disabled",
    )


def update_attachment_button_count(_emails):
    count = app_state.get_attachment_count()
    btnattachfilter.config(text=f"Csatolmány ({count})")
    btnattachfilter.config(state="normal" if count > 0 else "disabled")


def load_offline_emails():
    if email_controller is None:
        print("[ERROR] email_controller not initialized")
        return

    try:
        emails = email_controller.load_offline_emails()

        if not emails:
            treeemails.insert(
                "",
                tk.END,
                values=("Feladó/Email/Tag/📎/AI/Dátum megjelenik itt", "", "", "", "", "")
            )
            return

        populate_tree_from_emails(emails)
        update_tag_counts_from_storage(emails)
        update_attachment_button_count(emails)

        if emails:
            chkselectall.config(state="normal")

        if app_state.is_test_mode():
            test_mode_label.config(
                text="⚠ TESZT MÓD: emails_mod.csv betöltve - frissítés letiltva"
            )

        print("DEBUG counts on startup:", app_state.categorized_counts)

    except Exception as e:
        print(f"[ERROR] Failed to load offline emails: {e}")
        messagebox.showerror("Hiba", f"Email betöltési hiba:\n{e}")


def truncate_filename(filename: str, max_length: int = 20) -> str:
    if len(filename) <= max_length:
        return filename
    if '.' in filename:
        name_part, ext_part = filename.rsplit('.', 1)
        ext_with_dot = '.' + ext_part
        available = max_length - len(ext_with_dot) - 3
        if available < 1:
            return filename[:max_length]
        return f"{name_part[:available]}...{ext_with_dot}"
    return filename[:max_length - 3] + "..."


def verify_attachment_safety(email_id: str, filename: str) -> tuple:
    cached = attachment_cache.get_verification(email_id, filename)
    if cached:
        return (cached['is_safe'], cached.get('reason'))

    is_safe = True
    reason = None
    if not filename:
        return (True, None)

    dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js', '.jar', '.app', '.msi', '.dll']
    filename_lower = filename.lower()

    parts = filename_lower.split('.')
    if len(parts) > 2:
        doc_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'png', 'jpg', 'jpeg']
        if len(parts) >= 3 and parts[-2] in doc_extensions:
            is_safe = False
            reason = f"Dupla kiterjesztés: .{parts[-2]}.{parts[-1]} (gyanús átnevezés)"

    if is_safe:
        for ext in dangerous_extensions:
            if filename_lower.endswith(ext):
                is_safe = False
                reason = f"Veszélyes fájltípus: {ext}"
                break

    attachment_cache.store_verification(email_id, filename, is_safe, reason)
    return (is_safe, reason)


def update_details_panel(email_data):
    if not email_data:
        detail_widgets['sender_value'].config(text="")
        detail_widgets['subject_value'].config(text="")
        detail_widgets['date_value'].config(text="")
        detail_widgets['tag_var'].set("")
        detail_widgets['ai_summary'].config(state='normal')
        detail_widgets['ai_summary'].delete('1.0', tk.END)
        detail_widgets['ai_summary'].config(state='disabled')

        notebook = detail_widgets['notebook']
        for tab in notebook.tabs():
            notebook.forget(tab)

        msg_tab = detail_widgets['message_tab']
        notebook.add(msg_tab, text="Üzenet")
        detail_widgets['message_display'].set_html(
            '<p style="color: #999;">Válasszon ki egy emailt a részletek megtekintéséhez.</p>')
        return

    detail_widgets['sender_value'].config(text=email_data.get('sender_name', 'N/A'))
    detail_widgets['subject_value'].config(text=email_data.get('subject', '(no subject)'))
    detail_widgets['date_value'].config(text=email_data.get('datetime', 'N/A'))

    tag = email_data.get('tag', '----')
    if tag and tag != '----':
        tag_map = {
            'vezetoseg': 'Vezetőség',
            'tanszek': 'Tanszék',
            'neptun': 'Neptun',
            'moodle': 'Moodle',
            'milt-on': 'Milt-On',
            'hianyos': 'Hiányos',
            'egyeb': 'Egyéb',
        }
        tag_display = tag_map.get(tag.lower(), tag.capitalize())
        detail_widgets['tag_var'].set(tag_display)
    else:
        detail_widgets['tag_var'].set("")

    ai_summary = email_data.get('ai_summary', '')
    detail_widgets['ai_summary'].config(state='normal')
    detail_widgets['ai_summary'].delete('1.0', tk.END)
    if ai_summary:
        detail_widgets['ai_summary'].insert('1.0', ai_summary)
    else:
        detail_widgets['ai_summary'].insert('1.0', '[Még nincs AI összefoglaló - kattints a ✨ gombra a generáláshoz]')
    detail_widgets['ai_summary'].config(state='disabled')

    notebook = detail_widgets['notebook']
    for tab in notebook.tabs():
        notebook.forget(tab)

    msg_tab = detail_widgets['message_tab']
    notebook.add(msg_tab, text="Üzenet")

    body_html = email_data.get('body_html', '')
    body_plain = email_data.get('body_plain', '')

    try:
        if body_html:
            cleaned_html = clean_html_for_display(body_html)
            detail_widgets['message_display'].set_html(cleaned_html)
        elif body_plain:
            escaped_plain = body_plain.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            detail_widgets['message_display'].set_html(
                f'<pre style="font-family: Arial; font-size: 12px; white-space: pre-wrap;">{escaped_plain}</pre>')
        else:
            detail_widgets['message_display'].set_html('<p style="color: #999;">Nincs üzenet törzs.</p>')
    except Exception as e:
        print(f"[ERROR] Failed to render HTML body: {e}")
        if body_plain:
            escaped_plain = body_plain.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            detail_widgets['message_display'].set_html(
                f'<pre style="font-family: Arial; font-size: 12px;">{escaped_plain[:1000]}</pre>')
        else:
            detail_widgets['message_display'].set_html('<p style="color: red;">Hiba az email megjelenítése során.</p>')

    attachment_names = email_data.get('attachment_names', '')
    email_id = email_data.get('id', 'unknown')

    attachments = []
    if attachment_names and isinstance(attachment_names, str):
        import re
        attachments = [a.strip() for a in re.split(r'[;|]', attachment_names) if a.strip()]
    elif isinstance(attachment_names, list):
        attachments = [str(a).strip() for a in attachment_names if str(a).strip()]

    for idx, filename in enumerate(attachments[:3]):
        display_name = truncate_filename(filename, max_length=20)
        is_safe, reason = verify_attachment_safety(email_id, filename)
        att_tab = tk.Frame(notebook, bg="#FFFFFF")

        tab_text = f"✅ {display_name}" if is_safe else f"⚠️ {display_name}"
        notebook.add(att_tab, text=tab_text)

        att_text = tk.Text(
            att_tab,
            wrap=tk.WORD,
            state='disabled',
            bg="#FFFFFF",
            font=("Segoe UI", 10),
            relief="flat"
        )
        att_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        att_text.config(state='normal')
        if not is_safe:
            att_text.tag_configure("warning_header", background="#F8D7DA", foreground="#721C24",
                                   font=("Segoe UI", 11, "bold"))
            att_text.insert('1.0', "⚠️ FIGYELEM: Gyanús csatolmány!\n\n", "warning_header")
            att_text.insert('end',
                            f"📎 Fájl: {filename}\n\n"
                            f"🔍 Probléma: {reason}\n\n"
                            f"⚠️ JAVASOLT TEENDŐ:\n"
                            f"• Ne nyissa meg ezt a fájlt!\n"
                            f"• Ellenőrizze a feladóval telefonon/személyesen\n"
                            f"• Jelentse a biztonsági csapatnak\n"
                            f"• Törölje az emailt ha nem várt\n")
        else:
            att_text.tag_configure("safe_header", background="#D4EDDA", foreground="#155724",
                                   font=("Segoe UI", 11, "bold"))
            att_text.insert('1.0', f"✅ Biztonságos csatolmány\n\n", "safe_header")
            att_text.insert('end',
                            f"📎 Fájl: {filename}\n\n"
                            f"✓ A fájl automatikus ellenőrzésen átment\n"
                            f"✓ Nem tartalmaz gyanús kiterjesztést\n\n"
                            f"[AI összefoglaló a csatolmány tartalmáról - funkció fejlesztés alatt]")
        att_text.config(state='disabled')


def on_tree_select(_event=None):
    selected_items = treeemails.selection()

    if selected_items and not app_state.is_filtered:
        btncategorize.config(state="normal")
    else:
        btncategorize.config(state="disabled")

    # Enable AI címkézés gomb 1 elemnél
    if len(selected_items) == 1:
        btnailabel.config(state="normal")
    else:
        btnailabel.config(state="disabled")

    if len(selected_items) == 1:
        item_id = selected_items[0]
        email_data = app_state.email_data_map.get(item_id, {})
        update_details_panel(email_data)
    else:
        update_details_panel(None)


def generate_summary_for_selected_single():
    if ai_controller is None:
        messagebox.showerror("Hiba", "AI controller not initialized")
        return

    selected_items = treeemails.selection()
    if len(selected_items) != 1:
        messagebox.showinfo("Info", "Válasszon ki pontosan egy emailt az AI összefoglaló generálásához.")
        return

    if not get_ai_consent():
        result = show_ai_consent_dialog(windowsortify)
        if not result:
            return

    item_id = selected_items[0]
    email_data = app_state.email_data_map.get(item_id, {})
    if not email_data:
        return

    if email_data.get('ai_summary'):
        result = messagebox.askyesno("Megerősítés",
                                     "Ez az email már rendelkezik AI összefoglalóval.\n\n"
                                     "Újra generálod?")
        if not result:
            return

    detail_widgets['ai_summary'].config(state='normal')
    detail_widgets['ai_summary'].delete('1.0', tk.END)
    detail_widgets['ai_summary'].insert('1.0', '⏳ Összefoglaló generálása folyamatban...')
    detail_widgets['ai_summary'].config(state='disabled')
    windowsortify.update()

    print(f"[AI] Generating summary for '{email_data.get('subject', '')}'...")
    summary = ai_controller.generate_summary(email_data)
    if not summary:
        summary = "[Hiba: nem sikerült összefoglalót generálni]"

    detail_widgets['ai_summary'].config(state='normal')
    detail_widgets['ai_summary'].delete('1.0', tk.END)
    detail_widgets['ai_summary'].insert('1.0', summary)
    detail_widgets['ai_summary'].config(state='disabled')

    values = list(treeemails.item(item_id, 'values'))
    values[4] = AI_ICON
    treeemails.item(item_id, values=values)

    print(f"[AI] Summary generated successfully")


def ai_label_single_email():
    """AI-based labeling for single selected email."""
    if ai_controller is None:
        messagebox.showerror("Hiba", "AI controller not initialized")
        return

    selected_items = treeemails.selection()
    if len(selected_items) != 1:
        messagebox.showinfo("Info",
                            "Válasszon ki pontosan egy emailt az AI címkézéshez.")
        return

    if not get_ai_consent():
        result = show_ai_consent_dialog(windowsortify)
        if not result:
            return

    item_id = selected_items[0]
    email_data = app_state.email_data_map.get(item_id, {})
    if not email_data:
        return

    result = messagebox.askyesno("Megerősítés",
                                 f"AI alapú címkézés futtatása erre az emailre?\n\n"
                                 f"Tárgy: {email_data.get('subject', '')[:50]}")
    if not result:
        return

    print(f"[AI-LABEL] Running for '{email_data.get('subject', '')}'...")

    try:
        # AI címkézés (ez már ráírja a Gmail-re is!)
        ai_controller.auto_label_email(email_data)

        # TreeView frissítése
        current_values = list(treeemails.item(item_id, "values"))
        current_values[2] = email_data.get("tag", "----")
        treeemails.item(item_id, values=current_values)

        # Részletek panel frissítése
        update_details_panel(email_data)

        # CSAK CSV mentés, Gmail címke már meg van!
        # (a auto_label_email már meghívta az apply_label_to_message-t)
        if email_controller:
            # Save csak CSV-be, NE írjon Gmail-re
            email_controller.storage.save_emails(app_state.all_emails)
            print(f"[INFO] Tag saved for message_id={email_data.get('message_id')}: {email_data.get('tag')}")

        # Címke számok frissítése
        update_tag_counts_from_storage(app_state.all_emails)

        messagebox.showinfo(
            "Siker",
            f"AI címkézés kész!\n\nÚj címke: {email_data.get('tag', '----')}"
        )
    except Exception as e:
        messagebox.showerror("Hiba", f"AI címkézés sikertelen:\n{e}")
        import traceback
        traceback.print_exc()


def get_emails(_event):
    if email_controller is None:
        messagebox.showerror("Hiba", "Email controller not initialized")
        return
    if not auth_controller or not auth_controller.is_authenticated():
        messagebox.showwarning("Figyelmeztetés", "Kérjük, először jelentkezzen be!")
        return
    if app_state.is_test_mode():
        messagebox.showinfo("Teszt mód",
                            "Teszt adatállomány (emails_mod.csv) van betöltve.\n"
                            "Frissítés le van tiltva, hogy ne írjuk felül a teszt adatokat.")
        return

    # jobbra tolva az AI gomb miatt
    lbl_progress_status.config(text="Letöltés...")
    lbl_progress_status.place(x=500, y=14, width=90, height=22)

    pbaremails.config(value=0)
    pbaremails.place(x=600, y=14, width=150, height=22)

    lbl_progress_percent.config(text="0%")
    lbl_progress_percent.place(x=760, y=14, width=40, height=22)

    windowsortify.update()

    try:
        def update_progress(value, current=None, total=None):
            pbaremails.config(value=value)
            lbl_progress_percent.config(text=f"{int(value)}%")
            if current is not None and total is not None:
                lbl_progress_status.config(text=f"Letöltés ({current}/{total})")
            windowsortify.update()

        synced_emails = email_controller.fetch_new_emails(
            max_results=100,
            progress_callback=update_progress
        )

        # DEBUG: Gmail címkék (egyszerűsítve, mert csak 'tag'-gel dolgozunk)
        if synced_emails:
            for mail in synced_emails[:5]:
                print(
                    "[DEBUG][GMAIL]",
                    "message_id=", mail.get("message_id"),
                    "tag=", mail.get("tag"),
                )

        if synced_emails:
            app_state.all_emails = synced_emails
            populate_tree_from_emails(synced_emails)
            update_tag_counts_from_storage(synced_emails)
            update_attachment_button_count(synced_emails)
            chkselectall.config(state="normal")
            print("[DEBUG][UI][0]", synced_emails[0].get("tag"))

        pbaremails.config(value=100)
        lbl_progress_percent.config(text="100%")
        lbl_progress_status.config(text="Kész!")
        windowsortify.update()

    except Exception as e:
        messagebox.showerror("Hiba", f"Email letöltési hiba: {e}")
    finally:
        windowsortify.after(1500, lambda: lbl_progress_status.place_forget())
        windowsortify.after(1500, lambda: pbaremails.place_forget())
        windowsortify.after(1500, lambda: lbl_progress_percent.place_forget())


def filter_by_tag(tag_name):
    if email_controller is None:
        return

    email_controller.filter_by_tag(
        tag_name,
        app_state.all_tree_items,
        treeemails
    )

    treeemails.selection_remove(treeemails.get_children())
    btncategorize.config(state="disabled")
    btnclearfilters.place(x=851, y=636, width=150, height=30)


def filter_by_attachment():
    if email_controller is None:
        return

    email_controller.filter_by_attachment(
        app_state.all_tree_items,
        treeemails
    )

    treeemails.selection_remove(treeemails.get_children())
    btncategorize.config(state="disabled")
    btnclearfilters.place(x=851, y=636, width=150, height=30)


def clear_filters():
    if email_controller is None:
        return

    email_controller.clear_filters(app_state.all_tree_items, treeemails)
    treeemails.selection_remove(treeemails.get_children())
    btncategorize.config(state="disabled")
    btnclearfilters.place_forget()


def categorize_emails():
    if email_controller is None:
        messagebox.showerror("Hiba", "Email controller not initialized")
        return

    selected_items = treeemails.selection()
    if not selected_items:
        messagebox.showinfo("Info",
                            "Nincs kiválasztott email.\n\nVálasszon ki egy vagy több emailt a kategorizáláshoz.")
        return

    selected_emails = [app_state.email_data_map[item] for item in selected_items if item in app_state.email_data_map]
    count = email_controller.categorize_selected_emails(selected_emails)

    if count > 0:
        populate_tree_from_emails(app_state.all_emails)
        update_tag_counts_from_storage(app_state.all_emails)

    treeemails.selection_remove(treeemails.get_children())


def sort_tree_by_column(col_name):
    if email_controller is None:
        return

    if app_state.sort_column == col_name:
        app_state.sort_reverse = not app_state.sort_reverse
    else:
        app_state.sort_column = col_name
        app_state.sort_reverse = False

    sorted_items = email_controller.sort_emails(col_name, app_state.sort_reverse)

    for idx, (item_id, _) in enumerate(sorted_items):
        treeemails.move(item_id, "", idx)

    for col in ["Sender", "Subject", "Tag", "Attach", "AI", "Date"]:
        header_text = {
            "Sender": "Feladó",
            "Subject": "Email",
            "Tag": "Cimke",
            "Attach": attach_header,
            "AI": "✨",
            "Date": "Dátum"
        }[col]

        if col == col_name:
            arrow = " ▼" if app_state.sort_reverse else " ▲"
            treeemails.heading(col, text=header_text + arrow)
        else:
            treeemails.heading(col, text=header_text)


def select_all():
    is_checked = select_all_var.get()
    if is_checked:
        treeemails.selection_set(treeemails.get_children())
    else:
        treeemails.selection_remove(treeemails.get_children())


def uncheck_select_all_checkbox(_event):
    select_all_var.set(False)


def open_settings():
    from settings_ui import SettingsWindow
    SettingsWindow(windowsortify)


def update_get_emails_button_state():
    if auth_controller and auth_controller.can_refresh_emails():
        btngetmails.config(state="normal")
    else:
        btngetmails.config(state="disabled")


def session_login():
    if auth_controller is None:
        messagebox.showerror("Hiba", "Auth controller not initialized")
        return

    if btnsession.cget("text") == "Kijelentkezés":
        auth_controller.logout()
        btnsession.config(text="Bejelentkezés")
        update_get_emails_button_state()
    else:
        gmail_client = auth_controller.login()
        if gmail_client and email_controller:
            email_controller.gmail = gmail_client
        if gmail_client:
            btnsession.config(text="Kijelentkezés")
            update_get_emails_button_state()


def check_initial_login_state():
    if auth_controller is None:
        btnsession.config(text="Bejelentkezés")
        update_get_emails_button_state()
        return

    gmail_client = auth_controller.check_auto_login()
    if gmail_client and email_controller:
        email_controller.gmail = gmail_client

    btnsession.config(text="Kijelentkezés" if gmail_client else "Bejelentkezés")
    update_get_emails_button_state()


def on_key_press(event):
    if event.state == 4 and event.keysym.lower() == 'r':
        if auth_controller and auth_controller.can_refresh_emails():
            get_emails(None)
    elif event.keysym == 'Escape':
        if app_state.is_filtered:
            clear_filters()


# ========== WINDOW & WIDGET CREATION ==========

windowsortify = tk.Tk()
windowsortify.title("Sortify v1.0")
windowsortify.config(bg="#E4E2E2")
windowsortify.geometry("1724x743")

style = ttk.Style(windowsortify)
style.theme_use("clam")

frameactionbar = tk.Frame(master=windowsortify)
frameactionbar.config(bg="#EDECEC")
frameactionbar.place(x=8, y=0, width=1710, height=55)

framemain = tk.Frame(master=windowsortify)
framemain.config(bg="#EDECEC")
framemain.place(x=5, y=59, width=1011, height=680)

framedetails = tk.Frame(master=windowsortify, relief=tk.GROOVE, borderwidth=2)
framedetails.config(bg="#F5F5F5")
framedetails.place(x=1020, y=59, width=700, height=680)

test_mode_label = tk.Label(master=framemain,
                           text="",
                           bg="#EDECEC",
                           fg="#AA0000",
                           anchor="w")
test_mode_label.place(x=10, y=0, width=800, height=20)

style.configure("btngetmails.TButton", background="#E4E2E2", foreground="#000")
style.map("btngetmails.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btngetmails = ttk.Button(master=frameactionbar, text="Letöltés / Frissítés", style="btngetmails.TButton",
                         state="disabled")
btngetmails.bind("<Button-1>", get_emails)
btngetmails.place(x=10, y=9, width=140, height=40)

style.configure("btncategorize.TButton", background="#E4E2E2", foreground="#000")
style.map("btncategorize.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btncategorize = ttk.Button(master=frameactionbar, text="Kategorizálás", style="btncategorize.TButton",
                           command=categorize_emails, state="disabled")
btncategorize.place(x=160, y=9, width=110, height=40)

# AI Címkézés button
style.configure("btnailabel.TButton", background="#E4E2E2", foreground="#000")
style.map("btnailabel.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btnailabel = ttk.Button(master=frameactionbar, text="✨ AI Címkézés", style="btnailabel.TButton",
                        command=lambda: ai_label_single_email(), state="disabled")
btnailabel.place(x=280, y=9, width=120, height=40)

style.configure("chkselectall.TCheckbutton", background="#EDECEC", foreground="#000")
select_all_var = tk.BooleanVar(value=False)
chkselectall = ttk.Checkbutton(master=frameactionbar, text="Mind",
                               style="chkselectall.TCheckbutton",
                               variable=select_all_var,
                               command=select_all,
                               state="disabled")
chkselectall.place(x=410, y=14, width=70, height=30)

lbl_progress_status = tk.Label(master=frameactionbar,
                               text="",
                               bg="#EDECEC",
                               fg="#333",
                               font=("Segoe UI", 9),
                               anchor="w")

style.configure("btnsettings.TButton", background="#E4E2E2", foreground="#000", font=("Segoe UI Symbol", 16))
style.map("btnsettings.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000")])

btnsettings = ttk.Button(master=frameactionbar, text="⚙", style="btnsettings.TButton",
                         command=open_settings)
btnsettings.place(x=1565, y=9, width=40, height=40)

style.configure("btnsession.TButton", background="#E4E2E2", foreground="#000")
style.map("btnsession.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btnsession = ttk.Button(master=frameactionbar, text="Bejelentkezés", style="btnsession.TButton",
                        command=session_login)
btnsession.place(x=1609, y=9, width=90, height=40)

style.configure("btntagvezetosegi.TButton", background="#E4E2E2", foreground="#000")
btntagvezetosegi = ttk.Button(master=framemain, text="Vezetőség (0)", style="btntagvezetosegi.TButton",
                              state="disabled", command=lambda: filter_by_tag("vezetoseg"))
btntagvezetosegi.place(x=9, y=636, width=120, height=30)

style.configure("btntagtanszek.TButton", background="#E4E2E2", foreground="#000")
btntagtanszek = ttk.Button(master=framemain, text="Tanszék (0)", style="btntagtanszek.TButton",
                           state="disabled", command=lambda: filter_by_tag("tanszek"))
btntagtanszek.place(x=139, y=636, width=90, height=30)

style.configure("btntagneptun.TButton", background="#E4E2E2", foreground="#000")
btntagneptun = ttk.Button(master=framemain, text="Neptun (0)", style="btntagneptun.TButton",
                          state="disabled", command=lambda: filter_by_tag("neptun"))
btntagneptun.place(x=239, y=636, width=90, height=30)

style.configure("btntagmoodle.TButton", background="#E4E2E2", foreground="#000")
btntagmoodle = ttk.Button(master=framemain, text="Moodle (0)", style="btntagmoodle.TButton",
                          state="disabled", command=lambda: filter_by_tag("moodle"))
btntagmoodle.place(x=339, y=636, width=90, height=30)

style.configure("btntagmilton.TButton", background="#E4E2E2", foreground="#000")
btntagmilton = ttk.Button(master=framemain, text="Milt-On (0)", style="btntagmilton.TButton",
                          state="disabled", command=lambda: filter_by_tag("milt-on"))
btntagmilton.place(x=439, y=636, width=90, height=30)

style.configure("btntaghianyos.TButton", background="#E4E2E2", foreground="#000")
btntaghianyos = ttk.Button(master=framemain, text="Hiányos (0)", style="btntaghianyos.TButton",
                           state="disabled", command=lambda: filter_by_tag("hianyos"))
btntaghianyos.place(x=539, y=636, width=90, height=30)

style.configure("btntagegyeb.TButton", background="#E4E2E2", foreground="#000")
btntagegyeb = ttk.Button(master=framemain, text="Egyéb (0)", style="btntagegyeb.TButton",
                         state="disabled", command=lambda: filter_by_tag("egyeb"))
btntagegyeb.place(x=639, y=636, width=90, height=30)

style.configure("btnattachfilter.TButton", background="#E4E2E2", foreground="#000")
btnattachfilter = ttk.Button(master=framemain, text="Csatolmány (0)", style="btnattachfilter.TButton",
                             command=filter_by_attachment)
btnattachfilter.place(x=739, y=636, width=110, height=30)

style.configure("btnclearfilters.TButton", background="#E4E2E2", foreground="#000")
btnclearfilters = ttk.Button(master=framemain, text="Szűrők törlése", style="btnclearfilters.TButton",
                             command=clear_filters)

style.configure("pbaremails.Horizontal.TProgressbar",
                background="#90EE90",
                troughcolor="#E4E2E2")

pbaremails = ttk.Progressbar(master=frameactionbar,
                             style="pbaremails.Horizontal.TProgressbar",
                             value=0)
pbaremails.config(orient="horizontal", mode="determinate", length=150)

lbl_progress_percent = tk.Label(master=frameactionbar,
                                text="",
                                bg="#EDECEC",
                                fg="#333",
                                font=("Segoe UI", 9, "bold"),
                                anchor="w")

style.configure("treeemails.Treeview.Heading", background="#E0E0E0", foreground="#000000")
style.configure("treeemails.Treeview", background="#FFFFFF", foreground="#000", font=("", 12))
style.map("treeemails.Treeview", background=[("selected", "#0078D7")])

treeemails = ttk.Treeview(master=framemain, selectmode="extended", style="treeemails.Treeview")
treeemails.config(columns=("Sender", "Subject", "Tag", "Attach", "AI", "Date"), show='headings')
treeemails.bind("<Button-1>", uncheck_select_all_checkbox)
treeemails.bind("<<TreeviewSelect>>", on_tree_select)
treeemails.place(x=9, y=20, width=991, height=606)

treeemails.tag_configure('oddrow', background='#FFFFFF')
treeemails.tag_configure('evenrow', background='#F5F5F5')

attach_header = "📎"
try:
    attach_header.encode("utf-8")
except Exception:
    attach_header = "Att."

treeemails.heading("Sender", text="Feladó", command=lambda: sort_tree_by_column("Sender"))
treeemails.heading("Subject", text="Email", command=lambda: sort_tree_by_column("Subject"))
treeemails.heading("Tag", text="Cimke", command=lambda: sort_tree_by_column("Tag"))
treeemails.heading("Attach", text=attach_header, command=lambda: sort_tree_by_column("Attach"))
treeemails.heading("AI", text="✨", command=lambda: sort_tree_by_column("AI"))
treeemails.heading("Date", text="Dátum", command=lambda: sort_tree_by_column("Date"))

treeemails.column("Sender", anchor="w", width=180)
treeemails.column("Subject", anchor="w", width=420)
treeemails.column("Tag", anchor="w", width=100)
treeemails.column("Attach", anchor="center", width=40)
treeemails.column("AI", anchor="center", width=40)
treeemails.column("Date", anchor="center", width=170)

lbl_sender = tk.Label(framedetails, text="Feladó:", bg="#F5F5F5", fg="#333", font=("", 10, "bold"), anchor="w")
lbl_sender.place(x=10, y=10, width=60, height=25)

lbl_sender_value = tk.Label(framedetails, text="", bg="#F5F5F5", fg="#000", font=("", 10), anchor="w")
lbl_sender_value.place(x=75, y=10, width=410, height=25)

lbl_date_value = tk.Label(framedetails, text="", bg="#F5F5F5", fg="#666", font=("", 9, "italic"), anchor="e")
lbl_date_value.place(x=490, y=10, width=195, height=25)

lbl_subject = tk.Label(framedetails, text="Tárgy:", bg="#F5F5F5", fg="#333", font=("", 10, "bold"), anchor="w")
lbl_subject.place(x=10, y=40, width=50, height=25)

lbl_subject_value = tk.Label(framedetails, text="", bg="#F5F5F5", fg="#000", font=("", 10), anchor="w",
                              wraplength=620, justify="left")
lbl_subject_value.place(x=65, y=40, width=620, height=25)

tag_categories = ["Vezetőség", "Tanszék", "Neptun", "Moodle", "Milt-On", "Hiányos", "Egyéb"]
tag_var = tk.StringVar()
tag_dropdown = ttk.Combobox(
    framedetails,
    textvariable=tag_var,
    values=tag_categories,
    state="readonly",
    font=("", 9),
    width=20
)
tag_dropdown.place(x=555, y=40, width=130, height=22)


def on_tag_dropdown_change(event):
    selected_items = treeemails.selection()
    if not selected_items or len(selected_items) != 1:
        return

    item_id = selected_items[0]
    email_data = app_state.email_data_map.get(item_id)
    if not email_data:
        return

    display_tag = tag_var.get()
    if not display_tag:
        return

    tag_map_reverse = {
        'Vezetőség': 'vezetoseg',
        'Tanszék': 'tanszek',
        'Neptun': 'neptun',
        'Moodle': 'moodle',
        'Milt-On': 'milt-on',
        'Hiányos': 'hianyos',
        'Egyéb': 'egyeb',
    }
    new_tag = tag_map_reverse.get(display_tag, display_tag.lower())

    email_data["tag"] = new_tag

    current_values = list(treeemails.item(item_id, "values"))
    current_values[2] = new_tag
    treeemails.item(item_id, values=current_values)

    if email_controller:
        email_controller.update_tag_for_email(email_data, new_tag)

    update_tag_counts_from_storage(app_state.all_emails)


tag_dropdown.bind("<<ComboboxSelected>>", on_tag_dropdown_change)

lbl_ai_summary = tk.Label(framedetails, text="AI Összefoglaló:", bg="#F5F5F5", fg="#333",
                          font=("", 10, "bold"), anchor="w")
lbl_ai_summary.place(x=10, y=70, width=120, height=25)

style.configure("btnaisummary.TButton", background="#E4E2E2", foreground="#000", font=("", 10))
style.map("btnaisummary.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000")])

btnaisummary = ttk.Button(framedetails, text="✨ Generálás", style="btnaisummary.TButton",
                          command=generate_summary_for_selected_single)
btnaisummary.place(x=590, y=68, width=100, height=28)

txt_ai_summary = tk.Text(framedetails, wrap="word", bg="#FFFACD", fg="#000",
                         font=("", 10), relief="solid", borderwidth=1, state='disabled')
txt_ai_summary.place(x=10, y=100, width=680, height=80)

notebook = ttk.Notebook(framedetails)
notebook.place(x=10, y=190, width=680, height=480)

message_tab = tk.Frame(notebook, bg="#FFFFFF")
notebook.add(message_tab, text="Üzenet")

message_display = HTMLScrolledText(
    message_tab,
    html="<p style='color: #999;'>Válasszon ki egy emailt.</p>"
)
message_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

detail_widgets = {
    'sender_value': lbl_sender_value,
    'subject_value': lbl_subject_value,
    'date_value': lbl_date_value,
    'tag_dropdown': tag_dropdown,
    'tag_var': tag_var,
    'ai_summary': txt_ai_summary,
    'notebook': notebook,
    'message_tab': message_tab,
    'message_display': message_display
}

windowsortify.bind("<Key>", on_key_press)


def initialize_ui():
    if email_controller is None:
        raise RuntimeError(
            "\n\n"
            "=" * 70 + "\n"
            "ERROR: sortifyui.py cannot run standalone!\n"
            "=" * 70 + "\n\n"
            "sortifyui.py requires dependency injection from main.py\n\n"
            "Controllers not injected. Please run:\n\n"
            "    python main.py\n\n"
            "=" * 70 + "\n"
        )

    check_initial_login_state()
    load_offline_emails()

    if not get_ai_consent():
        windowsortify.after(500, lambda: show_ai_consent_dialog(windowsortify))
