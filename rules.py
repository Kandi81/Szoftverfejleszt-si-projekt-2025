"""
Email categorization rule engine.
Applies rules based on sender address/domain to assign tags.
"""

from typing import List, Dict

# -------- Hardcoded rule configuration --------
# Later these will be moved to an INI file and editable via Settings UI

# Leadership (vezetosegi): exact email addresses
# NOTE: These should be ONLY the top leadership (not overlapping with department)
LEADERSHIP_EMAILS = {
    "toth.tamas@uni-milton.hu",
    "kovacs.aron@uni-milton.hu",
    "grajczjar.istvan@uni-milton.hu",
    "szegedine.lengyel.piroska@uni-milton.hu",
    "szayly.jozsef@uni-milton.hu",
    "kukla.krisztian@uni-milton.hu",
    "szabo.k.gabor@uni-milton.hu",
    "schottner.krisztina@uni-milton.hu",
    # Add more leadership emails here (department heads from OTHER departments)
}

# Department (tanszek): exact email addresses of people in the user's department
# In the future, read from Settings (user specifies their department)
DEPARTMENT_EMAILS = {
    "honfi@uni-milton.hu",
    "barkanyi.pal@uni-milton.hu",
    "cser.jozsef@uni-milton.hu",
    "illesi.zsolt@uni-milton.hu",
    "nyikes.zoltan@uni-milton.hu",
    "atol.gabor@uni-milton.hu",
    "belle.csabane@uni-milton.hu",
    "feherpolgar.pal@uni-milton.hu",
    "keszthelyi.andras@uni-milton.hu",
    "kuris.zoltan@uni-milton.hu",
    "levai.istvan@uni-milton.hu",
    "madarasz.istvan@uni-milton.hu",
    "molnar.tamas@uni-milton.hu",
    "nagy.istvan@uni-milton.hu",
    "nemeth.imre.istvan@uni-milton.hu",
    "racz.julianna@uni-milton.hu",
    "szabo.istvan@uni-milton.hu",
    "szalai.patrik@uni-milton.hu",
    "tokodi.gergely@uni-milton.hu",
    "udvaros.jozsef@uni-milton.hu",
    "attila@dlabs.hu",
    # Add department colleagues here
}

# System-specific addresses or domains
NEPTUN_ADDRESSES = {
    "neptun@uni-milton.hu",
    "scott.d.edu@pm.me",
}

MOODLE_ADDRESSES = {
    "moodle@uni-milton.hu",
}

MILTON_ADDRESSES = {
    "noreply@milt-on.hu",
}

# University domain
UNI_DOMAIN = "uni-milton.hu"


def extract_email_from_sender(sender: str) -> str:
    """
    Extract email address from 'Name <email@domain.com>' format.
    Returns lowercase email.
    """
    if "<" in sender and ">" in sender:
        start = sender.index("<") + 1
        end = sender.index(">")
        return sender[start:end].strip().lower()
    return sender.strip().lower()


def apply_rules(emails: List[Dict]) -> List[Dict]:
    """
    Apply categorization rules to a list of emails.
    Updates 'tag' and 'rule_applied' fields in place.
    Returns the updated list.

    Rules are applied in priority order:
    1. tanszek (department) - YOUR department takes precedence
    2. vezetoseg (leadership) - other department heads and top management
    3. neptun
    4. moodle
    5. milt-on
    6. Student emails (non-university domain) - LAST priority before default
    7. Default (uncategorized - stays as ----)
    """
    for email in emails:
        sender_raw = email.get("sender", "")
        sender_email = extract_email_from_sender(sender_raw)
        sender_domain = email.get("sender_domain", "").lower()

        # Priority 1: Department (YOUR department first!)
        if sender_email in DEPARTMENT_EMAILS:
            email["tag"] = "tanszek"
            email["rule_applied"] = "tanszek"
            continue

        # Priority 2: Leadership (other department heads)
        if sender_email in LEADERSHIP_EMAILS:
            email["tag"] = "vezetoseg"
            email["rule_applied"] = "vezetoseg"
            continue

        # Priority 3: Neptun
        if sender_email in NEPTUN_ADDRESSES or "neptun" in sender_domain:
            email["tag"] = "neptun"
            email["rule_applied"] = "neptun"
            continue

        # Priority 4: Moodle
        if sender_email in MOODLE_ADDRESSES or "moodle" in sender_domain:
            email["tag"] = "moodle"
            email["rule_applied"] = "moodle"
            continue

        # Priority 5: Milt-On
        if sender_email in MILTON_ADDRESSES or "milt-on" in sender_domain:
            email["tag"] = "milt-on"
            email["rule_applied"] = "milt-on"
            continue

        # Priority 6: Student emails (non-university domain) - MOVED TO END
        if sender_domain and UNI_DOMAIN not in sender_domain:
            email["tag"] = "hianyos"
            email["rule_applied"] = "student_mail"
            continue

        # Default: Uncategorized/incomplete (keep as ----)
        # This catches uni-milton.hu emails that didn't match any specific rule
        email["tag"] = "----"
        email["rule_applied"] = ""

    return emails


def get_rule_summary() -> Dict[str, int]:
    """
    Return a summary of configured rules (for debugging/settings display).
    """
    return {
        "leadership_count": len(LEADERSHIP_EMAILS),
        "department_count": len(DEPARTMENT_EMAILS),
        "neptun_count": len(NEPTUN_ADDRESSES),
        "moodle_count": len(MOODLE_ADDRESSES),
        "milton_count": len(MILTON_ADDRESSES),
    }


# Example for testing
if __name__ == "__main__":
    test_emails = [
        {
            "message_id": "1",
            "sender": "Dr. Honfi Vid <honfi@uni-milton.hu>",
            "sender_domain": "uni-milton.hu",
            "subject": "Department meeting",
            "tag": "----",
            "rule_applied": ""
        },
        {
            "message_id": "2",
            "sender": "Dr. Grajczjár <grajczjar.istvan@uni-milton.hu>",
            "sender_domain": "uni-milton.hu",
            "subject": "Leadership announcement",
            "tag": "----",
            "rule_applied": ""
        },
        {
            "message_id": "3",
            "sender": "student@gmail.com",
            "sender_domain": "gmail.com",
            "subject": "Question about homework",
            "tag": "----",
            "rule_applied": ""
        },
        {
            "message_id": "4",
            "sender": "neptun@uni-milton.hu",
            "sender_domain": "uni-milton.hu",
            "subject": "Grade notification",
            "tag": "----",
            "rule_applied": ""
        },
    ]

    apply_rules(test_emails)

    for e in test_emails:
        print(f"{e['sender']:50s} -> {e['tag']:15s} ({e['rule_applied']})")

    print("\nRule summary:", get_rule_summary())
