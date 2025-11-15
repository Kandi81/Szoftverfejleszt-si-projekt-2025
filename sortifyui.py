# This code is generated using PyUIbuilder: [https://pyuibuilder.com](https://pyuibuilder.com)

import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from googleapiclient.errors import HttpError
from email.utils import parsedate_to_datetime
from datetime import datetime
import gmailclient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Global variables - DEFINED ONLY ONCE
all_items = []
is_filtered = False
categorized_counts = {
    "vezetoseg": 0,
    "tanszek": 0,
    "neptun": 0,
    "moodle": 0,
    "milt-on": 0,
    "hianyos": 0
}
categorized_items = set()  # Track which items have been categorized
gmail_client = None  # Gmail client instance


def get_emails(_event):
    global all_items, is_filtered, categorized_counts, categorized_items, gmail_client

    # Check if logged in
    if gmail_client is None:
        messagebox.showwarning("Figyelmeztetés", "Kérjük, először jelentkezzen be!")
        return

    # Show progress bar
    pbaremails.place(x=869, y=656, width=120, height=20)
    windowsortify.update()  # Force UI update to show progress bar

    try:
        # Fetch emails from Gmail
        messages = gmail_client.list_inbox(query="", max_results=100)

        # Clear existing rows and reset counts
        treeemails.delete(*treeemails.get_children())
        all_items.clear()
        is_filtered = False
        categorized_items.clear()

        # Reset categorized counts
        for tag in categorized_counts:
            categorized_counts[tag] = 0

        # Reset button texts to show (0)
        btntagvezetosegi.config(text="Vezetoseg (0)", state="disabled")
        btntagtanszek.config(text="Tanszék (0)", state="disabled")
        btntagneptun.config(text="Neptun (0)", state="disabled")
        btntagmoodle.config(text="Moodle (0)", state="disabled")
        btntagmilton.config(text="Milt-On (0)", state="disabled")
        btntaghianyos.config(text="Hiányos (0)", state="disabled")

        # Configure columns
        treeemails.config(columns=("Subject", "Tag", "Date"), show='headings')

        # Set up column headings
        treeemails.heading("Subject", text="Email")
        treeemails.heading("Tag", text="Cimke")
        treeemails.heading("Date", text="Dátum")

        # Set up column properties
        treeemails.column("Subject", anchor="w", width=500)
        treeemails.column("Tag", anchor="w", width=100)
        treeemails.column("Date", anchor="center", width=231)

        # Fetch and insert emails
        email_data = []
        for msg in messages:
            try:
                msg_data = gmail_client.get_subject_and_date(msg["id"])
                subject = msg_data["subject"]
                date_str = msg_data["date"]

                # Parse and format date
                try:
                    dt = parsedate_to_datetime(date_str)
                    formatted_date = dt.strftime("%Y-%m-%d")
                    email_data.append((subject, "----", formatted_date, dt))
                except (ValueError, TypeError):
                    formatted_date = "N/A"
                    email_data.append((subject, "----", formatted_date, datetime.min))

            except HttpError as e:
                print(f"Error fetching message {msg['id']}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error fetching message {msg['id']}: {e}")
                continue

        # Sort by date descending (newest first)
        email_data.sort(key=lambda x: x[3], reverse=True)

        # Insert rows into treeview
        for subject, tag, formatted_date, _ in email_data:
            item_id = treeemails.insert("", tk.END, values=(subject, tag, formatted_date))
            all_items.append(item_id)

        # Enable the select all checkbox now that we have emails
        if email_data:
            chkselectall.config(state="normal")

    except HttpError as e:
        messagebox.showerror("Hiba", f"Gmail API hiba: {e}")
    except Exception as e:
        messagebox.showerror("Hiba", f"Email letöltési hiba: {e}")
    finally:
        # Hide progress bar after loading
        pbaremails.place_forget()


def categorize_emails():
    """Count tags and update button text and state for selected items only"""
    global categorized_counts, categorized_items

    # Show progress bar
    pbaremails.place(x=869, y=656, width=120, height=20)

    # Count occurrences of each tag in current selection
    current_counts = {
        "vezetoseg": 0,
        "tanszek": 0,
        "neptun": 0,
        "moodle": 0,
        "milt-on": 0,
        "hianyos": 0
    }

    # Get selected items only
    selected_items = treeemails.selection()

    # Iterate through only the selected items that haven't been categorized yet
    for item_id in selected_items:
        # Skip if this item has already been categorized
        if item_id in categorized_items:
            continue

        item_values = treeemails.item(item_id, "values")
        if len(item_values) >= 2:
            tag = item_values[1]  # Tag is at index 1
            if tag in current_counts:
                current_counts[tag] += 1
                # Mark this item as categorized
                categorized_items.add(item_id)

    # Increment the cumulative counts
    for tag in categorized_counts:
        categorized_counts[tag] += current_counts[tag]

    # Update button texts and states using cumulative counts
    # Vezetoseg button
    count = categorized_counts["vezetoseg"]
    btntagvezetosegi.config(text=f"Vezetoseg ({count})")
    btntagvezetosegi.config(state="normal" if count >= 1 else "disabled")

    # Tanszek button
    count = categorized_counts["tanszek"]
    btntagtanszek.config(text=f"Tanszék ({count})")
    btntagtanszek.config(state="normal" if count >= 1 else "disabled")

    # Neptun button
    count = categorized_counts["neptun"]
    btntagneptun.config(text=f"Neptun ({count})")
    btntagneptun.config(state="normal" if count >= 1 else "disabled")

    # Moodle button
    count = categorized_counts["moodle"]
    btntagmoodle.config(text=f"Moodle ({count})")
    btntagmoodle.config(state="normal" if count >= 1 else "disabled")

    # Milt-On button
    count = categorized_counts["milt-on"]
    btntagmilton.config(text=f"Milt-On ({count})")
    btntagmilton.config(state="normal" if count >= 1 else "disabled")

    # Hianyos button
    count = categorized_counts["hianyos"]
    btntaghianyos.config(text=f"Hiányos ({count})")
    btntaghianyos.config(state="normal" if count >= 1 else "disabled")

    # Uncheck the select all checkbox and clear selection
    select_all_var.set(False)
    treeemails.selection_remove(treeemails.get_children())

    # Hide progress bar after categorization
    pbaremails.place_forget()


def select_all():
    # Get the current state of the checkbox variable
    is_checked = select_all_var.get()

    if is_checked:
        # Select all items
        all_items_in_tree = treeemails.get_children()
        treeemails.selection_set(all_items_in_tree)
    else:
        # Deselect all items
        treeemails.selection_remove(treeemails.get_children())


def uncheck_select_all_checkbox(_event):
    # Set the variable to False (unchecked)
    select_all_var.set(False)


def check_selection(_event=None):
    """Enable or disable the categorize button based on tree selection and filter state"""
    selected_items = treeemails.selection()
    # Disable categorize button if filtered or no selection
    if selected_items and not is_filtered:
        btncategorize.config(state="normal")
    else:
        btncategorize.config(state="disabled")


def filter_by_tag(tag_name):
    """Filter treeview to show only items with the specified tag"""
    global is_filtered

    # First, reattach all items
    for item_id in all_items:
        if treeemails.exists(item_id):
            try:
                treeemails.move(item_id, "", tk.END)
            except tk.TclError:
                pass

    # Now detach items that don't match the filter
    for item_id in all_items:
        if treeemails.exists(item_id):
            item_values = treeemails.item(item_id, "values")
            if len(item_values) >= 2:
                item_tag = item_values[1]
                if item_tag != tag_name:
                    treeemails.detach(item_id)

    # Deselect all items
    treeemails.selection_remove(treeemails.get_children())

    # Mark as filtered and disable categorize button
    is_filtered = True
    btncategorize.config(state="disabled")

    # Show the clear filters button
    btnclearfilters.place(x=789, y=636, width=120, height=40)


def clear_filters():
    """Remove filtering and show all items"""
    global is_filtered

    # Reattach all items
    for item_id in all_items:
        if treeemails.exists(item_id):
            try:
                treeemails.move(item_id, "", tk.END)
            except tk.TclError:
                pass

    # Deselect all items
    treeemails.selection_remove(treeemails.get_children())

    # Mark as not filtered
    is_filtered = False

    # Hide the clear filters button
    btnclearfilters.place_forget()


def update_get_emails_button_state():
    """Enable or disable get emails button based on login state"""
    if gmail_client is not None:
        btngetmails.config(state="normal")
    else:
        btngetmails.config(state="disabled")


def session_login():
    """Handle login/logout for Gmail"""
    global gmail_client

    token_path = resource_path(os.path.join("resource", "token.json"))

    # Check current state
    if btnsession.cget("text") == "Kijelentkezés":
        # Logout: delete token file
        if os.path.exists(token_path):
            os.remove(token_path)
        gmail_client = None
        btnsession.config(text="Bejelentkezés")
        update_get_emails_button_state()
        messagebox.showinfo("Kijelentkezés", "Sikeres kijelentkezés")
    else:
        # Login
        try:
            credentials_path = resource_path(os.path.join("resource", "credentials.json"))
            gmail_client = gmailclient.GmailClient(
                credentials_path=credentials_path,
                token_path=token_path
            )
            gmail_client.authenticate()

            # Success
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
    """Check if user is already logged in at startup"""
    global gmail_client
    token_path = resource_path(os.path.join("resource", "token.json"))
    if os.path.exists(token_path):
        btnsession.config(text="Kijelentkezés")
        # Automatically authenticate
        try:
            credentials_path = resource_path(os.path.join("resource", "credentials.json"))
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


windowsortify = tk.Tk()
windowsortify.title("Sortify v1.0")
windowsortify.config(bg="#E4E2E2")
windowsortify.geometry("1024x743")

style = ttk.Style(windowsortify)
style.theme_use("clam")

frameactionbar = tk.Frame(master=windowsortify)
frameactionbar.config(bg="#EDECEC")
frameactionbar.place(x=8, y=0, width=1010, height=55)

style.configure("button.TButton", background="#E4E2E2", foreground="#000")
style.map("button.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

button = ttk.Button(master=frameactionbar, text="Button", style="button.TButton")
button.place(x=20, y=589, width=80, height=40)

style.configure("btngetmails.TButton", background="#E4E2E2", foreground="#000")
style.map("btngetmails.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btngetmails = ttk.Button(master=frameactionbar, text="Letoltes / Frissítés", style="btngetmails.TButton",
                         state="disabled")
btngetmails.bind("<Button-1>", get_emails)
btngetmails.place(x=10, y=9, width=140, height=40)

style.configure("btncategorize.TButton", background="#E4E2E2", foreground="#000")
style.map("btncategorize.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btncategorize = ttk.Button(master=frameactionbar, text="Kategorizálás", style="btncategorize.TButton",
                           command=categorize_emails, state="disabled")
btncategorize.place(x=160, y=9, width=110, height=40)

style.configure("chkselectall.TCheckbutton", background="#EDECEC", foreground="#000")
style.map("chkselectall.TCheckbutton",
          background=[("active", "#EDECEC")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

# Create a BooleanVar to track checkbox state
select_all_var = tk.BooleanVar(value=False)

chkselectall = ttk.Checkbutton(master=frameactionbar, text="Mind",
                               style="chkselectall.TCheckbutton",
                               variable=select_all_var,
                               command=select_all,
                               state="disabled")
chkselectall.place(x=280, y=14, width=70, height=30)

style.configure("btnsettings.TButton", background="#E4E2E2", foreground="#000")
style.map("btnsettings.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btnsettings = ttk.Button(master=frameactionbar, text="Beállítások", style="btnsettings.TButton")
btnsettings.place(x=799, y=9, width=100, height=40)

style.configure("btnsession.TButton", background="#E4E2E2", foreground="#000")
style.map("btnsession.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btnsession = ttk.Button(master=frameactionbar, text="Bejelentkezés", style="btnsession.TButton",
                        command=session_login)
btnsession.place(x=909, y=9, width=90, height=40)

framemain = tk.Frame(master=windowsortify)
framemain.config(bg="#EDECEC")
framemain.place(x=5, y=59, width=1011, height=686)

style.configure("btntagvezetosegi.TButton", background="#E4E2E2", foreground="#000")
style.map("btntagvezetosegi.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btntagvezetosegi = ttk.Button(master=framemain, text="Vezetoseg (0)", style="btntagvezetosegi.TButton",
                              state="disabled", command=lambda: filter_by_tag("vezetoseg"))
btntagvezetosegi.place(x=9, y=636, width=120, height=40)

style.configure("btntagneptun.TButton", background="#E4E2E2", foreground="#000")
style.map("btntagneptun.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btntagneptun = ttk.Button(master=framemain, text="Neptun (0)", style="btntagneptun.TButton",
                          state="disabled", command=lambda: filter_by_tag("neptun"))
btntagneptun.place(x=269, y=636, width=120, height=40)

style.configure("btntagmoodle.TButton", background="#E4E2E2", foreground="#000")
style.map("btntagmoodle.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btntagmoodle = ttk.Button(master=framemain, text="Moodle (0)", style="btntagmoodle.TButton",
                          state="disabled", command=lambda: filter_by_tag("moodle"))
btntagmoodle.place(x=399, y=636, width=120, height=40)

style.configure("btntagtanszek.TButton", background="#E4E2E2", foreground="#000")
style.map("btntagtanszek.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btntagtanszek = ttk.Button(master=framemain, text="Tanszék (0)", style="btntagtanszek.TButton",
                           state="disabled", command=lambda: filter_by_tag("tanszek"))
btntagtanszek.place(x=139, y=636, width=120, height=40)

style.configure("btntagmilton.TButton", background="#E4E2E2", foreground="#000")
style.map("btntagmilton.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btntagmilton = ttk.Button(master=framemain, text="Milt-On (0)", style="btntagmilton.TButton",
                          state="disabled", command=lambda: filter_by_tag("milt-on"))
btntagmilton.place(x=529, y=636, width=120, height=40)

style.configure("btntaghianyos.TButton", background="#E4E2E2", foreground="#000")
style.map("btntaghianyos.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btntaghianyos = ttk.Button(master=framemain, text="Hiányos (0)", style="btntaghianyos.TButton",
                           state="disabled", command=lambda: filter_by_tag("hianyos"))
btntaghianyos.place(x=659, y=636, width=120, height=40)

style.configure("btnclearfilters.TButton", background="#E4E2E2", foreground="#000")
style.map("btnclearfilters.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000"), ("disabled", "#a0a0a0")])

btnclearfilters = ttk.Button(master=framemain, text="Szurok Torlese", style="btnclearfilters.TButton",
                             command=clear_filters)
# Initially hidden - don't place it yet

style.configure("pbaremails.Horizontal.TProgressbar", background="#bab6ab", troughcolor="#dcdad6")

pbaremails = ttk.Progressbar(master=framemain, style="pbaremails.Horizontal.TProgressbar", value=50)
pbaremails.config(orient="horizontal", mode="determinate", length=100)
# Progress bar is initially hidden - don't place it yet

style.configure("treeemails.Treeview.Heading", background="#E0E0E0", foreground="#000000")

style.configure("treeemails.Treeview", background="#E4E2E2", foreground="#000", font=("", 12))

treeemails = ttk.Treeview(master=framemain, selectmode="extended", style="treeemails.Treeview")
treeemails.config(columns=("Subject", "Tag", "Date"), show='headings')
treeemails.bind("<Button-1>", uncheck_select_all_checkbox)
treeemails.bind("<<TreeviewSelect>>", check_selection)
treeemails.place(x=9, y=0, width=991, height=626)

# Set up column headings
treeemails.heading("Subject", text="Email")
treeemails.heading("Tag", text="Cimke")
treeemails.heading("Date", text="Dátum")

# Set up column properties
treeemails.column("Subject", anchor="w", width=700)
treeemails.column("Tag", anchor="w", width=100)
treeemails.column("Date", anchor="center", width=191)

# Add initial instruction message
treeemails.insert("", tk.END, values=("Az emailek letoltesehez kattintson a Letoltes/Frissites gombra", "", ""))

# Check login state at startup
check_initial_login_state()

windowsortify.mainloop()
