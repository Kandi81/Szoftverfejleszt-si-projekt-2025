# gmailcimke.py - Gmail Label Service
"""
Címke műveletek a Sortify alkalmazáshoz.
Integrálva a modular architecture-be.
"""

from typing import Dict, List
from services.gmail_service import GmailService
from models.app_state import app_state


def _get_gmail_service() -> GmailService:
    """Az aktuális GmailService példány lekérése."""
    if app_state.gmail_service is None:
        raise RuntimeError(
            "GmailService nincs inicializálva.\n"
            "Jelentkezz be a fő alkalmazásból: python main.py"
        )
    return app_state.gmail_service


def list_labels() -> List[dict]:
    """Összes Gmail címke listázása."""
    gmail = _get_gmail_service()
    service = gmail.service  # Gmail API service objektum
    result = service.users().labels().list(userId="me").execute()
    return result.get("labels", [])


def get_label_map() -> Dict[str, str]:
    """Címke név -> ID mapping."""
    labels = list_labels()
    return {lbl["name"]: lbl["id"] for lbl in labels}


def ensure_labels(label_names: List[str]) -> Dict[str, str]:
    """
    Gondoskodik róla, hogy a megadott címkék létezzenek.
    Létrehozza őket ha kell, visszaadja a name -> id mapping-et.
    """
    gmail = _get_gmail_service()
    service = gmail.service

    existing = get_label_map()
    result = {}

    for name in label_names:
        if name in existing:
            print(f'✅ Címke már létezik: "{name}" (ID: {existing[name]})')
            result[name] = existing[name]
            continue

        print(f'➕ Címke létrehozása: "{name}"')
        body = {
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
            "backgroundColor": "#4285f4",
            "textColor": "#ffffff"
        }
        created = service.users().labels().create(userId="me", body=body).execute()
        print(f'✅ Létrehozva: "{created["name"]}" (ID: {created["id"]})')
        result[name] = created["id"]

    return result

def create_default_labels() -> Dict[str, str]:
    """Alap Sortify címkék létrehozása (ha még nincsenek)."""
    default_names = [
        "Vezetőség", "Hiányos", "Hibás csatolmány", "Hírlevél",
        "Neptun", "Tanulói", "Milton", "Moodle", "Egyéb"
    ]
    return ensure_labels(default_names)

def apply_label_to_message(message_id: str, label_name: str) -> None:
    """
    Egy konkrét emailhez címke hozzáadása.

    Args:
        message_id: Gmail message ID (pl. email lista sorából)
        label_name: Címke neve (pl. "Vezetőség")
    """
    gmail = _get_gmail_service()
    service = gmail.service

    # Biztosítja, hogy a címke létezik
    labels = ensure_labels([label_name])
    label_id = labels[label_name]

    body = {
        "addLabelIds": [label_id],
        "removeLabelIds": []
    }
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body=body
    ).execute()
    print(f'✅ Címke hozzáadva: "{label_name}" → message {message_id}')


def remove_label_from_message(message_id: str, label_name: str) -> None:
    """Címke eltávolítása egy emailekről."""
    gmail = _get_gmail_service()
    service = gmail.service

    labels = get_label_map()
    if label_name not in labels:
        print(f'❌ Címke nem található: "{label_name}"')
        return

    label_id = labels[label_name]
    body = {
        "addLabelIds": [],
        "removeLabelIds": [label_id]
    }
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body=body
    ).execute()
    print(f'❌ Címke eltávolítva: "{label_name}" → message {message_id}')
