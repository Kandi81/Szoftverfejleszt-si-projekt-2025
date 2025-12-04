"""
AI Consent Dialog
Shows terms and conditions for AI feature usage
"""
import tkinter as tk
from tkinter import ttk
from utils.config_helper import set_ai_consent


class AIConsentDialog:
    """Dialog for AI feature consent"""

    def __init__(self, parent):
        self.result = False  # Track if user accepted

        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AI Funkció - Felhasználási Feltételek")
        self.dialog.geometry("600x550")
        self.dialog.resizable(False, False)  # Not resizable
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (550 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Configure grid weights
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)

        self._create_widgets()

        # Wait for dialog to close
        parent.wait_window(self.dialog)

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container frame
        container = tk.Frame(self.dialog, bg="#F5F5F5")
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Configure container grid
        container.grid_rowconfigure(2, weight=1)  # Text area expands
        container.grid_columnconfigure(0, weight=1)

        # Title
        title_label = tk.Label(
            container,
            text="🤖 AI Összefoglaló Funkció",
            font=("Segoe UI", 14, "bold"),
            bg="#F5F5F5",
            fg="#333"
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Subtitle
        subtitle_label = tk.Label(
            container,
            text="Kérjük, olvassa el az alábbi tájékoztatót",
            font=("Segoe UI", 9),
            bg="#F5F5F5",
            fg="#666"
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(0, 15))

        # Text frame with scrollbar
        text_frame = tk.Frame(container, bg="#FFFFFF", relief=tk.SOLID, borderwidth=1)
        text_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 15))

        # Configure text frame grid
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Text widget
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#333",
            padx=15,
            pady=15,
            yscrollcommand=scrollbar.set,
            state='normal'
        )
        text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=text_widget.yview)

        # Insert consent text (PLACEHOLDER - you will replace this)
        consent_text = """
AI ÖSSZEFOGLALÓ FUNKCIÓ - TÁJÉKOZTATÓ

Az AI összefoglaló funkció használatával Ön hozzájárul az alábbiakhoz:

1. ADATFELDOLGOZÁS
   • Az email tartalmát AI szolgáltatás (Perplexity AI vagy Google Gemini) dolgozza fel
   • Az adatok titkosított kapcsolaton keresztül kerülnek továbbításra
   • A feldolgozás kizárólag összefoglaló készítése céljából történik

2. ADATBIZTONSÁG
   • Az email tartalma NEM kerül hosszú távú tárolásra az AI szolgáltatónál
   • A generált összefoglalók csak az Ön gépén kerülnek tárolásra
   • Harmadik fél részére adatot nem adunk át

3. KORLÁTOZÁSOK
   • Az AI összefoglaló NEM helyettesíti az eredeti email elolvasását
   • Az összefoglaló pontossága nem garantált
   • Bizalmas vagy érzékeny adatok esetén óvatosan használja

4. HOZZÁJÁRULÁS VISSZAVONÁSA
   • A hozzájárulást bármikor visszavonhatja
   • Visszavonás után az AI funkció nem lesz elérhető

[PLACEHOLDER SZÖVEG - CSERÉLD KI A SAJÁT SZÖVEGEDRE]

Az AI funkció használatával Ön kijelenti, hogy:
• Elolvasta és megértette a fenti tájékoztatót
• Hozzájárul az email tartalmának AI általi feldolgozásához
• Tudomásul veszi a funkció korlátait és kockázatait
        """

        text_widget.insert('1.0', consent_text.strip())
        text_widget.config(state='disabled')

        # Buttons frame (bottom right corner)
        button_frame = tk.Frame(container, bg="#F5F5F5")
        button_frame.grid(row=3, column=0, sticky="e")

        # Use ttk style for clean buttons
        style = ttk.Style()
        style.configure("Consent.TButton", font=("Segoe UI", 10))

        # Decline button
        btn_decline = ttk.Button(
            button_frame,
            text="Elutasítom",
            style="Consent.TButton",
            command=self._on_decline
        )
        btn_decline.grid(row=0, column=0, padx=(0, 10))

        # Accept button
        btn_accept = ttk.Button(
            button_frame,
            text="Elfogadom",
            style="Consent.TButton",
            command=self._on_accept
        )
        btn_accept.grid(row=0, column=1)

    def _on_accept(self):
        """User accepted consent"""
        self.result = True
        set_ai_consent(True)
        print("[INFO] AI consent ACCEPTED")
        self.dialog.destroy()

    def _on_decline(self):
        """User declined consent"""
        self.result = False
        print("[INFO] AI consent DECLINED")
        self.dialog.destroy()

    def get_result(self) -> bool:
        """Get dialog result

        Returns:
            True if accepted, False if declined
        """
        return self.result


def show_ai_consent_dialog(parent) -> bool:
    """Show AI consent dialog and return result

    Args:
        parent: Parent window

    Returns:
        True if user accepted, False if declined
    """
    dialog = AIConsentDialog(parent)
    return dialog.get_result()
