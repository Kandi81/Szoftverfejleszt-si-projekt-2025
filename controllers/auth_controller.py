"""
Authentication controller
Handles Gmail login/logout
"""
import os
from typing import Optional
from tkinter import messagebox
from googleapiclient.errors import HttpError

from models.app_state import app_state
from services import GmailService, StorageService
from utils import resource_path


class AuthController:
    """Controller for authentication operations"""
    
    def __init__(self, storage_service: StorageService):
        """Initialize auth controller
        
        Args:
            storage_service: Email storage service
        """
        self.storage = storage_service
        self.credentials_path = str(resource_path(os.path.join("resource", "credentials.json")))
        self.token_path = str(resource_path(os.path.join("resource", "token.json")))
    
    def login(self) -> Optional[GmailService]:
        """Perform Gmail login
        
        Returns:
            GmailService instance or None if failed
        """
        try:
            gmail_client = GmailService(
                credentials_path=self.credentials_path,
                token_path=self.token_path
            )
            gmail_client.authenticate()
            
            app_state.gmail_client = gmail_client
            
            messagebox.showinfo("Bejelentkezés", "Sikeres bejelentkezés")
            return gmail_client
        
        except HttpError as e:
            messagebox.showerror("Hiba", f"Gmail API hiba: {e}")
            app_state.gmail_client = None
            return None
        except Exception as e:
            messagebox.showerror("Hiba", f"Bejelentkezési hiba: {e}")
            app_state.gmail_client = None
            return None
    
    def logout(self):
        """Perform logout"""
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
        
        app_state.gmail_client = None
        
        messagebox.showinfo("Kijelentkezés", "Sikeres kijelentkezés")
    
    def check_auto_login(self) -> Optional[GmailService]:
        """Check if user is already logged in (token exists)
        
        Returns:
            GmailService instance or None if not logged in
        """
        if os.path.exists(self.token_path):
            try:
                gmail_client = GmailService(
                    credentials_path=self.credentials_path,
                    token_path=self.token_path
                )
                gmail_client.authenticate()
                
                app_state.gmail_client = gmail_client
                return gmail_client
            
            except (HttpError, Exception) as e:
                print(f"[ERROR] Auto-login failed: {e}")
                app_state.gmail_client = None
                return None
        
        return None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        return app_state.gmail_client is not None
    
    def can_refresh_emails(self) -> bool:
        """Check if email refresh is allowed
        
        Returns:
            True if refresh allowed, False otherwise
        """
        return self.is_authenticated() and not self.storage.is_test_mode()
