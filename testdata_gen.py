"""
Test data generator for Sortify email system
Generates HTML email bodies and creates emails_test.csv with full schema
"""
import csv
import os
import random
from pathlib import Path


def generate_email_body_html(sender_name, subject, sender_domain):
    """
    Generate contextual HTML email body based on sender and subject.
    Returns 3-15 sentences of relevant content.
    """

    # Detect email category
    is_leadership = any(name in sender_name for name in [
        "Grajczjár", "Szegediné", "Lengyel", "Szayly", "Kukla", "Szabó Kálmán"
    ])
    is_department = "uni-milton.hu" in sender_domain and not is_leadership
    is_student = sender_domain in ["gmail.com", "email.com", "gmx.de", "office.com",
                                    "yahoo.com", "citromail.hu", "studentmail.hu", "pm.me"]

    # Base templates by category
    if is_leadership:
        templates = [
            f"<p>Kedves Kollégák!</p><p>Az alábbi témában szeretném egyeztetni az elképzeléseimet: <strong>{subject}</strong>.</p>",
            f"<p>Tisztelt Tanszékvezetők!</p><p>A {subject} kapcsán kérem, szíveskedjenek állást foglalni a következő kérdésekben.</p>",
            f"<p>Kedves Munkatársak!</p><p>A rektorátus kérésére összefoglalnám a {subject} jelenlegi státuszát.</p>"
        ]
    elif is_department:
        templates = [
            f"<p>Kedves Kollégák!</p><p>A(z) {subject} témában kérem a visszajelzéseiteket.</p>",
            f"<p>Sziasztok!</p><p>Szeretném megosztani veletek az aktuális információkat a következő témában: {subject}.</p>",
            f"<p>Kedves Csapat!</p><p>A mai nap folyamán felmerült egy fontos kérdés a(z) {subject} kapcsán.</p>"
        ]
    elif is_student:
        templates = [
            f"<p>Tisztelt {sender_name.split()[0] if ' ' in sender_name else 'Tanár Úr/Hölgy'}!</p><p>A(z) {subject} tárgyában szeretném kérni a segítségét.</p>",
            f"<p>Kedves Tanár Úr/Hölgy!</p><p>Ezúton fordulok Önhöz a következő ügyben: {subject}.</p>",
            f"<p>Tisztelt Oktató!</p><p>Kérdésem lenne a(z) {subject} témakörrel kapcsolatban.</p>"
        ]
    else:
        templates = [
            f"<p>Kedves Címzett!</p><p>A(z) {subject} ügyében keresem meg Önt.</p>",
            f"<p>Tisztelt Partnerünk!</p><p>Ezúton tájékoztatom a(z) {subject} aktuális állapotáról.</p>"
        ]

    # Generate body paragraphs
    body_paragraphs = []
    intro = random.choice(templates)
    body_paragraphs.append(intro)

    # Add 2-14 more sentences
    num_sentences = random.randint(2, 14)

    filler_sentences = [
        "<p>Kérem, szíveskedjen mielőbb visszajelezni az ügyben.</p>",
        "<p>A határidő közeledtével egyre sürgetőbbé válik a döntés meghozatala.</p>",
        "<p>Amennyiben bármilyen kérdése merülne fel, állok rendelkezésére.</p>",
        "<p>A csatolt dokumentumokat kérem, tekintse át.</p>",
        "<p>A megbeszélt időpontban várom visszajelzését.</p>",
        "<p>Remélem, hamarosan találkozhatunk személyesen is.</p>",
        "<p>Köszönöm a türelmét és együttműködését.</p>",
        "<p>Az érintett kollégákat is tájékoztattam az ügyben.</p>",
        "<p>A következő lépések megbeszélése érdekében kérem, jelezzen vissza.</p>",
        "<p>Amennyiben további információkra van szüksége, keressen bizalommal.</p>",
        "<p>A projekt jelenlegi státuszát az alábbi linken követheti.</p>",
        "<p>Kérem, vegye figyelembe a módosított határidőket.</p>",
        "<p>A csapat többi tagjával is egyeztettem az ügyben.</p>",
        "<p>Várhatóan a jövő héten tudok részletesebb tájékoztatást adni.</p>",
        "<p>Az előző megbeszélésen felmerült pontokat összefoglaltam.</p>"
    ]

    selected = random.sample(filler_sentences, min(num_sentences, len(filler_sentences)))
    body_paragraphs.extend(selected)

    # Add closing
    closings = [
        "<p>Üdvözlettel,<br><strong>{}</strong></p>".format(sender_name),
        "<p>Tisztelettel,<br>{}</p>".format(sender_name),
        "<p>Köszönettel,<br>{}</p>".format(sender_name)
    ]
    body_paragraphs.append(random.choice(closings))

    # Build final HTML
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        p {{ margin: 10px 0; }}
    </style>
</head>
<body>
{}
</body>
</html>""".format("\n".join(body_paragraphs))

    return html


def main():
    """Main test data generation logic"""

    # Paths
    input_csv = "emails_mod-XX-v2.csv"
    output_csv = "data/emails_test.csv"
    bodies_dir = "data/bodies"

    # Create bodies directory if not exists
    Path(bodies_dir).mkdir(parents=True, exist_ok=True)

    # Read input CSV
    print(f"[INFO] Reading input CSV: {input_csv}")
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[INFO] Found {len(rows)} rows in input CSV")

    # Process each row
    enhanced_rows = []
    for idx, row in enumerate(rows, 1):
        # Clean row: remove None/empty keys that come from trailing commas
        cleaned_row = {k: v for k, v in row.items() if k is not None and k.strip() != ''}

        message_id = cleaned_row.get('message_id', '')
        sender_name = cleaned_row.get('sender_name', '')
        sender_domain = cleaned_row.get('sender_domain', '')
        subject = cleaned_row.get('subject', '')

        if not message_id:
            print(f"[WARNING] Row {idx} has no message_id, skipping...")
            continue

        # Generate HTML body
        html_content = generate_email_body_html(sender_name, subject, sender_domain)

        # Save HTML file
        html_filename = f"{message_id}.html"
        html_path = os.path.join(bodies_dir, html_filename)

        with open(html_path, 'w', encoding='utf-8') as hf:
            hf.write(html_content)

        print(f"[{idx}/{len(rows)}] Generated: {html_filename}")

        # Add new columns to cleaned row
        cleaned_row['body_file'] = f"data/bodies/{html_filename}"
        cleaned_row['body_format'] = "html"
        cleaned_row['ai_summary'] = ""  # Leave empty as requested

        enhanced_rows.append(cleaned_row)

    # Write output CSV
    print(f"\n[INFO] Writing output CSV: {output_csv}")

    # Ensure output directory exists
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)

    # Define full column order
    fieldnames = [
        'message_id', 'sender', 'sender_name', 'sender_domain', 'subject',
        'datetime', 'attachment_count', 'attachment_names', 'mime_types',
        'tag', 'is_last_downloaded', 'needs_more_info', 'rule_applied',
        'body_file', 'body_format', 'ai_summary'
    ]

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(enhanced_rows)

    print(f"[SUCCESS] Generated {len(enhanced_rows)} emails with HTML bodies")
    print(f"[SUCCESS] Output saved to: {output_csv}")
    print(f"[SUCCESS] HTML files saved to: {bodies_dir}/")


if __name__ == "__main__":
    main()
