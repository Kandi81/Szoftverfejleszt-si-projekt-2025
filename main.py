"""
Sortify - Email Management Tool
Main entry point using modular architecture
"""
import sys
import os

# Fix tkhtmlview compatibility
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# Initialize services
from services import StorageService, GmailService, AIServiceFactory  # ← ADDED GmailService
from controllers import EmailController, AIController, AuthController
from models import app_state


def main():
    """Main entry point"""
    print("=" * 50)
    print("Sortify v1.0.0 - AI + Gmail Integration")  # ← Updated version
    print("=" * 50)
    print()

    # Initialize services
    print("[INIT] Initializing services...")
    storage_service = StorageService()
    app_state.email_storage = storage_service

    # ========== ADDED: GmailService initialization ==========
    gmail_service = GmailService()
    app_state.gmail_service = gmail_service
    # =========================================================

    # Initialize controllers
    print("[INIT] Initializing controllers...")
    auth_controller = AuthController(storage_service)
    email_controller = EmailController(storage_service, gmail_service)  # ← MODIFIED: pass gmail_service
    ai_controller = AIController(storage_service, ai_provider="perplexity")

    # Check auto-login
    print("[INIT] Checking authentication...")
    gmail_client = auth_controller.check_auto_login()

    if gmail_client:
        print("[AUTH] ✓ Auto-login successful")
        email_controller.gmail = gmail_client
        gmail_service.service = gmail_client.service  # ← ADDED: connect service
    else:
        print("[AUTH] ⚠ Not authenticated")

    print()
    print("[INIT] Starting UI...")
    print("=" * 50)
    print()

    # Import UI and inject controllers
    import sortifyui

    # Inject controllers into UI module
    sortifyui.email_controller = email_controller
    sortifyui.ai_controller = ai_controller
    sortifyui.auth_controller = auth_controller

    # Initialize UI with controllers
    sortifyui.initialize_ui()

    # Launch UI
    sortifyui.windowsortify.mainloop()


if __name__ == "__main__":
    main()
