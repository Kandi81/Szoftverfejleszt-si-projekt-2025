"""
Email data model
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Email:
    """Email data structure"""
    message_id: str
    sender: str
    sender_name: str
    sender_domain: str
    subject: str
    datetime: str
    snippet: str
    
    # Attachments
    attachment_count: int = 0
    attachment_names: str = ""
    mime_types: List[str] = field(default_factory=list)
    
    # Body
    body_plain: str = ""
    body_html: str = ""
    body_file: str = ""
    body_format: str = ""
    
    # Categorization
    tag: str = "----"
    needs_more_info: int = 0
    rule_applied: str = ""
    
    # AI
    ai_summary: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV storage"""
        return {
            'message_id': self.message_id,
            'sender': self.sender,
            'sender_name': self.sender_name,
            'sender_domain': self.sender_domain,
            'subject': self.subject,
            'datetime': self.datetime,
            'snippet': self.snippet,
            'attachment_count': self.attachment_count,
            'attachment_names': self.attachment_names,
            'mime_types': '|'.join(self.mime_types) if self.mime_types else '',
            'body_plain': self.body_plain,
            'body_html': self.body_html,
            'body_file': self.body_file,
            'body_format': self.body_format,
            'tag': self.tag,
            'needs_more_info': self.needs_more_info,
            'rule_applied': self.rule_applied,
            'ai_summary': self.ai_summary,
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Email':
        """Create Email from dictionary (CSV row)"""
        mime_types_str = data.get('mime_types', '')
        mime_types = mime_types_str.split('|') if mime_types_str else []
        
        return Email(
            message_id=data.get('message_id', ''),
            sender=data.get('sender', ''),
            sender_name=data.get('sender_name', ''),
            sender_domain=data.get('sender_domain', ''),
            subject=data.get('subject', ''),
            datetime=data.get('datetime', ''),
            snippet=data.get('snippet', ''),
            attachment_count=int(data.get('attachment_count', 0)),
            attachment_names=data.get('attachment_names', ''),
            mime_types=mime_types,
            body_plain=data.get('body_plain', ''),
            body_html=data.get('body_html', ''),
            body_file=data.get('body_file', ''),
            body_format=data.get('body_format', ''),
            tag=data.get('tag', '----'),
            needs_more_info=int(data.get('needs_more_info', 0)),
            rule_applied=data.get('rule_applied', ''),
            ai_summary=data.get('ai_summary', ''),
        )
    
    def has_attachments(self) -> bool:
        """Check if email has attachments"""
        return self.attachment_count > 0
    
    def has_ai_summary(self) -> bool:
        """Check if email has AI summary"""
        return bool(self.ai_summary and self.ai_summary.strip())
    
    def is_categorized(self) -> bool:
        """Check if email is categorized (has tag other than ----)"""
        return self.tag != "----"
