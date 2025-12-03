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

# NEW: Import from modular architecture
from models import app_state
from utils import resource_path, format_date_hungarian, clean_html_for_display

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== CONTROLLER INJECTION ====================
# These are injected by main.py
email_controller = None
ai_controller = None
auth_controller = None

# ==================== UI-SPECIFIC GLOBALS ====================
# UI-specific state (not in app_state)
detail_widgets = {}
select_all_var = None

# AI icon (for treeview)
AI_ICON = "✨"


# ==================== UTILITY FUNCTIONS ====================

def populate_tree_from_emails(emails):
    """Populate treeview with emails"""
    treeemails.delete(*treeemails.get_children())
    app_state.all_tree_items.clear()
    app_state.email_data_map.clear()

    emails.sort(key=lambda x: x.get("datetime", ""), reverse=True)

    for idx, e in enumerate(emails):
        # Format date
        formatted_date = format_date_hungarian(e.get("datetime", "N/A"))

        # AI indicator
        ai_indicator = AI_ICON if e.get('ai_summary') else ""

        values = (
            e.get("sender_name", ""),
            e.get("subject", "(no subject)"),
            e.get("tag", "----"),
            e.get("attachment_count", 0),
            ai_indicator,
            formatted_date,
        )

        # Add item with alternating row tags
        tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
        item_id = treeemails.insert("", tk.END, values=values, tags=(tag,))
        app_state.all_tree_items.append(item_id)
        app_state.email_data_map[item_id] = e


def update_tag_counts_from_storage(emails):
    """Update tag button counts"""
    app_state.update_categorized_counts()

    btntagvezetosegi.config(
        text=f"Vezetoseg ({app_state.categorized_counts['vezetoseg']})",
        state="normal" if app_state.categorized_counts['vezetoseg'] > 0 else "disabled"
    )
    btntagtanszek.config(
        text=f"Tanszék ({app_state.categorized_counts['tanszek']})",
        state="normal" if app_state.categorized_counts['tanszek'] > 0 else "disabled"
    )
    btntagneptun.config(
        text=f"Neptun ({app_state.categorized_counts['neptun']})",
        state="normal" if app_state.categorized_counts['neptun'] > 0 else "disabled"
    )
    btntagmoodle.config(
        text=f"Moodle ({app_state.categorized_counts['moodle']})",
        state="normal" if app_state.categorized_counts['moodle'] > 0 else "disabled"
    )
    btntagmilton.config(
        text=f"Milt-On ({app_state.categorized_counts['milt-on']})",
        state="normal" if app_state.categorized_counts['milt-on'] > 0 else "disabled"
    )
    btntaghianyos.config(
        text=f"Hiányos ({app_state.categorized_counts['hianyos']})",
        state="normal" if app_state.categorized_counts['hianyos'] > 0 else "disabled"
    )


def update_attachment_button_count(emails):
    """Update attachment button count"""
    count = app_state.get_attachment_count()
    btnattachfilter.config(text=f"Csatolmány ({count})")
    btnattachfilter.config(state="normal" if count > 0 else "disabled")


def load_offline_emails():
    """Load emails from storage (called on startup)"""
    if email_controller is None:
        print("[ERROR] email_controller not initialized")
        return

    try:
        emails = email_controller.load_offline_emails()

        if not emails:
            treeemails.insert("", tk.END, values=("Feladó/Email/Tag/📎/AI/Dátum megjelenik itt", "", "", "", "", ""))
            return

        populate_tree_from_emails(emails)
        update_tag_counts_from_storage(emails)
        update_attachment_button_count(emails)

        # Enable "Mind" checkbox if emails exist
        if emails:
            chkselectall.config(state="normal")

        # Show test mode warning if applicable
        if app_state.is_test_mode():
            test_mode_label.config(
                text="⚠ TESZT MÓD: emails_mod.csv betöltve - frissítés letiltva"
            )
    except Exception as e:
        print(f"[ERROR] Failed to load offline emails: {e}")
        messagebox.showerror("Hiba", f"Email betöltési hiba:\n{e}")


def update_details_panel(email_data):
    """Update the details panel with selected email data"""
    if not email_data:
        # Clear panel
        detail_widgets['sender_value'].config(text="")
        detail_widgets['subject_value'].config(text="")
        detail_widgets['date_value'].config(text="")
        detail_widgets['tag_value'].config(text="")
        detail_widgets['ai_summary'].config(state='normal')
        detail_widgets['ai_summary'].delete('1.0', tk.END)
        detail_widgets['ai_summary'].config(state='disabled')
        detail_widgets['body'].set_html(
            '<p style="color: #999;">Válasszon ki egy emailt a részletek megtekintéséhez.</p>')

        # Hide all attachment buttons
        for btn in detail_widgets['attachment_buttons']:
            btn.place_forget()
        detail_widgets['btnattachcheck'].place_forget()
        return

    # Update fields
    detail_widgets['sender_value'].config(text=email_data.get('sender_name', 'N/A'))
    detail_widgets['subject_value'].config(text=email_data.get('subject', '(no subject)'))
    detail_widgets['date_value'].config(text=email_data.get('datetime', 'N/A'))

    # Tag (only show if exists and not '----')
    tag = email_data.get('tag', '----')
    if tag and tag != '----':
        detail_widgets['tag_value'].config(text=tag)
    else:
        detail_widgets['tag_value'].config(text="")

    # AI Summary
    ai_summary = email_data.get('ai_summary', '')
    detail_widgets['ai_summary'].config(state='normal')
    detail_widgets['ai_summary'].delete('1.0', tk.END)
    if ai_summary:
        detail_widgets['ai_summary'].insert('1.0', ai_summary)
    else:
        detail_widgets['ai_summary'].insert('1.0', '[Még nincs AI összefoglaló - kattints a ✨ gombra a generáláshoz]')
    detail_widgets['ai_summary'].config(state='disabled')

    # Message body (HTML rendered with cleanup)
    body_html = email_data.get('body_html', '')
    body_plain = email_data.get('body_plain', '')

    try:
        if body_html:
            # Clean HTML before rendering
            cleaned_html = clean_html_for_display(body_html)
            detail_widgets['body'].set_html(cleaned_html)
        elif body_plain:
            # Fallback to plain text wrapped in <pre> tag
            escaped_plain = body_plain.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            detail_widgets['body'].set_html(
                f'<pre style="font-family: Arial; font-size: 12px; white-space: pre-wrap;">{escaped_plain}</pre>')
        else:
            detail_widgets['body'].set_html('<p style="color: #999;">Nincs üzenet törzs.</p>')
    except Exception as e:
        print(f"[ERROR] Failed to render HTML body: {e}")
        # Fallback to plain text if HTML rendering fails
        if body_plain:
            escaped_plain = body_plain.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            detail_widgets['body'].set_html(
                f'<pre style="font-family: Arial; font-size: 12px;">{escaped_plain[:1000]}</pre>')
        else:
            detail_widgets['body'].set_html('<p style="color: red;">Hiba az email megjelenítése során.</p>')

    # Attachments
    attachment_count = int(email_data.get('attachment_count', 0))
    attachment_names = email_data.get('attachment_names', '')

    # Parse attachment names
    attachments = []
    if attachment_names and isinstance(attachment_names, str):
        import re
        attachments = [a.strip() for a in re.split(r'[;|]', attachment_names) if a.strip()]
    elif isinstance(attachment_names, list):
        attachments = [str(a).strip() for a in attachment_names if str(a).strip()]

    # Hide all buttons first
    for btn in detail_widgets['attachment_buttons']:
        btn.place_forget()
    detail_widgets['btnattachcheck'].place_forget()

    # Show up to 3 attachment buttons
    max_chars = 30
    for idx, filename in enumerate(attachments[:3]):
        # Truncate filename if too long
        if len(filename) > max_chars:
            if '.' in filename:
                name_part = filename.rsplit('.', 1)[0]
                ext_part = '.' + filename.rsplit('.', 1)[1]
                available = max_chars - len(ext_part) - 3
                display_name = name_part[:available] + "..." + ext_part
            else:
                display_name = filename[:max_chars - 3] + "..."
        else:
            display_name = filename

        detail_widgets['attachment_buttons'][idx].config(text=f"📎 {display_name}")
        detail_widgets['attachment_buttons'][idx].place(x=10, y=580 + (idx * 35), width=450, height=30)

    # Show "Csatolmányok ellenőrzése" button if attachments exist
    if attachment_count > 0:
        detail_widgets['btnattachcheck'].place(x=470, y=580, width=210, height=30)


def on_tree_select(_event=None):
    """Handle TreeView selection change"""
    selected_items = treeemails.selection()

    # Update categorize button state
    if selected_items and not app_state.is_filtered:
        btncategorize.config(state="normal")
    else:
        btncategorize.config(state="disabled")

    # Update details panel
    if len(selected_items) == 1:
        item_id = selected_items[0]
        email_data = app_state.email_data_map.get(item_id, {})
        update_details_panel(email_data)
    else:
        # No selection or multiple selection
        update_details_panel(None)


def generate_summary_for_selected_single():
    """Generate AI summary for the currently selected single email"""
    if ai_controller is None:
        messagebox.showerror("Hiba", "AI controller not initialized")
        return

    selected_items = treeemails.selection()

    if len(selected_items) != 1:
        messagebox.showinfo("Info", "Válasszon ki pontosan egy emailt az AI összefoglaló generálásához.")
        return

    # Get selected email
    item_id = selected_items[0]
    email_data = app_state.email_data_map.get(item_id, {})

    if not email_data:
        return

    # Check if already has summary
    if email_data.get('ai_summary'):
        result = messagebox.askyesno("Megerősítés",
                                     "Ez az email már rendelkezik AI összefoglalóval.\n\n"
                                     "Újra generálod?")
        if not result:
            return

    # Show generating message in AI summary box
    detail_widgets['ai_summary'].config(state='normal')
    detail_widgets['ai_summary'].delete('1.0', tk.END)
    detail_widgets['ai_summary'].insert('1.0', '⏳ Összefoglaló generálása folyamatban...')
    detail_widgets['ai_summary'].config(state='disabled')
    windowsortify.update()

    # Generate summary using controller
    print(f"[AI] Generating summary for '{email_data.get('subject', '')}'...")
    summary = ai_controller.generate_summary(email_data)

    if not summary:
        summary = "[Hiba: nem sikerült összefoglalót generálni]"

    # Update details panel (without reloading tree)
    detail_widgets['ai_summary'].config(state='normal')
    detail_widgets['ai_summary'].delete('1.0', tk.END)
    detail_widgets['ai_summary'].insert('1.0', summary)
    detail_widgets['ai_summary'].config(state='disabled')

    # Update treeview item to show AI icon
    values = list(treeemails.item(item_id, 'values'))
    values[4] = AI_ICON  # AI column
    treeemails.item(item_id, values=values)

    print(f"[AI] Summary generated successfully")


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

    # Initialize progress bar at 0%
    pbaremails.config(value=0)
    pbaremails.place(x=560, y=14, width=200, height=22)
    windowsortify.update()

    try:
        # Progress callback
        def update_progress(value):
            pbaremails.config(value=value)
            windowsortify.update()

        # Fetch emails using controller
        synced_emails = email_controller.fetch_new_emails(
            max_results=100,
            progress_callback=update_progress
        )

        # Refresh UI
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


def verify_attachments():
    """Verify attachments for the currently selected email"""
    selected_items = treeemails.selection()

    if len(selected_items) != 1:
        messagebox.showinfo("Info", "Válasszon ki pontosan egy emailt a csatolmányok ellenőrzéséhez.")
        return

    item_id = selected_items[0]
    email_data = app_state.email_data_map.get(item_id, {})

    if int(email_data.get('attachment_count', 0)) == 0:
        messagebox.showinfo("Info", "Ennek az emailnek nincs csatolmánya.")
        return

    # Import verification service
    from services import verify_attachments as verify_service

    # Run verification on single email
    results = verify_service([email_data])

    # Display results
    total = results['total_attachments']
    suspicious = results['suspicious_count']

    if suspicious == 0:
        messagebox.showinfo("Ellenőrzés kész",
                            f"Ellenőrzött csatolmányok: {total}\n"
                            f"Gyanús fájlok: 0\n\n"
                            f"Minden csatolmány rendben van! ✓")
    else:
        # Build detailed message
        email_info = results['suspicious_emails'][0]
        msg = f"Ellenőrzött csatolmányok: {total}\nGyanús fájlok: {suspicious}\n\n"
        msg += "GYANÚS CSATOLMÁNYOK:\n" + "=" * 50 + "\n\n"

        for att in email_info['suspicious_attachments']:
            msg += f"⚠️  {att['filename']}\n"
            msg += f"   {att['reason']}\n\n"

        messagebox.showwarning("FIGYELEM - Gyanús csatolmányok", msg)


def categorize_emails():
    """Re-apply categorization rules to selected uncategorized emails"""
    if email_controller is None:
        messagebox.showerror("Hiba", "Email controller not initialized")
        return

    # Get selected items
    selected_items = treeemails.selection()

    if not selected_items:
        messagebox.showinfo("Info",
                            "Nincs kiválasztott email.\n\nVálasszon ki egy vagy több emailt a kategorizáláshoz.")
        return

    # Get selected email data
    selected_emails = [app_state.email_data_map[item] for item in selected_items if item in app_state.email_data_map]

    # Categorize using controller
    count = email_controller.categorize_selected_emails(selected_emails)

    # Refresh UI if any were categorized
    if count > 0:
        populate_tree_from_emails(app_state.all_emails)
        update_tag_counts_from_storage(app_state.all_emails)

    # Clear selection after categorization
    treeemails.selection_remove(treeemails.get_children())


def sort_tree_by_column(col_name):
    """Sort TreeView by column, toggle ascending/descending"""
    if email_controller is None:
        return

    # Toggle sort direction
    if app_state.sort_column == col_name:
        app_state.sort_reverse = not app_state.sort_reverse
    else:
        app_state.sort_column = col_name
        app_state.sort_reverse = False

    # Sort using controller
    sorted_items = email_controller.sort_emails(col_name, app_state.sort_reverse)

    # Reorder treeview
    for idx, (item_id, _) in enumerate(sorted_items):
        treeemails.move(item_id, "", idx)

    # Update column headers
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
    """Select/deselect all items in treeview"""
    is_checked = select_all_var.get()
    if is_checked:
        treeemails.selection_set(treeemails.get_children())
    else:
        treeemails.selection_remove(treeemails.get_children())


def uncheck_select_all_checkbox(_event):
    """Uncheck select-all checkbox when manual selection"""
    select_all_var.set(False)


def open_settings():
    """Open settings window"""
    from settings_ui import SettingsWindow
    SettingsWindow(windowsortify)


def update_get_emails_button_state():
    """Update get emails button state based on auth and test mode"""
    if auth_controller and auth_controller.can_refresh_emails():
        btngetmails.config(state="normal")
    else:
        btngetmails.config(state="disabled")


def session_login():
    """Gmail login/logout (using auth_controller)"""
    if auth_controller is None:
        messagebox.showerror("Hiba", "Auth controller not initialized")
        return

    if btnsession.cget("text") == "Kijelentkezés":
        # Logout
        auth_controller.logout()
        btnsession.config(text="Bejelentkezés")
        update_get_emails_button_state()
    else:
        # Login
        gmail_client = auth_controller.login()

        if gmail_client:
            # Update email_controller with authenticated client
            if email_controller:
                email_controller.gmail = gmail_client

            btnsession.config(text="Kijelentkezés")
            update_get_emails_button_state()


def check_initial_login_state():
    """Check if user is already logged in (called on startup)"""
    if auth_controller is None:
        btnsession.config(text="Bejelentkezés")
        update_get_emails_button_state()
        return

    gmail_client = auth_controller.check_auto_login()

    if gmail_client:
        # Update email_controller with authenticated client
        if email_controller:
            email_controller.gmail = gmail_client

        btnsession.config(text="Kijelentkezés")
    else:
        btnsession.config(text="Bejelentkezés")

    update_get_emails_button_state()


def on_key_press(event):
    """Handle keyboard shortcuts"""
    # Ctrl+R: Refresh
    if event.state == 4 and event.keysym.lower() == 'r':
        if auth_controller and auth_controller.can_refresh_emails():
            get_emails(None)
    # Escape: Clear filters
    elif event.keysym == 'Escape':
        if app_state.is_filtered:
            clear_filters()


# ==================== UI SETUP ====================

# Window and styles
windowsortify = tk.Tk()
windowsortify.title("Sortify v0.4.0")
windowsortify.config(bg="#E4E2E2")
windowsortify.geometry("1724x743")

style = ttk.Style(windowsortify)
style.theme_use("clam")

# Action bar - expanded width
frameactionbar = tk.Frame(master=windowsortify)
frameactionbar.config(bg="#EDECEC")
frameactionbar.place(x=8, y=0, width=1710, height=55)

# Main frame (left side - treeview)
framemain = tk.Frame(master=windowsortify)
framemain.config(bg="#EDECEC")
framemain.place(x=5, y=59, width=1011, height=686)

# Details frame (right side - email details)
framedetails = tk.Frame(master=windowsortify)
framedetails.config(bg="#F9F9F9")
framedetails.place(x=1020, y=59, width=700, height=686)

test_mode_label = tk.Label(master=framemain,
                           text="",
                           bg="#EDECEC",
                           fg="#AA0000",
                           anchor="w")
test_mode_label.place(x=10, y=0, width=800, height=20)

# Buttons (left side)
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

# Settings button - right aligned
style.configure("btnsettings.TButton", background="#E4E2E2", foreground="#000", font=("", 14))
style.map("btnsettings.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000")])

btnsettings = ttk.Button(master=frameactionbar, text="⚙", style="btnsettings.TButton",
                         command=open_settings)
btnsettings.place(x=1565, y=9, width=40, height=40)

# Login/Logout button - right aligned
style.configure("btnsession.TButton", background="#E4E2E2", foreground="#000")
style.map("btnsession.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btnsession = ttk.Button(master=frameactionbar, text="Bejelentkezés", style="btnsession.TButton",
                        command=session_login)
btnsession.place(x=1609, y=9, width=90, height=40)

# Tag buttons (bottom of left panel)
style.configure("btntagvezetosegi.TButton", background="#E4E2E2", foreground="#000")
btntagvezetosegi = ttk.Button(master=framemain, text="Vezetoseg (0)", style="btntagvezetosegi.TButton",
                              state="disabled", command=lambda: filter_by_tag("vezetoseg"))
btntagvezetosegi.place(x=9, y=636, width=120, height=40)

style.configure("btntagtanszek.TButton", background="#E4E2E2", foreground="#000")
btntagtanszek = ttk.Button(master=framemain, text="Tanszék (0)", style="btntagtanszek.TButton",
                           state="disabled", command=lambda: filter_by_tag("tanszek"))
btntagtanszek.place(x=139, y=636, width=120, height=40)

style.configure("btntagneptun.TButton", background="#E4E2E2", foreground="#000")
btntagneptun = ttk.Button(master=framemain, text="Neptun (0)", style="btntagneptun.TButton",
                          state="disabled", command=lambda: filter_by_tag("neptun"))
btntagneptun.place(x=269, y=636, width=120, height=40)

style.configure("btntagmoodle.TButton", background="#E4E2E2", foreground="#000")
btntagmoodle = ttk.Button(master=framemain, text="Moodle (0)", style="btntagmoodle.TButton",
                          state="disabled", command=lambda: filter_by_tag("moodle"))
btntagmoodle.place(x=399, y=636, width=120, height=40)

style.configure("btntagmilton.TButton", background="#E4E2E2", foreground="#000")
btntagmilton = ttk.Button(master=framemain, text="Milt-On (0)", style="btntagmilton.TButton",
                          state="disabled", command=lambda: filter_by_tag("milt-on"))
btntagmilton.place(x=529, y=636, width=120, height=40)

style.configure("btntaghianyos.TButton", background="#E4E2E2", foreground="#000")
btntaghianyos = ttk.Button(master=framemain, text="Hiányos (0)", style="btntaghianyos.TButton",
                           state="disabled", command=lambda: filter_by_tag("hianyos"))
btntaghianyos.place(x=659, y=636, width=120, height=40)

# Clear filters button
style.configure("btnclearfilters.TButton", background="#E4E2E2", foreground="#000")
btnclearfilters = ttk.Button(master=framemain, text="Szűrők törlése", style="btnclearfilters.TButton",
                             command=clear_filters)

# Attachment filter button
style.configure("btnattachfilter.TButton", background="#E4E2E2", foreground="#000")
btnattachfilter = ttk.Button(master=framemain, text="Csatolmány (0)", style="btnattachfilter.TButton",
                             command=filter_by_attachment)
btnattachfilter.place(x=789, y=636, width=120, height=40)

# Progress bar
style.configure("pbaremails.Horizontal.TProgressbar",
                background="#90EE90",
                troughcolor="#E4E2E2")

pbaremails = ttk.Progressbar(master=frameactionbar,
                             style="pbaremails.Horizontal.TProgressbar",
                             value=0)
pbaremails.config(orient="horizontal", mode="determinate", length=200)

# Tree styles and widget with banded rows
style.configure("treeemails.Treeview.Heading", background="#E0E0E0", foreground="#000000")
style.configure("treeemails.Treeview", background="#FFFFFF", foreground="#000", font=("", 12))
style.map("treeemails.Treeview", background=[("selected", "#0078D7")])

treeemails = ttk.Treeview(master=framemain, selectmode="extended", style="treeemails.Treeview")
treeemails.config(columns=("Sender", "Subject", "Tag", "Attach", "AI", "Date"), show='headings')
treeemails.bind("<Button-1>", uncheck_select_all_checkbox)
treeemails.bind("<<TreeviewSelect>>", on_tree_select)
treeemails.place(x=9, y=20, width=991, height=606)

# Configure alternating row colors (banded rows)
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

# Select-all checkbox
style.configure("chkselectall.TCheckbutton", background="#EDECEC", foreground="#000")
select_all_var = tk.BooleanVar(value=False)
chkselectall = ttk.Checkbutton(master=frameactionbar, text="Mind",
                               style="chkselectall.TCheckbutton",
                               variable=select_all_var,
                               command=select_all,
                               state="disabled")
chkselectall.place(x=480, y=14, width=70, height=30)

# Filter status label
filter_status_label = tk.Label(master=frameactionbar,
                               text="",
                               bg="#EDECEC",
                               fg="#555555",
                               font=("", 9, "italic"),
                               anchor="w")
filter_status_label.place(x=770, y=14, width=95, height=30)

# ==================== DETAILS PANEL ====================

# Sender (left side)
lbl_sender = tk.Label(framedetails, text="Feladó:", bg="#F9F9F9", fg="#333", font=("", 10, "bold"), anchor="w")
lbl_sender.place(x=10, y=10, width=60, height=25)

lbl_sender_value = tk.Label(framedetails, text="", bg="#F9F9F9", fg="#000", font=("", 10), anchor="w")
lbl_sender_value.place(x=75, y=10, width=420, height=25)

# Date (right side)
lbl_date = tk.Label(framedetails, text="Dátum:", bg="#F9F9F9", fg="#333", font=("", 10, "bold"), anchor="e")
lbl_date.place(x=500, y=10, width=60, height=25)

lbl_date_value = tk.Label(framedetails, text="", bg="#F9F9F9", fg="#000", font=("", 10), anchor="e")
lbl_date_value.place(x=565, y=10, width=125, height=25)

# Subject
lbl_subject = tk.Label(framedetails, text="Tárgy:", bg="#F9F9F9", fg="#333", font=("", 10, "bold"), anchor="w")
lbl_subject.place(x=10, y=40, width=50, height=25)

lbl_subject_value = tk.Label(framedetails, text="", bg="#F9F9F9", fg="#000", font=("", 10), anchor="w",
                              wraplength=620, justify="left")
lbl_subject_value.place(x=65, y=40, width=625, height=25)

# Tag (left side)
lbl_tag = tk.Label(framedetails, text="Címke:", bg="#F9F9F9", fg="#333", font=("", 10, "bold"), anchor="w")
lbl_tag.place(x=10, y=70, width=50, height=25)

lbl_tag_value = tk.Label(framedetails, text="", bg="#F9F9F9", fg="#000", font=("", 10), anchor="w")
lbl_tag_value.place(x=65, y=70, width=200, height=25)

# AI Summary section
lbl_ai_summary = tk.Label(framedetails, text="AI Összefoglaló:", bg="#F9F9F9", fg="#333",
                          font=("", 10, "bold"), anchor="w")
lbl_ai_summary.place(x=10, y=100, width=120, height=25)

# AI Summary generate button
style.configure("btnaisummary.TButton", background="#E4E2E2", foreground="#000", font=("", 10))
style.map("btnaisummary.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000")])

btnaisummary = ttk.Button(framedetails, text="✨ Generálás", style="btnaisummary.TButton",
                          command=generate_summary_for_selected_single)
btnaisummary.place(x=590, y=98, width=100, height=28)

# AI Summary text box (read-only)
txt_ai_summary = tk.Text(framedetails, wrap="word", bg="#FFFACD", fg="#000",
                         font=("", 10), relief="solid", borderwidth=1, state='disabled')
txt_ai_summary.place(x=10, y=130, width=680, height=80)

# Message body section
lbl_body = tk.Label(framedetails, text="Üzenet:", bg="#F9F9F9", fg="#333",
                    font=("", 10, "bold"), anchor="w")
lbl_body.place(x=10, y=220, width=80, height=25)

# HTML body viewer
html_body = HTMLScrolledText(framedetails, html="<p>Válasszon ki egy emailt.</p>")
html_body.place(x=10, y=250, width=680, height=320)

# Attachment buttons (3 buttons for first 3 attachments)
style.configure("btnattachment.TButton", background="#E4E2E2", foreground="#000", font=("", 9))
style.map("btnattachment.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000")])

btnattachment1 = ttk.Button(framedetails, text="📎 attachment1.pdf", style="btnattachment.TButton")
btnattachment2 = ttk.Button(framedetails, text="📎 attachment2.docx", style="btnattachment.TButton")
btnattachment3 = ttk.Button(framedetails, text="📎 attachment3.xlsx", style="btnattachment.TButton")

# Verify attachments button
style.configure("btnattachcheck.TButton", background="#FFD700", foreground="#000", font=("", 9, "bold"))
style.map("btnattachcheck.TButton", background=[("active", "#FFC700")],
          foreground=[("active", "#000")])

btnattachcheck = ttk.Button(framedetails, text="🔍 Csatolmányok ellenőrzése",
                            style="btnattachcheck.TButton",
                            command=verify_attachments)

# Store detail widgets in dictionary for easy access
detail_widgets = {
    'sender_value': lbl_sender_value,
    'subject_value': lbl_subject_value,
    'date_value': lbl_date_value,
    'tag_value': lbl_tag_value,
    'ai_summary': txt_ai_summary,
    'body': html_body,
    'attachment_buttons': [btnattachment1, btnattachment2, btnattachment3],
    'btnattachcheck': btnattachcheck
}

# ==================== INITIALIZATION ====================

# Keyboard shortcuts
windowsortify.bind("<Key>", on_key_press)


# ==================== MODULE-LEVEL INITIALIZATION ====================
# This is called by main.py after controller injection

def initialize_ui():
    """Initialize UI after controllers are injected by main.py

    This function is called by main.py after:
    1. Services are initialized
    2. Controllers are created
    3. Controllers are injected into this module (sortifyui.email_controller = ...)

    It performs:
    1. Check initial login state (token.json detection)
    2. Load offline emails from storage (CSV or test data)
    3. Update UI state accordingly (buttons, treeview, etc.)

    Raises:
        RuntimeError: If controllers not injected (sortifyui run directly)
    """
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

    # Check login state and update UI
    check_initial_login_state()

    # Load offline emails
    load_offline_emails()
