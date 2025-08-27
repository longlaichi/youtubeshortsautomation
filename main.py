import os
import pickle
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from instagrapi import Client
from caption_generator import generate_caption

# ======================
# Google Drive Auth
# ======================
def authenticate_google_drive():
    gauth = GoogleAuth()

    # Load token.pickle if it exists
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token_file:
            gauth.credentials = pickle.load(token_file)

    # If credentials are not available or invalid, authenticate again
    if not gauth.credentials or not gauth.credentials.valid:
        gauth.LocalWebserverAuth()

        # Save the credentials to token.pickle
        with open("token.pickle", "wb") as token_file:
            pickle.dump(gauth.credentials, token_file)

    return GoogleDrive(gauth)


# ======================
# Instagram Auth
# ======================
def authenticate_instagram():
    cl = Client()
    cl.login(os.environ["IG_USERNAME"], os.environ["IG_PASSWORD"])
    return cl

# ======================
# Main Posting Logic
# ======================
def main():
    # Authenticate Google Drive
    drive = authenticate_google_drive()

    # Authenticate Instagram
    cl = authenticate_instagram()

    # Example: list first file in Drive
    file_list = drive.ListFile({'q': "'<YOUR_FOLDER_ID>' in parents and trashed=false"}).GetList()
    if not file_list:
        print("No files found in Google Drive.")
        return

    first_file = file_list[0]
    print("Downloading:", first_file['title'])
    first_file.GetContentFile(first_file['title'])

    # Generate caption
    caption = generate_caption(first_file['title'])

    # Upload reel to Instagram
    cl.clip_upload(first_file['title'], caption)

    print("Uploaded successfully:", first_file['title'])

    # Delete local file
    os.remove(first_file['title'])


if __name__ == "__main__":
    main()
