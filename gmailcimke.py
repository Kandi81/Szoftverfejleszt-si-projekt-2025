import resource.config
from gmailclient import GmailClient

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.labels"]




def cimke_lekerdezes():
    client = GmailClient(credentials_path="resource/credentials.json", token_path="resource/token.json")
    client.authenticate()  # uses the existing quickstart token flow
    labels = client.list_labels()
    for label in labels:
        print(f"{label['name']} (ID: {label['id']})")


def alap_cimkek_hozzaadasa():
    labels = ['p1', 'p2']
    created_labels = []
    client = GmailClient(credentials_path="resource/credentials.json", token_path="resource/token.json")
    client.authenticate()  # uses the existing quickstart token flow
    # Új címke létrehozása
    name = 'Proba1'
    label = client.create_label(name)
    print(f'Label "{label["name"]}" created')
    created_labels.append(label)
    client.create_label( f'{label["name"]}')
    print(f'{label["name"]} created')

alap_cimkek_hozzaadasa()

                


alap_cimkek_hozzaadasa()



