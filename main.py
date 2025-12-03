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
from services import StorageService, AIServiceFactory
from controllers import EmailController, AIController, AuthController
from models import app_state

# Import old UI temporarily (until we refactor it)
import sortifyui

def main():
    """Main entry point"""
    print("="*50)
    print("Sortify v0.4.0 - Modular Architecture")
    print("="*50)
    print()
    
    # Initialize services
    print("[INIT] Initializing services...")
    storage_service = StorageService()
    app_state.email_storage = storage_service
    
    # Initialize controllers
    print("[INIT] Initializing controllers...")
    auth_controller = AuthController(storage_service)
    email_controller = EmailController(storage_service)
    ai_controller = AIController(storage_service, ai_provider="perplexity")
    
    # Check auto-login
    print("[INIT] Checking authentication...")
    gmail_client = auth_controller.check_auto_login()
    
    if gmail_client:
        print("[AUTH] ✓ Auto-login successful")
        email_controller.gmail = gmail_client
    else:
        print("[AUTH] ⚠ Not authenticated")
    
    # Load offline emails
    print("[INIT] Loading offline emails...")
    emails = email_controller.load_offline_emails()
    print(f"[DATA] Loaded {len(emails)} emails")
    
    print()
    print("[INIT] Starting UI...")
    print("="*50)
    print()
    
    # Launch UI (using old sortifyui.py for now)
    # TODO: Replace with new modular UI
    sortifyui.windowsortify.mainloop()


if __name__ == "__main__":
    main()
