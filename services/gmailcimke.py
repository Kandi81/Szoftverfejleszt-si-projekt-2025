"""
Gmail Label Service
Címke műveletek a Sortify alkalmazáshoz.
Integrálva a modular architecture-be.
"""

from typing import Dict, List
from models.app_state import app_state


def _get_gmail_service():
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
    service = gmail.service
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
    Töröli az összes többi Sortify címkét az emailről.

    Args:
        message_id: Gmail message ID
        label_name: Címke neve (pl. "Vezetőség")
    """
    gmail = _get_gmail_service()
    service = gmail.service

    # Az összes Sortify címke
    sortify_categories = [
        "Vezetőség", "Hiányos", "Hibás csatolmány", "Hírlevél",
        "Neptun", "Tanulói", "Milton", "Moodle", "Egyéb"
    ]

    # Biztosítjuk, hogy létezzenek a címkék
    all_labels = ensure_labels(sortify_categories)

    # Új címke ID
    new_label_id = all_labels.get(label_name)

    if not new_label_id:
        print(f"[GMAIL-LABEL] ✗ HIBA: '{label_name}' címke nem található!")
        return

    # Többi Sortify címke ID-k (amiket törölni kell)
    remove_label_ids = [
        label_id for cat, label_id in all_labels.items()
        if cat != label_name  # ← NE töröljük az újat!
    ]

    print(f"[GMAIL-LABEL] Címke módosítás:")
    print(f"  Hozzáadandó: '{label_name}' (ID: {new_label_id})")
    print(f"  Törlendő címkék: {len(remove_label_ids)} db")

    body = {
        "addLabelIds": [new_label_id],
        "removeLabelIds": remove_label_ids
    }

    result = service.users().messages().modify(
        userId="me",
        id=message_id,
        body=body
    ).execute()

    print(f'✅ Címke hozzáadva: "{label_name}" → message {message_id}')
    print(f'   Törölt címkék: {len(remove_label_ids)} db')
    print(f'[GMAIL] Labels updated: add={body["addLabelIds"]}, remove={remove_label_ids[:3]}...')


def apply_label_to_messages(message_ids: List[str], label_name: str) -> None:
    """Címke hozzáadása több emailhez (batch)."""
    for msg_id in message_ids:
        apply_label_to_message(msg_id, label_name)


def remove_label_from_message(message_id: str, label_name: str) -> None:
    """Címke eltávolítása egy emailről."""
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
