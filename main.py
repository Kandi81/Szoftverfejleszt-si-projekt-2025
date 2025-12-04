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
from services import StorageService, AIServiceFactory, GmailService
from controllers import EmailController, AIController, AuthController
from models import app_state

def main():
    """Main entry point"""
    print("="*50)
    print("Sortify v0.4.0 - Modular Architecture")
    print("="*50)
    print()

    # Initialize services
    print("[INIT] Initializing services...")
    storage_service = StorageService()
    gmail_service = GmailService(storage_service)
    app_state.email_storage = storage_service
    app_state.gmail_service = gmail_service

    # Initialize controllers
    print("[INIT] Initializing controllers...")
    auth_controller = AuthController(storage_service)
    email_controller = EmailController(storage_service)
    ai_controller = AIController(storage_service, ai_provider="perplexity")

    # Check auto-login
    print("[INIT] Checking authentication...")
    gmail_client = auth_controller.check_auto_login()
    gmail_service.service = gmail_client.service

    if gmail_client:
        print("[AUTH] ✓ Auto-login successful")
        email_controller.gmail = gmail_client
    else:
        print("[AUTH] ⚠ Not authenticated")

    print()
    print("[INIT] Starting UI...")
    print("="*50)
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
