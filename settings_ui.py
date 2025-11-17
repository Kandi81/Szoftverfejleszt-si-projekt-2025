"""
Settings UI for Sortify
Allows users to edit rules and general settings via GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import configparser
import os
from typing import Dict


class SettingsWindow:
    def __init__(self, parent: tk.Tk) -> None:
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Beállítások - Sortify")
        self.window.geometry("800x600")
        self.window.config(bg="#E4E2E2")

        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()

        self.settings_path = "config/settings.ini"
        self.config = configparser.ConfigParser()

        # Load current settings
        self._load_settings()

        # Create UI
        self._create_ui()

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 400
        y = (self.window.winfo_screenheight() // 2) - 300
        self.window.geometry(f"800x600+{x}+{y}")

    def _load_settings(self) -> None:
        """Load settings from INI file"""
        if os.path.exists(self.settings_path):
            self.config.read(self.settings_path, encoding='utf-8')
        else:
            messagebox.showwarning("Figyelem",
                                   f"A {self.settings_path} fájl nem található.\n"
                                   "Alapértelmezett értékek kerülnek használatra.")

    def _create_ui(self) -> None:
        """Create the settings UI"""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.rules_tab = ttk.Frame(notebook)
        self.general_tab = ttk.Frame(notebook)

        notebook.add(self.rules_tab, text="Szabályok")
        notebook.add(self.general_tab, text="Általános")

        # Populate tabs
        self._create_rules_tab()
        self._create_general_tab()

        # Buttons at bottom
        button_frame = tk.Frame(self.window, bg="#E4E2E2")
        button_frame.pack(fill="x", padx=10, pady=10)

        btn_save = tk.Button(button_frame, text="Mentés", command=self._save_settings,
                            bg="#90EE90", fg="#000", font=("", 10, "bold"),
                            width=15, height=2)
        btn_save.pack(side="right", padx=5)

        btn_cancel = tk.Button(button_frame, text="Mégse", command=self.window.destroy,
                               bg="#E4E2E2", fg="#000", font=("", 10),
                               width=15, height=2)
        btn_cancel.pack(side="right", padx=5)

    def _create_rules_tab(self) -> None:
        """Create the rules editing tab"""
        # Instruction label
        instruction = tk.Label(self.rules_tab,
                              text="Szerkessze az email címeket kategóriánként. Vesszővel válassza el őket.",
                              bg="#EDECEC", fg="#333", font=("", 9))
        instruction.pack(fill="x", padx=10, pady=10)

        # Create scrollable frame
        canvas = tk.Canvas(self.rules_tab, bg="#EDECEC")
        scrollbar = ttk.Scrollbar(self.rules_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#EDECEC")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Rule categories
        self.rule_entries: Dict[str, tk.Text] = {}

        categories = [
            ("rules.leadership", "Vezetőség", "Más tanszékvezetők és felsővezetők email címei"),
            ("rules.department", "Tanszék", "Az Ön tanszékének tagjainak email címei"),
            ("rules.neptun", "Neptun", "Neptun rendszer email címei"),
            ("rules.moodle", "Moodle", "Moodle rendszer email címei"),
            ("rules.milton", "Milt-On", "Milt-On rendszer email címei"),
        ]

        for section, label, description in categories:
            self._create_rule_section(scrollable_frame, section, label, description)

    def _create_rule_section(self, parent: tk.Frame, section: str, label: str, description: str) -> None:
        """Create a section for editing a rule category"""
        frame = tk.LabelFrame(parent, text=label, bg="#EDECEC", fg="#000",
                             font=("", 10, "bold"), padx=10, pady=10)
        frame.pack(fill="x", padx=5, pady=10)

        # Description
        desc_label = tk.Label(frame, text=description, bg="#EDECEC", fg="#555",
                             font=("", 8), anchor="w")
        desc_label.pack(fill="x", pady=(0, 5))

        # Get current emails
        emails = ""
        if self.config.has_option(section, 'emails'):
            emails = self.config.get(section, 'emails')

        # Text widget for editing
        text_frame = tk.Frame(frame, bg="#EDECEC")
        text_frame.pack(fill="both", expand=True)

        text_widget = tk.Text(text_frame, height=4, wrap="word", font=("", 9))
        text_widget.insert("1.0", emails)
        text_widget.pack(side="left", fill="both", expand=True)

        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=text_scrollbar.set)

        # Store reference
        self.rule_entries[section] = text_widget

        # Add example button
        btn_add = tk.Button(frame, text="+ Email hozzáadása",
                           command=lambda s=section: self._add_email_prompt(s),
                           bg="#E4E2E2", fg="#000", font=("", 8))
        btn_add.pack(anchor="w", pady=(5, 0))

    def _add_email_prompt(self, section: str) -> None:
        """Prompt user to add an email address"""
        email = simpledialog.askstring("Email hozzáadása",
                                       "Adja meg az email címet:",
                                       parent=self.window)
        if email:
            email = email.strip().lower()
            # Validate email format (basic)
            if '@' not in email:
                messagebox.showerror("Hiba", "Érvénytelen email cím formátum.")
                return

            # Add to text widget
            text_widget = self.rule_entries[section]
            current = text_widget.get("1.0", tk.END).strip()
            if current:
                text_widget.insert(tk.END, f",{email}")
            else:
                text_widget.insert("1.0", email)

    def _create_general_tab(self) -> None:
        """Create the general settings tab"""
        frame = tk.Frame(self.general_tab, bg="#EDECEC")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # University domain
        tk.Label(frame, text="Egyetemi domain:", bg="#EDECEC", fg="#000",
                font=("", 10, "bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=10)

        self.uni_domain_var = tk.StringVar(value=self.config.get('general', 'uni_domain',
                                                                  fallback='uni-milton.hu'))
        tk.Entry(frame, textvariable=self.uni_domain_var, font=("", 10),
                width=40).grid(row=0, column=1, sticky="w", padx=10, pady=10)

        tk.Label(frame, text="A hallgatói emailek felismeréséhez használt domain",
                bg="#EDECEC", fg="#555", font=("", 8), anchor="w").grid(row=1, column=1,
                                                                        sticky="w", padx=10)

        # Department name
        tk.Label(frame, text="Tanszék neve:", bg="#EDECEC", fg="#000",
                font=("", 10, "bold"), anchor="w").grid(row=2, column=0, sticky="w", pady=10)

        self.dept_name_var = tk.StringVar(value=self.config.get('general', 'department_name',
                                                                fallback='Informatikai Tanszék'))
        tk.Entry(frame, textvariable=self.dept_name_var, font=("", 10),
                width=40).grid(row=2, column=1, sticky="w", padx=10, pady=10)

        tk.Label(frame, text="Az Ön tanszékének neve",
                bg="#EDECEC", fg="#555", font=("", 8), anchor="w").grid(row=3, column=1,
                                                                        sticky="w", padx=10)

        # Max emails to fetch
        tk.Label(frame, text="Max. letöltött emailek:", bg="#EDECEC", fg="#000",
                font=("", 10, "bold"), anchor="w").grid(row=4, column=0, sticky="w", pady=10)

        self.max_emails_var = tk.IntVar(value=self.config.getint('general', 'max_emails_fetch',
                                                                  fallback=100))
        tk.Spinbox(frame, from_=10, to=500, increment=10,
                  textvariable=self.max_emails_var, font=("", 10), width=10).grid(row=4, column=1,
                                                                                   sticky="w",
                                                                                   padx=10, pady=10)

        tk.Label(frame, text="Egyszerre letölthető emailek maximális száma",
                bg="#EDECEC", fg="#555", font=("", 8), anchor="w").grid(row=5, column=1,
                                                                        sticky="w", padx=10)

    def _save_settings(self) -> None:
        """Save settings to INI file"""
        try:
            # Update rules
            for section, text_widget in self.rule_entries.items():
                emails_text = text_widget.get("1.0", tk.END).strip()
                if not self.config.has_section(section):
                    self.config.add_section(section)
                self.config.set(section, 'emails', emails_text)

            # Update general settings
            if not self.config.has_section('general'):
                self.config.add_section('general')

            self.config.set('general', 'uni_domain', self.uni_domain_var.get().strip())
            self.config.set('general', 'department_name', self.dept_name_var.get().strip())
            self.config.set('general', 'max_emails_fetch', str(self.max_emails_var.get()))

            # Ensure config directory exists
            os.makedirs('config', exist_ok=True)

            # Write to file
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                self.config.write(f)

            messagebox.showinfo("Siker",
                               "A beállítások sikeresen mentésre kerültek!\n\n"
                               "Az új szabályok az alkalmazás újraindítása után lépnek érvénybe.")

            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba a beállítások mentése során:\n{e}")
