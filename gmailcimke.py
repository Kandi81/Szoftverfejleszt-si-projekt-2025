import resource.config
from gmailclient import GmailClient

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.labels"]


def cimke_lekerdezes():
    client = GmailClient(credentials_path="resource/credentials.json", token_path="resource/token.json")
    client.authenticate()
    labels = client.list_labels()
    for label in labels:
        print(f"{label['name']} (ID: {label['id']})")


def alap_cimkek_hozzaadasa():
    labels = ['p3', 'p4']
    created_labels = []
    client = GmailClient(credentials_path="resource/credentials.json", token_path="resource/token.json")
    client.authenticate()

    # Végigmegyünk a címkéken és mindegyiket létrehozzuk
    for label_name in labels:
        label = client.create_label(label_name)  # paraméterként add meg a nevet!
        print(f'Label "{label["name"]}" created (ID: {label["id"]})')
        created_labels.append(label)

    return created_labels

def cimke():
    client = GmailClient(credentials_path="resource/credentials.json", token_path="resource/token.json")
    client.authenticate()
    letezo_cimkek = client.list_labels()
    letezo_cimke_nevek = {label["name"]: label["id"] for label in letezo_cimkek}
    letrehozando_cimkek = [
        "Vezetőség", "Hiányos", "Hibás csatolmány", "Hírlevél",
        "Neptun", "Tanulói", "Milton", "Moodle", "Egyéb"
    ]
    label_ids = []
    for name in letrehozando_cimkek:
        if name in letezo_cimke_nevek:
            print(f' Címke már létezik: "{name}" (ID: {letezo_cimke_nevek[name]})')
            label_ids.append(letezo_cimke_nevek[name])
        else:
            print(f' Címke nem létezik, létrehozás: "{name}"')
            created = client.create_label(name)
            print(f' Létrehozva: "{created["name"]}" (ID: {created["id"]})')
            label_ids.append(created["id"])

cimke()
