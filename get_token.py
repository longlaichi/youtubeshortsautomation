from google_auth_oauthlib.flow import InstalledAppFlow
import json

# YouTube upload scope
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    # Load OAuth client (downloaded from Google Cloud → "Desktop App")
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", SCOPES
    )

    # Run local server to authenticate
    creds = flow.run_local_server(
        port=0,
        access_type="offline",   # ensures we get a refresh_token
        prompt="consent"         # force asking consent every time -> guarantees refresh_token
    )

    # Save credentials as JSON (preferred over pickle for GitHub secrets)
    with open("token.json", "w") as f:
        f.write(creds.to_json())

    print("✅ Saved token.json with refresh_token. This will not expire after 7 days if your OAuth app is in PRODUCTION mode.")

if __name__ == "__main__":
    main()
