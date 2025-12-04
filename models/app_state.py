"""
Global application state management
"""
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field


@dataclass
class AppState:
    """Application state container"""
    
    # Email data
    all_emails: List[Dict] = field(default_factory=list)
    email_data_map: Dict[str, Dict] = field(default_factory=dict)  # tree_item_id -> email_dict
    all_tree_items: List[str] = field(default_factory=list)  # All treeview item IDs
    
    # Filter state
    is_filtered: bool = False
    attachment_filter_active: bool = False
    current_filter_label: str = ""
    
    # Categorization tracking
    categorized_items: Set[str] = field(default_factory=set)
    categorized_counts: Dict[str, int] = field(default_factory=lambda: {
        "vezetoseg": 0,
        "tanszek": 0,
        "neptun": 0,
        "moodle": 0,
        "milt-on": 0,
        "hianyos": 0
    })
    
    # Sorting state
    sort_column: str = "Date"
    sort_reverse: bool = True
    
    # Authentication state
    gmail_client: Optional[object] = None
    perplexity_client: Optional[object] = None
    
    # Services
    email_storage: Optional[object] = None
    gmail_service: Optional[object] = None
    
    def reset_filters(self):
        """Reset all filter states"""
        self.is_filtered = False
        self.attachment_filter_active = False
        self.current_filter_label = ""
    
    def update_categorized_counts(self):
        """Update categorized counts from all_emails"""
        for tag in self.categorized_counts:
            self.categorized_counts[tag] = 0
        
        for email in self.all_emails:
            tag = email.get("tag", "----")
            if tag in self.categorized_counts:
                self.categorized_counts[tag] += 1
    
    def get_attachment_count(self) -> int:
        """Get total number of emails with attachments"""
        return sum(1 for e in self.all_emails if int(e.get("attachment_count", 0)) > 0)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with Gmail"""
        return self.gmail_client is not None
    
    def is_test_mode(self) -> bool:
        """Check if running in test mode"""
        return self.email_storage and self.email_storage.is_test_mode()


# Global singleton instance
app_state = AppState()
