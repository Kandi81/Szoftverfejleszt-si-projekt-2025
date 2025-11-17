"""
Email categorization rule engine.
Applies rules based on sender address/domain to assign tags.
Rules are loaded from config/settings.ini with hardcoded fallback.
"""

from typing import List, Dict, Set
import configparser
import os


# -------- Hardcoded fallback configuration --------
# Used if INI file is missing or corrupt

FALLBACK_LEADERSHIP_EMAILS = {
    "toth.tamas@uni-milton.hu",
    "kovacs.aron@uni-milton.hu",
    "grajczjar.istvan@uni-milton.hu",
    "szegedine.lengyel.piroska@uni-milton.hu",
    "szayly.jozsef@uni-milton.hu",
    "kukla.krisztian@uni-milton.hu",
    "szabo.k.gabor@uni-milton.hu",
    "schottner.krisztina@uni-milton.hu",
}

FALLBACK_DEPARTMENT_EMAILS = {
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
}

FALLBACK_NEPTUN_ADDRESSES = {
    "neptun@uni-milton.hu",
    "scott.d.edu@pm.me",
}

FALLBACK_MOODLE_ADDRESSES = {
    "moodle@uni-milton.hu",
}

FALLBACK_MILTON_ADDRESSES = {
    "noreply@milt-on.hu",
}

FALLBACK_UNI_DOMAIN = "uni-milton.hu"


# -------- Runtime configuration (loaded from INI or fallback) --------

LEADERSHIP_EMAILS: Set[str] = set()
DEPARTMENT_EMAILS: Set[str] = set()
NEPTUN_ADDRESSES: Set[str] = set()
NEPTUN_DOMAINS: Set[str] = set()
MOODLE_ADDRESSES: Set[str] = set()
MOODLE_DOMAINS: Set[str] = set()
MILTON_ADDRESSES: Set[str] = set()
MILTON_DOMAINS: Set[str] = set()
UNI_DOMAIN: str = ""


def load_rules_from_ini(ini_path: str = "config/settings.ini") -> bool:
    """
    Load rules from INI file. Returns True if successful, False if fallback used.
    """
    global LEADERSHIP_EMAILS, DEPARTMENT_EMAILS, NEPTUN_ADDRESSES, NEPTUN_DOMAINS
    global MOODLE_ADDRESSES, MOODLE_DOMAINS, MILTON_ADDRESSES, MILTON_DOMAINS, UNI_DOMAIN

    if not os.path.exists(ini_path):
        print(f"[RULES] INI file not found: {ini_path}, using fallback")
        _load_fallback()
        return False

    try:
        config = configparser.ConfigParser()
        config.read(ini_path, encoding='utf-8')

        # Load leadership
        if config.has_option('rules.leadership', 'emails'):
            emails_str = config.get('rules.leadership', 'emails')
            LEADERSHIP_EMAILS = {email.strip().lower() for email in emails_str.split(',') if email.strip()}
        else:
            LEADERSHIP_EMAILS = FALLBACK_LEADERSHIP_EMAILS.copy()

        # Load department
        if config.has_option('rules.department', 'emails'):
            emails_str = config.get('rules.department', 'emails')
            DEPARTMENT_EMAILS = {email.strip().lower() for email in emails_str.split(',') if email.strip()}
        else:
            DEPARTMENT_EMAILS = FALLBACK_DEPARTMENT_EMAILS.copy()

        # Load neptun
        if config.has_option('rules.neptun', 'emails'):
            emails_str = config.get('rules.neptun', 'emails')
            NEPTUN_ADDRESSES = {email.strip().lower() for email in emails_str.split(',') if email.strip()}
        else:
            NEPTUN_ADDRESSES = FALLBACK_NEPTUN_ADDRESSES.copy()

        if config.has_option('rules.neptun', 'domains'):
            domains_str = config.get('rules.neptun', 'domains')
            NEPTUN_DOMAINS = {domain.strip().lower() for domain in domains_str.split(',') if domain.strip()}
        else:
            NEPTUN_DOMAINS = {'neptun'}

        # Load moodle
        if config.has_option('rules.moodle', 'emails'):
            emails_str = config.get('rules.moodle', 'emails')
            MOODLE_ADDRESSES = {email.strip().lower() for email in emails_str.split(',') if email.strip()}
        else:
            MOODLE_ADDRESSES = FALLBACK_MOODLE_ADDRESSES.copy()

        if config.has_option('rules.moodle', 'domains'):
            domains_str = config.get('rules.moodle', 'domains')
            MOODLE_DOMAINS = {domain.strip().lower() for domain in domains_str.split(',') if domain.strip()}
        else:
            MOODLE_DOMAINS = {'moodle'}

        # Load milton
        if config.has_option('rules.milton', 'emails'):
            emails_str = config.get('rules.milton', 'emails')
            MILTON_ADDRESSES = {email.strip().lower() for email in emails_str.split(',') if email.strip()}
        else:
            MILTON_ADDRESSES = FALLBACK_MILTON_ADDRESSES.copy()

        if config.has_option('rules.milton', 'domains'):
            domains_str = config.get('rules.milton', 'domains')
            MILTON_DOMAINS = {domain.strip().lower() for domain in domains_str.split(',') if domain.strip()}
        else:
            MILTON_DOMAINS = {'milt-on'}

        # Load general
        if config.has_option('general', 'uni_domain'):
            UNI_DOMAIN = config.get('general', 'uni_domain').strip().lower()
        else:
            UNI_DOMAIN = FALLBACK_UNI_DOMAIN

        print(f"[RULES] Loaded from INI: {len(LEADERSHIP_EMAILS)} leadership, "
              f"{len(DEPARTMENT_EMAILS)} department, "
              f"{len(NEPTUN_ADDRESSES)} neptun, "
              f"{len(MOODLE_ADDRESSES)} moodle, "
              f"{len(MILTON_ADDRESSES)} milton")
        return True

    except Exception as ex:
        print(f"[RULES] Error loading INI: {ex}, using fallback")
        _load_fallback()
        return False


def _load_fallback():
    """Load hardcoded fallback rules"""
    global LEADERSHIP_EMAILS, DEPARTMENT_EMAILS, NEPTUN_ADDRESSES, NEPTUN_DOMAINS
    global MOODLE_ADDRESSES, MOODLE_DOMAINS, MILTON_ADDRESSES, MILTON_DOMAINS, UNI_DOMAIN

    LEADERSHIP_EMAILS = FALLBACK_LEADERSHIP_EMAILS.copy()
    DEPARTMENT_EMAILS = FALLBACK_DEPARTMENT_EMAILS.copy()
    NEPTUN_ADDRESSES = FALLBACK_NEPTUN_ADDRESSES.copy()
    NEPTUN_DOMAINS = {'neptun'}
    MOODLE_ADDRESSES = FALLBACK_MOODLE_ADDRESSES.copy()
    MOODLE_DOMAINS = {'moodle'}
    MILTON_ADDRESSES = FALLBACK_MILTON_ADDRESSES.copy()
    MILTON_DOMAINS = {'milt-on'}
    UNI_DOMAIN = FALLBACK_UNI_DOMAIN
    print("[RULES] Using hardcoded fallback rules")


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
    for email_item in emails:
        sender_raw = email_item.get("sender", "")
        sender_email = extract_email_from_sender(sender_raw)
        sender_domain = email_item.get("sender_domain", "").lower()

        # Priority 1: Department (YOUR department first!)
        if sender_email in DEPARTMENT_EMAILS:
            email_item["tag"] = "tanszek"
            email_item["rule_applied"] = "tanszek"
            continue

        # Priority 2: Leadership (other department heads)
        if sender_email in LEADERSHIP_EMAILS:
            email_item["tag"] = "vezetoseg"
            email_item["rule_applied"] = "vezetoseg"
            continue

        # Priority 3: Neptun
        if sender_email in NEPTUN_ADDRESSES or any(d in sender_domain for d in NEPTUN_DOMAINS):
            email_item["tag"] = "neptun"
            email_item["rule_applied"] = "neptun"
            continue

        # Priority 4: Moodle
        if sender_email in MOODLE_ADDRESSES or any(d in sender_domain for d in MOODLE_DOMAINS):
            email_item["tag"] = "moodle"
            email_item["rule_applied"] = "moodle"
            continue

        # Priority 5: Milt-On
        if sender_email in MILTON_ADDRESSES or any(d in sender_domain for d in MILTON_DOMAINS):
            email_item["tag"] = "milt-on"
            email_item["rule_applied"] = "milt-on"
            continue

        # Priority 6: Student emails (non-university domain) - MOVED TO END
        if sender_domain and UNI_DOMAIN not in sender_domain:
            email_item["tag"] = "hianyos"
            email_item["rule_applied"] = "student_mail"
            continue

        # Default: Uncategorized/incomplete (keep as ----)
        # This catches uni-milton.hu emails that didn't match any specific rule
        email_item["tag"] = "----"
        email_item["rule_applied"] = ""

    return emails


def get_rule_summary() -> Dict:
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


# Load rules on module import
load_rules_from_ini()


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

    for test_email in test_emails:
        print(f"{test_email['sender']:50s} -> {test_email['tag']:15s} ({test_email['rule_applied']})")

    print("\nRule summary:", get_rule_summary())
