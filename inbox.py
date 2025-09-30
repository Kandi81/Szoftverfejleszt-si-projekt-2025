import resource.config
from gmailclient import GmailClient
from geminiclient import GeminiClient

def main():
    client = GmailClient(credentials_path="resource/credentials.json", token_path="resource/token.json")
    client.authenticate()  # uses the existing quickstart token flow
    messages = client.list_inbox(query="", max_results=50)  # users.messages.list under the hood
    for m in messages:
        msg_id = m["id"]
        subject = client.get_subject(msg_id)  # efficient metadata fetch
        full = client.get_message(msg_id)     # format="full" MIME tree
        snippet = full.get("snippet", "")
        print(subject)
        print(snippet[:500])
        print("-" * 60)

def summarize():
    gmail = GmailClient(credentials_path="resource/credentials.json", token_path="resource/token.json")
    gmail.authenticate()  # uses the existing quickstart token flow
    msg_dicts = gmail.list_inbox(query="", max_results=50)

    gemini = GeminiClient(api_key=resource.config.GEMINI_API_KEY, model="gemini-2.5-flash")

    for m in msg_dicts:
        mid = m["id"]  # extract the string id
        item = gmail.get_subject_and_body(mid)
        subject = item["subject"]
        body = item["text"]
        if not body:
            print(f"[SKIP] {subject} — no body text found.")
            continue
        summary = gemini.summarize_hu(body, max_words=10)
        print("Tárgy:", subject)
        print("Összefoglaló:", summary if summary else "(nincs összefoglaló)")
        print("-" * 60)

summarize()



# Zita ok
# Zita ok1
