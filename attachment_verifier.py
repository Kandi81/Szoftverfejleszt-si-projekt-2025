"""
Attachment verification: compare file extensions with MIME types
"""

from typing import List, Dict, Tuple

# Known safe MIME types for common extensions
EXTENSION_MIME_MAP = {
    '.pdf': ['application/pdf'],
    '.doc': ['application/msword'],
    '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    '.xls': ['application/vnd.ms-excel'],
    '.xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    '.ppt': ['application/vnd.ms-powerpoint'],
    '.pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
    '.txt': ['text/plain'],
    '.jpg': ['image/jpeg'],
    '.jpeg': ['image/jpeg'],
    '.png': ['image/png'],
    '.zip': ['application/zip', 'application/x-zip-compressed'],
}


def verify_attachment(filename: str, mime_type: str) -> Tuple[bool, str]:
    """
    Verify if the file extension matches the MIME type.
    Returns (is_safe, reason)
    """
    if not filename or not mime_type:
        return True, "Nincs csatolmány adat"

    # Extract extension
    ext = None
    if '.' in filename:
        ext = '.' + filename.rsplit('.', 1)[-1].lower()

    if not ext:
        return False, "Nincs fájlkiterjesztés"

    # Check if extension is known
    if ext not in EXTENSION_MIME_MAP:
        return True, f"Ismeretlen kiterjesztés: {ext}"

    expected_mimes = EXTENSION_MIME_MAP[ext]

    # Check if MIME matches
    if mime_type in expected_mimes:
        return True, "Rendben"

    # Mismatch detected
    return False, f"GYANÚS: {ext} fájl, de MIME type: {mime_type}"


def verify_email_attachments(email: Dict) -> List[Dict]:
    """
    Verify all attachments in an email.
    Returns list of verification results.
    """
    attachment_names = email.get('attachment_names', [])
    mime_types = email.get('mime_types', [])

    if not attachment_names:
        return []

    results = []
    for idx, filename in enumerate(attachment_names):
        mime_type = mime_types[idx] if idx < len(mime_types) else 'unknown'
        is_safe, reason = verify_attachment(filename, mime_type)

        results.append({
            'filename': filename,
            'mime_type': mime_type,
            'is_safe': is_safe,
            'reason': reason
        })

    return results


def verify_emails_batch(emails: List[Dict]) -> Dict:
    """
    Verify attachments for a batch of emails.
    Returns summary dict with suspicious items.
    """
    total_attachments = 0
    suspicious_count = 0
    suspicious_emails = []

    for email in emails:
        if email.get('attachment_count', 0) == 0:
            continue

        verification_results = verify_email_attachments(email)
        email_suspicious = []

        for result in verification_results:
            total_attachments += 1
            if not result['is_safe']:
                suspicious_count += 1
                email_suspicious.append(result)

        if email_suspicious:
            suspicious_emails.append({
                'subject': email.get('subject', '(no subject)'),
                'sender_name': email.get('sender_name', 'Unknown'),
                'datetime': email.get('datetime', 'N/A'),
                'suspicious_attachments': email_suspicious
            })

    return {
        'total_attachments': total_attachments,
        'suspicious_count': suspicious_count,
        'suspicious_emails': suspicious_emails
    }
