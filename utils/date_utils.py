"""
Date formatting utilities
"""
from datetime import datetime


def format_date_hungarian(date_str: str) -> str:
    """Format date to Hungarian format with smart today/time display
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        str: Formatted date string (HH:MM if today, YYYY.MM.DD HH:MM otherwise)
    """
    if not date_str or date_str == "N/A":
        return "N/A"
    
    try:
        # Try parsing RFC 2822 format (from Gmail API)
        formats = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%d %b %Y %H:%M:%S %Z",
            "%d %b %Y %H:%M:%S %z",
            "%Y.%m.%d %H:%M:%S",
            "%Y.%m.%d %H:%M",
        ]
        
        dt = None
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not dt:
            # Already in Hungarian format?
            if date_str.count('.') == 2 and ':' in date_str:
                return date_str
            return date_str
        
        # Check if today
        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        else:
            return dt.strftime("%Y.%m.%d %H:%M")
    
    except Exception as e:
        print(f"[DATE] Error formatting date '{date_str}': {e}")
        return date_str
