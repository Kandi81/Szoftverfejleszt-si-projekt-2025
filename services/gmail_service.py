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
        self._label_cache = None  # ← ADDED from branch1

    def authenticate(self):
        """Authenticate with Gmail API"""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
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
            formats = [
                "%a, %d %b %Y %H:%M:%S %z",
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

            return date_str
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

            if 'parts' in payload:
                body_data = self._extract_body_from_part(payload)
            else:
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

            formatted_date = self._parse_date_hungarian(date_str)

            attachments = []
            mime_types = []

            def extract_attachments(part):
                if 'filename' in part and part['filename']:
                    attachments.append(part['filename'])

                mime_type = part.get('mimeType')
                if mime_type:
                    mime_types.append(mime_type)

                if 'parts' in part:
                    for subpart in part['parts']:
                        extract_attachments(subpart)

            extract_attachments(message['payload'])

            body_data = self.get_email_body(message_id)

            # ========== GMAIL LABEL → NORMALIZÁLT TAG ==========
            label_ids = message.get('labelIds', []) or []

            label_map = self.get_label_map()  # id -> name

            # Label-név → belső tag mapping (EZ A LÉNYEG)
            label_name_to_internal_tag = {
                "Vezetőség": "vezetoseg",
                "Vezetoseg": "vezetoseg",
                "Neptun": "neptun",
                "Moodle": "moodle",
                "Milton": "milt-on",
                "Hiányos": "hianyos",
                "Hianyos": "hianyos",
                "Egyéb": "egyeb",
                "Egyeb": "egyeb",
                # ha később kell:
                "Hírlevél": "egyeb",
                "Tanulói": "egyeb",
            }

            tag_internal = "----"
            for lid in label_ids:
                name = label_map.get(lid, "")
                if name in label_name_to_internal_tag:
                    tag_internal = label_name_to_internal_tag[name]
                    break
            # ====================================================

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
                'tag': tag_internal,
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

    def set_message_label(self, message_id: str, new_internal_tag: str) -> None:
        """
        Átállítja az adott üzenet Sortify-címkéjét Gmailben:
        leveszi az összes Sortify-labelt, és felrakja az újat.
        """
        if not self.service:
            return

        # 1) Label ID → név cache már van: get_label_map()
        label_map = self.get_label_map()              # id -> name
        name_to_id = {v: k for k, v in label_map.items()}  # név -> id

        # 2) Belső tag -> Gmail label NÉV
        internal_to_label_name = {
            "vezetoseg": "Vezetőség",
            "tanszek": "Tanszék",
            "neptun": "Neptun",
            "moodle": "Moodle",
            "milt-on": "Milton",
            "hianyos": "Hiányos",
            "egyeb": "Egyéb",
        }

        if new_internal_tag not in internal_to_label_name:
            # ha ---- vagy ismeretlen → csak levesszük a Sortify label-eket
            target_label_name = None
        else:
            target_label_name = internal_to_label_name[new_internal_tag]

        # 3) Sortify label nevek, amiket LE KELL VENNI
        sortify_label_names = {
            "Vezetőség", "Tanszék", "Neptun", "Moodle",
            "Milton", "Hiányos", "Egyéb",
        }
        sortify_label_ids = [name_to_id[n] for n in sortify_label_names if n in name_to_id]

        # Céllabel meghatározása
        add_ids = []
        if target_label_name:
            target_id = name_to_id.get(target_label_name)
            if target_id:
                add_ids.append(target_id)
        else:
            target_id = None

        # NE távolítsuk el azt a labelt, amit épp felteszünk
        if target_id:
            remove_ids = [lid for lid in sortify_label_ids if lid != target_id]
        else:
            remove_ids = sortify_label_ids

        body = {
            "addLabelIds": add_ids,
            "removeLabelIds": remove_ids,
        }

        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body=body
            ).execute()
            print(f"[GMAIL] Labels updated for {message_id}: add={add_ids}, remove={remove_ids}")
        except Exception as e:
            print(f"[GMAIL] Failed to update labels for {message_id}: {e}")


    def get_label_map(self):
        """Get all Gmail labels (cached) - ADDED from branch1"""
        if self._label_cache is None:
            try:
                labels_response = self.service.users().labels().list(userId='me').execute()
                self._label_cache = {lbl['id']: lbl['name'] for lbl in labels_response.get('labels', [])}

                # DEBUG: írd ki az összes labelt
                print("[GMAIL][LABELS]")
                for lid, name in self._label_cache.items():
                    print("   ", lid, "->", repr(name))
            except Exception as e:
                print(f"[GMAIL] Label cache error: {e}")
                self._label_cache = {}
        return self._label_cache
