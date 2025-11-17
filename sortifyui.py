import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from googleapiclient.errors import HttpError
from email.utils import parseaddr
import gmailclient
from email_storage import EmailStorage
from rules import apply_rules
from attachment_verifier import verify_emails_batch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # noinspection PyProtectedMember
        base_path = sys._MEIPASS  # type: ignore
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Global variables
all_items = []
is_filtered = False
attachment_filter_active = False
current_filter_label = ""

categorized_counts = {
    "vezetoseg": 0,
    "tanszek": 0,
    "neptun": 0,
    "moodle": 0,
    "milt-on": 0,
    "hianyos": 0
}
categorized_items = set()
gmail_client = None
email_storage = EmailStorage()
email_data_map = {}

# Sorting state
sort_column = "Date"
sort_reverse = True


def populate_tree_from_emails(emails):
    global all_items, email_data_map
    treeemails.delete(*treeemails.get_children())
    all_items.clear()
    email_data_map.clear()

    emails.sort(key=lambda x: x.get("datetime", ""), reverse=True)

    for e in emails:
        values = (
            e.get("sender_name", ""),
            e.get("subject", "(no subject)"),
            e.get("tag", "----"),
            e.get("attachment_count", 0),
            e.get("datetime", "N/A"),
        )
        item_id = treeemails.insert("", tk.END, values=values)
        all_items.append(item_id)
        email_data_map[item_id] = e


def update_tag_counts_from_storage(emails):
    global categorized_counts
    for tag in categorized_counts:
        categorized_counts[tag] = 0
    for e in emails:
        t = e.get("tag", "----")
        if t in categorized_counts:
            categorized_counts[t] += 1

    btntagvezetosegi.config(text=f"Vezetoseg ({categorized_counts['vezetoseg']})",
                            state="normal" if categorized_counts['vezetoseg'] > 0 else "disabled")
    btntagtanszek.config(text=f"Tanszék ({categorized_counts['tanszek']})",
                         state="normal" if categorized_counts['tanszek'] > 0 else "disabled")
    btntagneptun.config(text=f"Neptun ({categorized_counts['neptun']})",
                        state="normal" if categorized_counts['neptun'] > 0 else "disabled")
    btntagmoodle.config(text=f"Moodle ({categorized_counts['moodle']})",
                        state="normal" if categorized_counts['moodle'] > 0 else "disabled")
    btntagmilton.config(text=f"Milt-On ({categorized_counts['milt-on']})",
                        state="normal" if categorized_counts['milt-on'] > 0 else "disabled")
    btntaghianyos.config(text=f"Hiányos ({categorized_counts['hianyos']})",
                         state="normal" if categorized_counts['hianyos'] > 0 else "disabled")


def update_attachment_button_count(emails):
    count = sum(1 for e in emails if int(e.get("attachment_count", 0)) > 0)
    btnattachfilter.config(text=f"Csatolmány ({count})")
    btnattachfilter.config(state="normal" if count > 0 else "disabled")


def load_offline_emails():
    emails = email_storage.load_emails()
    if not emails:
        treeemails.insert("", tk.END, values=("Feladó/Email/Tag/📎/Dátum megjelenik itt", "", "", "", ""))
        return

    apply_rules(emails)

    populate_tree_from_emails(emails)
    update_tag_counts_from_storage(emails)
    update_attachment_button_count(emails)


def get_emails(_event):
    global is_filtered, categorized_items, attachment_filter_active

    if gmail_client is None:
        messagebox.showwarning("Figyelmeztetés", "Kérjük, először jelentkezzen be!")
        return

    if email_storage.is_test_mode():
        messagebox.showinfo("Teszt mód",
                            "Teszt adatállomány (emails_mod.csv) van betöltve.\n"
                            "Frissítés le van tiltva, hogy ne írjuk felül a teszt adatokat.")
        return

    # Initialize progress bar at 0%
    pbaremails.config(value=0)
    pbaremails.place(x=560, y=14, width=200, height=22)
    windowsortify.update()

    try:
        # Step 1: Fetch message list (0-10% of progress)
        messages = gmail_client.list_inbox(query="", max_results=100)
        pbaremails.config(value=10)
        windowsortify.update()

        gmail_emails = []
        total = len(messages) if isinstance(messages, list) else 0

        if total == 0:
            pbaremails.config(value=100)
            windowsortify.update()
            messagebox.showinfo("Info", "Nincs új email a postaládában.")
            pbaremails.place_forget()
            return

        # Step 2: Fetch email details (10-90% of progress)
        detail_progress_range = 80

        for idx, msg in enumerate(messages, start=1):
            try:
                details = gmail_client.get_email_full_details(msg["id"])
                name, addr = parseaddr(details.get("sender", ""))
                domain = addr.split("@", 1)[-1] if "@" in addr else ""
                details["sender_name"] = name or addr
                details["sender_domain"] = domain
                details.setdefault("mime_types", [])
                details.setdefault("tag", "----")
                details.setdefault("needs_more_info", 0)
                details.setdefault("rule_applied", "")
                gmail_emails.append(details)
            except Exception as e:
                print(f"Hiba az üzenet feldolgozásakor: {e}")
                continue
            finally:
                progress = 10 + int((idx / total) * detail_progress_range)
                pbaremails.config(value=progress)
                windowsortify.update()

        # Step 3: Apply rules (90-95% of progress)
        pbaremails.config(value=90)
        windowsortify.update()

        apply_rules(gmail_emails)

        pbaremails.config(value=95)
        windowsortify.update()

        # Step 4: Sync with storage and display (95-100% of progress)
        synced_emails = email_storage.sync_emails(gmail_emails)

        is_filtered = False
        attachment_filter_active = False
        categorized_items.clear()

        populate_tree_from_emails(synced_emails)
        update_tag_counts_from_storage(synced_emails)
        update_attachment_button_count(synced_emails)

        if synced_emails:
            chkselectall.config(state="normal")

        pbaremails.config(value=100)
        windowsortify.update()

        messagebox.showinfo("Siker", f"{len(synced_emails)} email letöltve és szinkronizálva!")

    except HttpError as e:
        messagebox.showerror("Hiba", f"Gmail API hiba: {e}")
    except Exception as e:
        messagebox.showerror("Hiba", f"Email letöltési hiba: {e}")
    finally:
        pbaremails.place_forget()


def filter_by_tag(tag_name):
    """Filter treeview to show only items with the specified tag"""
    global is_filtered, current_filter_label
    for item_id in all_items:
        if treeemails.exists(item_id):
            try:
                treeemails.move(item_id, "", tk.END)
            except tk.TclError:
                pass
    for item_id in all_items:
        if treeemails.exists(item_id):
            item_values = treeemails.item(item_id, "values")
            if len(item_values) >= 3:
                item_tag = item_values[2]
                if item_tag != tag_name:
                    treeemails.detach(item_id)
    treeemails.selection_remove(treeemails.get_children())
    is_filtered = True
    current_filter_label = tag_name.capitalize()
    filter_status_label.config(text=f"Szűrő: {current_filter_label}")
    btncategorize.config(state="disabled")
    btnclearfilters.place(x=919, y=636, width=80, height=40)


def filter_by_attachment():
    global is_filtered, attachment_filter_active, current_filter_label
    for item_id in all_items:
        if treeemails.exists(item_id):
            e = email_data_map.get(item_id, {})
            if int(e.get("attachment_count", 0)) > 0:
                try:
                    treeemails.move(item_id, "", tk.END)
                except tk.TclError:
                    pass
            else:
                treeemails.detach(item_id)
    treeemails.selection_remove(treeemails.get_children())
    is_filtered = True
    attachment_filter_active = True
    current_filter_label = "Csatolmány"
    filter_status_label.config(text=f"Szűrő: {current_filter_label}")
    btncategorize.config(state="disabled")
    btnattachcheck.config(state="normal")
    btnclearfilters.place(x=919, y=636, width=80, height=40)


def clear_filters():
    global is_filtered, attachment_filter_active, current_filter_label
    for item_id in all_items:
        if treeemails.exists(item_id):
            try:
                treeemails.move(item_id, "", tk.END)
            except tk.TclError:
                pass
    treeemails.selection_remove(treeemails.get_children())
    is_filtered = False
    attachment_filter_active = False
    current_filter_label = ""
    filter_status_label.config(text="")
    btnattachcheck.config(state="disabled")
    btnclearfilters.place_forget()


def verify_attachments():
    """Verify attachments for filtered emails"""
    # Get all visible (filtered) emails
    filtered_emails = []
    for item_id in treeemails.get_children():
        if item_id in email_data_map:
            filtered_emails.append(email_data_map[item_id])

    if not filtered_emails:
        messagebox.showinfo("Info", "Nincs szűrt email csatolmánnyal.")
        return

    # Run verification
    results = verify_emails_batch(filtered_emails)

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
        msg = f"Ellenőrzött csatolmányok: {total}\nGyanús fájlok: {suspicious}\n\n"
        msg += "GYANÚS EMAILEK:\n" + "=" * 50 + "\n\n"

        for idx, email_data in enumerate(results['suspicious_emails'], start=1):
            msg += f"{idx}. {email_data['subject'][:50]}\n"
            msg += f"   Feladó: {email_data['sender_name']}\n"
            msg += f"   Dátum: {email_data['datetime']}\n"

            for att in email_data['suspicious_attachments']:
                msg += f"   ⚠️  {att['filename']}\n"
                msg += f"      {att['reason']}\n"
            msg += "\n"

        messagebox.showwarning("FIGYELEM - Gyanús csatolmányok", msg)


def sort_tree_by_column(col_name):
    """Sort TreeView by column, toggle ascending/descending"""
    global sort_column, sort_reverse

    if sort_column == col_name:
        sort_reverse = not sort_reverse
    else:
        sort_column = col_name
        sort_reverse = False

    items = []
    for item_id in treeemails.get_children():
        if item_id in email_data_map:
            e = email_data_map[item_id]
            items.append((item_id, e))

    if col_name == "Sender":
        items.sort(key=lambda x: x[1].get("sender_name", "").lower(), reverse=sort_reverse)
    elif col_name == "Subject":
        items.sort(key=lambda x: x[1].get("subject", "").lower(), reverse=sort_reverse)
    elif col_name == "Tag":
        items.sort(key=lambda x: x[1].get("tag", "").lower(), reverse=sort_reverse)
    elif col_name == "Attach":
        items.sort(key=lambda x: int(x[1].get("attachment_count", 0)), reverse=sort_reverse)
    elif col_name == "Date":
        items.sort(key=lambda x: x[1].get("datetime", ""), reverse=sort_reverse)

    for idx, (item_id, _) in enumerate(items):
        treeemails.move(item_id, "", idx)

    for col in ["Sender", "Subject", "Tag", "Attach", "Date"]:
        header_text = {
            "Sender": "Feladó",
            "Subject": "Email",
            "Tag": "Cimke",
            "Attach": attach_header,
            "Date": "Dátum"
        }[col]

        if col == col_name:
            arrow = " ▼" if sort_reverse else " ▲"
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


def check_selection(_event=None):
    selected_items = treeemails.selection()
    if selected_items and not is_filtered:
        btncategorize.config(state="normal")
    else:
        btncategorize.config(state="disabled")


def categorize_emails():
    messagebox.showinfo("Info", "Kategorizálás funkció később kerül finomításra.")


def update_get_emails_button_state():
    if gmail_client is not None and not email_storage.is_test_mode():
        btngetmails.config(state="normal")
    else:
        btngetmails.config(state="disabled")


def session_login():
    global gmail_client
    token_path = str(resource_path(os.path.join("resource", "token.json")))

    if btnsession.cget("text") == "Kijelentkezés":
        if os.path.exists(token_path):
            os.remove(token_path)
        gmail_client = None
        btnsession.config(text="Bejelentkezés")
        update_get_emails_button_state()
        messagebox.showinfo("Kijelentkezés", "Sikeres kijelentkezés")
    else:
        try:
            credentials_path = str(resource_path(os.path.join("resource", "credentials.json")))
            gmail_client = gmailclient.GmailClient(
                credentials_path=credentials_path,
                token_path=token_path
            )
            gmail_client.authenticate()
            btnsession.config(text="Kijelentkezés")
            update_get_emails_button_state()
            messagebox.showinfo("Bejelentkezés", "Sikeres bejelentkezés")
        except HttpError as e:
            messagebox.showerror("Hiba", f"Gmail API hiba: {e}")
            gmail_client = None
            update_get_emails_button_state()
        except Exception as e:
            messagebox.showerror("Hiba", f"Bejelentkezési hiba: {e}")
            gmail_client = None
            update_get_emails_button_state()


def check_initial_login_state():
    global gmail_client
    token_path = str(resource_path(os.path.join("resource", "token.json")))
    if os.path.exists(token_path):
        btnsession.config(text="Kijelentkezés")
        try:
            credentials_path = str(resource_path(os.path.join("resource", "credentials.json")))
            gmail_client = gmailclient.GmailClient(
                credentials_path=credentials_path,
                token_path=token_path
            )
            gmail_client.authenticate()
        except (HttpError, Exception):
            gmail_client = None
    else:
        btnsession.config(text="Bejelentkezés")
    update_get_emails_button_state()


def on_key_press(event):
    """Handle keyboard shortcuts"""
    # Ctrl+R: Refresh
    if event.state == 4 and event.keysym.lower() == 'r':
        if gmail_client and not email_storage.is_test_mode():
            get_emails(None)
    # Escape: Clear filters
    elif event.keysym == 'Escape':
        if is_filtered:
            clear_filters()


# Window and styles
windowsortify = tk.Tk()
windowsortify.title("Sortify v1.0")
windowsortify.config(bg="#E4E2E2")
windowsortify.geometry("1024x743")

style = ttk.Style(windowsortify)
style.theme_use("clam")

frameactionbar = tk.Frame(master=windowsortify)
frameactionbar.config(bg="#EDECEC")
frameactionbar.place(x=8, y=0, width=1010, height=55)

framemain = tk.Frame(master=windowsortify)
framemain.config(bg="#EDECEC")
framemain.place(x=5, y=59, width=1011, height=686)

test_mode_label = tk.Label(master=framemain,
                           text="",
                           bg="#EDECEC",
                           fg="#AA0000",
                           anchor="w")
test_mode_label.place(x=10, y=0, width=800, height=20)

# Buttons
style.configure("btngetmails.TButton", background="#E4E2E2", foreground="#000")
style.map("btngetmails.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btngetmails = ttk.Button(master=frameactionbar, text="Letoltes / Frissítés", style="btngetmails.TButton",
                         state="disabled")
btngetmails.bind("<Button-1>", get_emails)
btngetmails.place(x=10, y=9, width=140, height=40)

style.configure("btncategorize.TButton", background="#E4E2E2", foreground="#000")
style.map("btncategorize.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btncategorize = ttk.Button(master=frameactionbar, text="Kategorizálás", style="btncategorize.TButton",
                           command=categorize_emails, state="disabled")
btncategorize.place(x=160, y=9, width=110, height=40)

style.configure("btnattachcheck.TButton", background="#E4E2E2", foreground="#000")
style.map("btnattachcheck.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btnattachcheck = ttk.Button(master=frameactionbar, text="Csatolmányok ellenőrzése",
                            style="btnattachcheck.TButton",
                            command=verify_attachments,
                            state="disabled")
btnattachcheck.place(x=280, y=9, width=190, height=40)

style.configure("btnsession.TButton", background="#E4E2E2", foreground="#000")
style.map("btnsession.TButton", background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btnsession = ttk.Button(master=frameactionbar, text="Bejelentkezés", style="btnsession.TButton",
                        command=session_login)
btnsession.place(x=909, y=9, width=90, height=40)

# Tag buttons
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

# Tree styles and widget
style.configure("treeemails.Treeview.Heading", background="#E0E0E0", foreground="#000000")
style.configure("treeemails.Treeview", background="#E4E2E2", foreground="#000", font=("", 12))

treeemails = ttk.Treeview(master=framemain, selectmode="extended", style="treeemails.Treeview")
treeemails.config(columns=("Sender", "Subject", "Tag", "Attach", "Date"), show='headings')
treeemails.bind("<Button-1>", uncheck_select_all_checkbox)
treeemails.bind("<<TreeviewSelect>>", check_selection)
treeemails.place(x=9, y=20, width=991, height=606)

attach_header = "📎"
try:
    attach_header.encode("utf-8")
except Exception:
    attach_header = "Att."

treeemails.heading("Sender", text="Feladó", command=lambda: sort_tree_by_column("Sender"))
treeemails.heading("Subject", text="Email", command=lambda: sort_tree_by_column("Subject"))
treeemails.heading("Tag", text="Cimke", command=lambda: sort_tree_by_column("Tag"))
treeemails.heading("Attach", text=attach_header, command=lambda: sort_tree_by_column("Attach"))
treeemails.heading("Date", text="Dátum", command=lambda: sort_tree_by_column("Date"))

treeemails.column("Sender", anchor="w", width=180)
treeemails.column("Subject", anchor="w", width=420)
treeemails.column("Tag", anchor="w", width=100)
treeemails.column("Attach", anchor="center", width=70)
treeemails.column("Date", anchor="center", width=180)

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
filter_status_label.place(x=770, y=14, width=130, height=30)

# Keyboard shortcuts
windowsortify.bind("<Key>", on_key_press)

# Initial state
check_initial_login_state()

if email_storage.is_test_mode():
    test_mode_label.config(text="Teszt mód: emails_mod.csv van betöltve. A frissítés le van tiltva.")
    btngetmails.config(state="disabled")

load_offline_emails()

windowsortify.mainloop()
