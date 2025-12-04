import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from datetime import datetime

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic"
]


class GmailService:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service = None
        self._label_cache = None

    def authenticate(self):
        """Authenticate with Gmail API"""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('gmail', 'v1', credentials=self.creds)

    def list_inbox(self, query='', max_results=100):
        """List emails from inbox"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            messages = results.get('messages', [])
            return messages
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def _parse_date_hungarian(self, date_str):
        """Parse email date and return in Hungarian format: YYYY.MM.DD HH:MM"""
        if not date_str:
            return "N/A"

        try:
            # Gmail API returns dates in RFC 2822 format or Unix timestamp
            # Example: "Mon, 15 Nov 2021 10:30:00 +0100"

            # Try parsing common formats
            formats = [
                "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
                "%d %b %Y %H:%M:%S %z",
                "%Y-%m-%d %H:%M:%S",
            ]

            dt = None
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

            if dt:
                return dt.strftime("%Y.%m.%d %H:%M")

            return date_str  # Return original if parsing fails
        except Exception as e:
            print(f"Date parsing error: {e}")
            return date_str

    def _extract_body_from_part(self, part):
        """Recursively extract body from message part"""
        body_data = {'plain': '', 'html': ''}

        mime_type = part.get('mimeType', '')

        if mime_type == 'text/plain':
            if 'data' in part.get('body', {}):
                body_data['plain'] = base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode('utf-8', errors='ignore')

        elif mime_type == 'text/html':
            if 'data' in part.get('body', {}):
                body_data['html'] = base64.urlsafe_b64decode(
                    part['body']['data']
                ).decode('utf-8', errors='ignore')

        elif mime_type.startswith('multipart/'):
            # Recursively process multipart
            for subpart in part.get('parts', []):
                sub_body = self._extract_body_from_part(subpart)
                if sub_body['plain']:
                    body_data['plain'] += sub_body['plain']
                if sub_body['html']:
                    body_data['html'] += sub_body['html']

        return body_data

    def get_email_body(self, message_id):
        """Extract email body (both plain and HTML if available)

        Returns:
            dict: {'plain': str, 'html': str}
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            payload = message.get('payload', {})
            body_data = {'plain': '', 'html': ''}

            # Check if message has parts (multipart)
            if 'parts' in payload:
                body_data = self._extract_body_from_part(payload)
            else:
                # Single part message
                body_data = self._extract_body_from_part(payload)

            return body_data

        except HttpError as error:
            print(f'Error fetching body for {message_id}: {error}')
            return {'plain': '', 'html': ''}

    def _extract_mime_types_recursive(self, part, mime_types):
        """Recursively extract MIME types from all parts"""
        mime_type = part.get('mimeType')
        if mime_type:
            mime_types.append(mime_type)

        # Recurse into subparts
        if 'parts' in part:
            for subpart in part['parts']:
                self._extract_mime_types_recursive(subpart, mime_types)

    def get_email_full_details(self, message_id):
        """Get full email details including attachments and body"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(no subject)')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Parse date
            formatted_date = self._parse_date_hungarian(date_str)

            # Extract attachments
            attachments = []
            mime_types = []

            def extract_attachments(part):
                if 'filename' in part and part['filename']:
                    attachments.append(part['filename'])

                # Extract MIME type
                mime_type = part.get('mimeType')
                if mime_type:
                    mime_types.append(mime_type)

                # Recurse into parts
                if 'parts' in part:
                    for subpart in part['parts']:
                        extract_attachments(subpart)

            extract_attachments(message['payload'])

            # Get body (both plain and HTML)
            body_data = self.get_email_body(message_id)
            label_ids = message.get('labelIds', [])
            gmail_tag = '----'

            if label_ids:
                sortify_categories = [
                    "Vezetőség", "Hiányos", "Hibás csatolmány", "Hírlevél",
                    "Neptun", "Tanulói", "Milton", "Moodle", "Egyéb"
                ]

                label_map = self.get_label_map()  # cache-elt címkék

                for label_id in label_ids:
                    label_name = label_map.get(label_id, '')
                    if label_name in sortify_categories:
                        gmail_tag = label_name
                        break

            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'datetime': formatted_date,
                'attachment_count': len(attachments),
                'attachment_names': '|'.join(attachments) if attachments else '',
                'mime_types': '|'.join(mime_types) if mime_types else '',
                'body_plain': body_data.get('plain', ''),
                'body_html': body_data.get('html', ''),
                'tag': gmail_tag,  # ← ÚJ SOR IDE
                'is_last_downloaded': 1
            }

        except HttpError as error:
            print(f'Error fetching email {message_id}: {error}')
            return None

    def send_message(self, to, subject, body):
        """Send an email message"""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            print(f'Message Id: {send_message["id"]}')
            return send_message
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def get_label_map(self):
        """Get all Gmail labels (cached)"""
        if self._label_cache is None:
            try:
                labels_response = self.service.users().labels().list(userId='me').execute()
                self._label_cache = {lbl['id']: lbl['name'] for lbl in labels_response.get('labels', [])}
            except Exception as e:
                print(f"[GMAIL] Label cache error: {e}")
                self._label_cache = {}
        return self._label_cache
