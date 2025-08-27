from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle

# Google Drive scope (read-only is enough for testing)
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def main():
    # Start OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)

    # Save credentials for next time
    with open("token.pickle", "wb") as token:
        pickle.dump(creds, token)

    # Test by listing first 10 files in Drive
    service = build("drive", "v3", credentials=creds)
    results = service.files().list(pageSize=10, fields="files(id, name)").execute()
    items = results.get("files", [])

    if not items:
        print("No files found.")
    else:
        print("Files:")
        for item in items:
            print(f"{item['name']} ({item['id']})")

if __name__ == "__main__":
    main()
