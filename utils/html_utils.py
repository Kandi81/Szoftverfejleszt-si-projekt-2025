"""
HTML cleaning utilities for tkhtmlview compatibility
"""
import re


def clean_html_for_display(html_content: str) -> str:
    """Clean HTML content for tkhtmlview display
    
    Removes problematic elements that tkhtmlview can't handle:
    - <style> blocks
    - <script> blocks
    - Inline style attributes (limited CSS support in tkhtmlview)
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        str: Cleaned HTML safe for tkhtmlview
    """
    # Remove <style> blocks (including content)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, 
                          flags=re.DOTALL | re.IGNORECASE)
    
    # Remove <script> blocks (security + compatibility)
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, 
                          flags=re.DOTALL | re.IGNORECASE)
    
    # Remove ALL inline style attributes (tkhtmlview has limited CSS support)
    html_content = re.sub(r'\s+style="[^"]*"', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r"\s+style='[^']*'", '', html_content, flags=re.IGNORECASE)
    
    return html_content


def strip_html_tags(html_content: str) -> str:
    """Strip all HTML tags from content
    
    Args:
        html_content: HTML string
        
    Returns:
        str: Plain text without HTML tags
    """
    return re.sub(r'<[^>]+>', '', html_content)
