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
    }

    for e in emails:
        tag = (e.get('tag') or '').lower()
        if tag in counts:
            counts[tag] += 1

    app_state.categorized_counts = counts

    btntagvezetosegi.config(
        text=f"Vezetoseg ({counts['vezetoseg']})",
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
            'hianyos': 'Hiányos'
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
        attachments = attachment_names

    for i in range(min(3, len(attachments))):
        filename = attachments[i]
        is_safe, reason = verify_attachment_safety(email_id, filename)

        tab_frame = detail_widgets[f'attachment_tab_{i + 1}']
        notebook.add(tab_frame, text=f"📎 {i + 1}")

        for widget in tab_frame.winfo_children():
            widget.destroy()

        header_frame = tk.Frame(tab_frame, bg='white')
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        status_emoji = "✅" if is_safe else "⚠️"
        status_text = "Biztonságos" if is_safe else "GYANÚS"
        status_color = "#28a745" if is_safe else "#dc3545"

        status_label = tk.Label(header_frame, text=f"{status_emoji} {status_text}",
                                font=("Arial", 11, "bold"), fg=status_color, bg='white')
        status_label.pack(anchor='w')

        filename_label = tk.Label(header_frame, text=filename, font=("Arial", 10),
                                  bg='white', fg='#333', wraplength=380, justify='left')
        filename_label.pack(anchor='w', pady=(5, 0))

        if not is_safe and reason:
            reason_frame = tk.Frame(tab_frame, bg='#fff3cd', relief=tk.SOLID, borderwidth=1)
            reason_frame.pack(fill=tk.X, padx=10, pady=10)

            reason_label = tk.Label(reason_frame, text=f"⚠️  {reason}",
                                    font=("Arial", 9), bg='#fff3cd', fg='#856404',
                                    wraplength=380, justify='left')
            reason_label.pack(padx=10, pady=10)


def on_tree_select(_event=None):
    """Handle TreeView selection change"""
    selected_items = treeemails.selection()

    # Update categorize button state
    if selected_items and not app_state.is_filtered:
        btncategorize.config(state="normal")
    else:
        btncategorize.config(state="disabled")

    # ========== ADDED: Enable AI button for single selection ==========
    if len(selected_items) == 1:
        btnailabel.config(state="normal")
    else:
        btnailabel.config(state="disabled")
    # ====================================================================

    # Update details panel
    if len(selected_items) == 1:
        item_id = selected_items[0]
        email_data = app_state.email_data_map.get(item_id, {})
        update_details_panel(email_data)
    else:
        update_details_panel(None)


def on_tag_dropdown_change(event):
    """Handle tag dropdown change with auto-save"""
    if email_controller is None:
        return

    selected_items = treeemails.selection()
    if len(selected_items) != 1:
        return

    item_id = selected_items[0]
    email_data = app_state.email_data_map.get(item_id, {})
    if not email_data:
        return

    selected_display = detail_widgets['tag_var'].get()

    tag_reverse_map = {
        'Vezetőség': 'vezetoseg',
        'Tanszék': 'tanszek',
        'Neptun': 'neptun',
        'Moodle': 'moodle',
        'Milt-On': 'milt-on',
        'Hiányos': 'hianyos'
    }

    new_tag = tag_reverse_map.get(selected_display, '----')

    old_tag = email_data.get('tag', '----')
    if new_tag == old_tag:
        return

    email_data['tag'] = new_tag

    email_controller.update_tag_for_email(email_data)

    current_values = list(treeemails.item(item_id, "values"))
    current_values[2] = new_tag
    treeemails.item(item_id, values=current_values)

    update_tag_counts_from_storage(app_state.all_emails)

    print(f"[TAG] Auto-saved: {old_tag} → {new_tag}")


def toggle_select_all():
    if select_all_var.get():
        for item_id in app_state.all_tree_items:
            treeemails.selection_add(item_id)
    else:
        treeemails.selection_remove(treeemails.get_children())


def get_emails(_event):
    """Fetch new emails from Gmail (using email_controller)"""
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

    pbaremails.config(value=0)
    pbaremails.place(x=560, y=14, width=200, height=22)
    windowsortify.update()

    try:
        def update_progress(value):
            pbaremails.config(value=value)
            windowsortify.update()

        synced_emails = email_controller.fetch_new_emails(
            max_results=100,
            progress_callback=update_progress
        )

        if synced_emails:
            populate_tree_from_emails(synced_emails)
            update_tag_counts_from_storage(synced_emails)
            update_attachment_button_count(synced_emails)
            chkselectall.config(state="normal")

        pbaremails.config(value=100)
        windowsortify.update()

    except Exception as e:
        messagebox.showerror("Hiba", f"Email letöltési hiba: {e}")
    finally:
        pbaremails.place_forget()


def filter_by_tag(tag_name):
    """Filter treeview to show only items with the specified tag"""
    if email_controller is None:
        return

    visible_items = email_controller.filter_by_tag(
        tag_name,
        app_state.all_tree_items,
        treeemails
    )

    treeemails.selection_remove(treeemails.get_children())
    filter_status_label.config(text=f"Szűrő: {tag_name.capitalize()}")
    btncategorize.config(state="disabled")
    btnclearfilters.place(x=919, y=636, width=80, height=40)


def filter_by_attachment():
    """Filter emails with attachments"""
    if email_controller is None:
        return

    visible_items = email_controller.filter_by_attachment(
        app_state.all_tree_items,
        treeemails
    )

    treeemails.selection_remove(treeemails.get_children())
    filter_status_label.config(text="Szűrő: Csatolmány")
    btncategorize.config(state="disabled")
    btnclearfilters.place(x=919, y=636, width=80, height=40)


def clear_filters():
    """Clear all filters"""
    if email_controller is None:
        return

    email_controller.clear_filters(app_state.all_tree_items, treeemails)

    treeemails.selection_remove(treeemails.get_children())
    filter_status_label.config(text="")
    btncategorize.config(state="disabled")
    btnclearfilters.place_forget()


def ai_label_single_email():
    """AI-based labeling for single selected email - ADDED"""
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
        ai_controller.auto_label_email(email_data)

        current_values = list(treeemails.item(item_id, "values"))
        current_values[2] = email_data.get("tag", "----")
        treeemails.item(item_id, values=current_values)

        update_details_panel(email_data)

        # Save to CSV
        email_controller.update_tag_for_email(email_data)

        update_tag_counts_from_storage(app_state.all_emails)

        messagebox.showinfo("Siker",
                            f"AI címkézés kész!\n\n"
                            f"Új címke: {email_data.get('tag', '----')}")
    except Exception as e:
        messagebox.showerror("Hiba", f"AI címkézés sikertelen:\n{e}")


def categorize_emails():
    """Categorize selected emails using rule engine - KEPT from main"""
    if email_controller is None:
        messagebox.showerror("Hiba", "Email controller not initialized")
        return

    selected_items = treeemails.selection()
    if not selected_items:
        messagebox.showinfo("Info", "Válasszon ki legalább egy emailt a kategorizáláshoz.")
        return

    selected_emails = [app_state.email_data_map.get(item) for item in selected_items]
    selected_emails = [e for e in selected_emails if e]

    if not selected_emails:
        return

    result = messagebox.askyesno("Megerősítés",
                                 f"Kategorizálás futtatása {len(selected_emails)} kijelölt emailre?")
    if not result:
        return

    categorized = email_controller.categorize_selected_emails(selected_emails)

    for item_id in selected_items:
        email_data = app_state.email_data_map.get(item_id, {})
        if email_data:
            current_values = list(treeemails.item(item_id, "values"))
            current_values[2] = email_data.get("tag", "----")
            treeemails.item(item_id, values=current_values)

    update_tag_counts_from_storage(app_state.all_emails)

    messagebox.showinfo("Siker", f"Kategorizálás kész!\n\n{categorized} email frissítve.")


def generate_ai_summary():
    """Generate AI summary for selected email"""
    if ai_controller is None:
        messagebox.showerror("Hiba", "AI controller not initialized")
        return

    selected_items = treeemails.selection()
    if len(selected_items) != 1:
        messagebox.showinfo("Info", "Válasszon ki pontosan egy emailt az AI összefoglalóhoz.")
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
                                     "Újragenerálja?")
        if not result:
            return

    summary = ai_controller.generate_summary(email_data)

    if summary:
        current_values = list(treeemails.item(item_id, "values"))
        current_values[4] = AI_ICON
        treeemails.item(item_id, values=current_values)

        update_details_panel(email_data)

        messagebox.showinfo("Siker", "AI összefoglaló sikeresen generálva!")


def generate_batch_ai_summaries():
    """Generate AI summaries for all emails"""
    if ai_controller is None:
        messagebox.showerror("Hiba", "AI controller not initialized")
        return

    if not get_ai_consent():
        result = show_ai_consent_dialog(windowsortify)
        if not result:
            return

    def progress_callback(current, total):
        print(f"[AI BATCH] Processing {current}/{total}...")

    summaries = ai_controller.generate_batch_summaries(
        app_state.all_emails,
        progress_callback=progress_callback
    )

    if summaries:
        populate_tree_from_emails(app_state.all_emails)


def sort_treeview(col, reverse):
    """Sort TreeView by column"""
    if email_controller is None:
        return

    email_controller.sort_emails(col, reverse, app_state.all_emails)

    app_state.sort_column = col
    app_state.sort_reverse = reverse

    populate_tree_from_emails(app_state.all_emails)


def initialize_ui():
    """Initialize UI components and load data"""
    global windowsortify, treeemails, pbaremails, chkselectall
    global btncategorize, btnailabel, btnclearfilters, btnattachfilter
    global btntagvezetosegi, btntagtanszek, btntagneptun, btntagmoodle, btntagmilton, btntaghianyos
    global filter_status_label, test_mode_label, style

    windowsortify = tk.Tk()
    windowsortify.title("Sortify - Email Manager v0.6.0")
    windowsortify.geometry("1400x850")
    windowsortify.configure(bg="#f0f0f0")

    style = ttk.Style()
    style.theme_use('clam')

    framemaincontainer = tk.Frame(master=windowsortify, bg="#f0f0f0")
    framemaincontainer.place(x=10, y=10, width=1380, height=830)

    frameactionbar = tk.Frame(master=framemaincontainer, bg="#E4E2E2")
    frameactionbar.place(x=0, y=0, width=1380, height=60)

    style.configure("btnsync.TButton", background="#E4E2E2", foreground="#000")
    style.map("btnsync.TButton", background=[("active", "#E4E2E2")], foreground=[("active", "#000")])

    btnsync = ttk.Button(master=frameactionbar, text="Frissítés", style="btnsync.TButton")
    btnsync.place(x=10, y=9, width=110, height=40)
    btnsync.bind("<Button-1>", get_emails)

    style.configure("btncategorize.TButton", background="#E4E2E2", foreground="#000")
    style.map("btncategorize.TButton", background=[("active", "#E4E2E2")],
              foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

    btncategorize = ttk.Button(master=frameactionbar, text="Kategorizálás", style="btncategorize.TButton",
                               command=categorize_emails, state="disabled")
    btncategorize.place(x=160, y=9, width=110, height=40)

    # ========== ADDED: AI Címkézés button ==========
    style.configure("btnailabel.TButton", background="#E4E2E2", foreground="#000")
    style.map("btnailabel.TButton", background=[("active", "#E4E2E2")],
              foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

    btnailabel = ttk.Button(master=frameactionbar, text="✨ AI Címkézés", style="btnailabel.TButton",
                            command=lambda: ai_label_single_email(), state="disabled")
    btnailabel.place(x=280, y=9, width=120, height=40)
    # ================================================

    pbaremails = ttk.Progressbar(master=frameactionbar, mode='determinate', maximum=100)

    global select_all_var
    select_all_var = tk.BooleanVar(value=False)
    chkselectall = tk.Checkbutton(master=frameactionbar, text="Mind kijelölése",
                                  variable=select_all_var, command=toggle_select_all,
                                  bg="#E4E2E2", state="disabled")
    chkselectall.place(x=1230, y=18, width=140, height=25)

    test_mode_label = tk.Label(master=frameactionbar, text="", bg="#E4E2E2",
                               fg="#ff6600", font=("Arial", 9, "bold"))
    test_mode_label.place(x=800, y=20, width=400, height=20)

    frameemaillist = tk.Frame(master=framemaincontainer, bg="white")
    frameemaillist.place(x=0, y=60, width=1000, height=610)

    treeemails_scroll = ttk.Scrollbar(frameemaillist, orient="vertical")
    treeemails_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    columns = ("Feladó", "Tárgy", "Tag", "📎", "AI", "Dátum")
    treeemails = ttk.Treeview(frameemaillist, columns=columns, show="headings",
                              yscrollcommand=treeemails_scroll.set, selectmode="extended")
    treeemails_scroll.config(command=treeemails.yview)

    treeemails.heading("Feladó", text="Feladó", anchor=tk.W,
                       command=lambda: sort_treeview("Feladó", not app_state.sort_reverse))
    treeemails.heading("Tárgy", text="Tárgy", anchor=tk.W,
                       command=lambda: sort_treeview("Tárgy", not app_state.sort_reverse))
    treeemails.heading("Tag", text="Tag", anchor=tk.W,
                       command=lambda: sort_treeview("Tag", not app_state.sort_reverse))
    treeemails.heading("📎", text="📎", anchor=tk.CENTER)
    treeemails.heading("AI", text="AI", anchor=tk.CENTER)
    treeemails.heading("Dátum", text="Dátum", anchor=tk.W,
                       command=lambda: sort_treeview("Dátum", not app_state.sort_reverse))

    treeemails.column("Feladó", width=200, anchor=tk.W)
    treeemails.column("Tárgy", width=400, anchor=tk.W)
    treeemails.column("Tag", width=100, anchor=tk.W)
    treeemails.column("📎", width=40, anchor=tk.CENTER)
    treeemails.column("AI", width=40, anchor=tk.CENTER)
    treeemails.column("Dátum", width=140, anchor=tk.W)

    treeemails.tag_configure('evenrow', background='#f9f9f9')
    treeemails.tag_configure('oddrow', background='#ffffff')

    treeemails.pack(fill=tk.BOTH, expand=True)

    treeemails.bind("<<TreeviewSelect>>", on_tree_select)

    framefilters = tk.Frame(master=framemaincontainer, bg="#E4E2E2")
    framefilters.place(x=0, y=670, width=1000, height=160)

    filter_label = tk.Label(master=framefilters, text="Szűrők:", bg="#E4E2E2",
                            font=("Arial", 10, "bold"))
    filter_label.place(x=10, y=10, width=100, height=30)

    style.configure("btnfilter.TButton", background="#E4E2E2", foreground="#000")
    style.map("btnfilter.TButton", background=[("active", "#d0d0d0")],
              foreground=[("disabled", "#a0a0a0")])

    btntagvezetosegi = ttk.Button(master=framefilters, text="Vezetoseg (0)",
                                  style="btnfilter.TButton",
                                  command=lambda: filter_by_tag("vezetoseg"), state="disabled")
    btntagvezetosegi.place(x=10, y=50, width=150, height=40)

    btntagtanszek = ttk.Button(master=framefilters, text="Tanszék (0)",
                               style="btnfilter.TButton",
                               command=lambda: filter_by_tag("tanszek"), state="disabled")
    btntagtanszek.place(x=170, y=50, width=150, height=40)

    btntagneptun = ttk.Button(master=framefilters, text="Neptun (0)",
                              style="btnfilter.TButton",
                              command=lambda: filter_by_tag("neptun"), state="disabled")
    btntagneptun.place(x=330, y=50, width=150, height=40)

    btntagmoodle = ttk.Button(master=framefilters, text="Moodle (0)",
                              style="btnfilter.TButton",
                              command=lambda: filter_by_tag("moodle"), state="disabled")
    btntagmoodle.place(x=490, y=50, width=150, height=40)

    btntagmilton = ttk.Button(master=framefilters, text="Milt-On (0)",
                              style="btnfilter.TButton",
                              command=lambda: filter_by_tag("milt-on"), state="disabled")
    btntagmilton.place(x=650, y=50, width=150, height=40)

    btntaghianyos = ttk.Button(master=framefilters, text="Hiányos (0)",
                               style="btnfilter.TButton",
                               command=lambda: filter_by_tag("hianyos"), state="disabled")
    btntaghianyos.place(x=810, y=50, width=150, height=40)

    btnattachfilter = ttk.Button(master=framefilters, text="Csatolmány (0)",
                                 style="btnfilter.TButton",
                                 command=filter_by_attachment, state="disabled")
    btnattachfilter.place(x=10, y=100, width=150, height=40)

    filter_status_label = tk.Label(master=framefilters, text="", bg="#E4E2E2",
                                   fg="#0066cc", font=("Arial", 9, "bold"))
    filter_status_label.place(x=170, y=105, width=200, height=30)

    btnclearfilters = ttk.Button(master=framefilters, text="Törlés",
                                 style="btnfilter.TButton",
                                 command=clear_filters)

    framedetails = tk.Frame(master=framemaincontainer, bg="white", relief=tk.RIDGE, borderwidth=1)
    framedetails.place(x=1010, y=60, width=370, height=770)

    details_title = tk.Label(master=framedetails, text="Email Részletek", bg="white",
                             font=("Arial", 12, "bold"))
    details_title.pack(pady=10)

    info_frame = tk.Frame(framedetails, bg="white")
    info_frame.pack(fill=tk.X, padx=10, pady=5)

    tk.Label(info_frame, text="Feladó:", bg="white", font=("Arial", 9, "bold")).grid(
        row=0, column=0, sticky='w', pady=2)
    sender_value = tk.Label(info_frame, text="", bg="white", font=("Arial", 9), wraplength=280, justify='left')
    sender_value.grid(row=0, column=1, sticky='w', pady=2)

    tk.Label(info_frame, text="Tárgy:", bg="white", font=("Arial", 9, "bold")).grid(
        row=1, column=0, sticky='w', pady=2)
    subject_value = tk.Label(info_frame, text="", bg="white", font=("Arial", 9), wraplength=280, justify='left')
    subject_value.grid(row=1, column=1, sticky='w', pady=2)

    tk.Label(info_frame, text="", bg="white", font=("Arial", 9, "bold")).grid(
        row=2, column=0, sticky='w', pady=2)
    date_value = tk.Label(info_frame, text="", bg="white", font=("Arial", 9))
    date_value.grid(row=2, column=1, sticky='w', pady=2)

    tag_frame = tk.Frame(info_frame, bg="white")
    tag_frame.grid(row=3, column=0, columnspan=2, sticky='w', pady=5)

    tk.Label(tag_frame, text="Címke:", bg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))

    tag_var = tk.StringVar()
    tag_values = ["Vezetőség", "Tanszék", "Neptun", "Moodle", "Milt-On", "Hiányos"]
    tag_dropdown = ttk.Combobox(tag_frame, textvariable=tag_var, values=tag_values,
                                state="readonly", width=15)
    tag_dropdown.pack(side=tk.LEFT)
    tag_dropdown.bind("<<ComboboxSelected>>", on_tag_dropdown_change)

    ai_summary_frame = tk.Frame(framedetails, bg="#f8f9fa")
    ai_summary_frame.pack(fill=tk.BOTH, padx=10, pady=10, expand=False)

    ai_header = tk.Frame(ai_summary_frame, bg="#f8f9fa")
    ai_header.pack(fill=tk.X, pady=(5, 5))

    tk.Label(ai_header, text="✨ AI Összefoglaló", bg="#f8f9fa",
             font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

    btn_generate_ai = tk.Button(ai_header, text="✨", command=generate_ai_summary,
                                bg="#007bff", fg="white", font=("Arial", 10, "bold"),
                                relief=tk.FLAT, cursor="hand2", padx=8, pady=2)
    btn_generate_ai.pack(side=tk.RIGHT, padx=5)

    ai_summary_text = tk.Text(ai_summary_frame, height=4, wrap=tk.WORD,
                              font=("Arial", 9), bg="white", relief=tk.SOLID, borderwidth=1)
    ai_summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    ai_summary_text.config(state='disabled')

    notebook = ttk.Notebook(framedetails)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    message_tab = tk.Frame(notebook, bg='white')
    notebook.add(message_tab, text="Üzenet")

    message_display = HTMLScrolledText(message_tab, html="<p>Válasszon egy emailt</p>")
    message_display.pack(fill=tk.BOTH, expand=True)

    attachment_tabs = []
    for i in range(3):
        tab = tk.Frame(notebook, bg='white')
        attachment_tabs.append(tab)

    detail_widgets['sender_value'] = sender_value
    detail_widgets['subject_value'] = subject_value
    detail_widgets['date_value'] = date_value
    detail_widgets['tag_var'] = tag_var
    detail_widgets['ai_summary'] = ai_summary_text
    detail_widgets['notebook'] = notebook
    detail_widgets['message_tab'] = message_tab
    detail_widgets['message_display'] = message_display
    for i in range(3):
        detail_widgets[f'attachment_tab_{i + 1}'] = attachment_tabs[i]

    load_offline_emails()

    return windowsortify
