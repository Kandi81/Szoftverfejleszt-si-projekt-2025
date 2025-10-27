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
    labels = ['p1', 'p2']
    created_labels = []
    client = GmailClient(credentials_path="resource/credentials.json", token_path="resource/token.json")
    client.authenticate()

    # Végigmegyünk a címkéken és mindegyiket létrehozzuk
    for label_name in labels:
        label = client.create_label(label_name)  # paraméterként add meg a nevet!
        print(f'Label "{label["name"]}" created (ID: {label["id"]})')
        created_labels.append(label)

    return created_labels

alap_cimkek_hozzaadasa()
