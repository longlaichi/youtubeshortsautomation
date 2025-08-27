import os
import pickle
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
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
    if not gauth.credentials or gauth.credentials.valid:
        gauth.LocalWebserverAuth()

        # Save the credentials to token.pickle
        with open("token.pickle", "wb") as token_file:
            pickle.dump(gauth.credentials, token_file)

    return GoogleDrive(gauth)

# ======================
# YouTube API Auth
# ======================
# ======================
# YouTube API Auth
# ======================
def authenticate_youtube():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token_file:
            creds = pickle.load(token_file)

    if not creds or not creds.valid:
        # If expired, refresh
        from google.auth.transport.requests import Request
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If no creds, run OAuth
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                scopes=["https://www.googleapis.com/auth/youtube.upload",
                        "https://www.googleapis.com/auth/drive"]
            )
            creds = flow.run_local_server(port=0)

        # Save creds for next run
        with open("token.pickle", "wb") as token_file:
            pickle.dump(creds, token_file)

    return build("youtube", "v3", credentials=creds)

# ======================
# Main Posting Logic
# ======================
def main():
    # Authenticate Google Drive
    drive = authenticate_google_drive()

    # Authenticate YouTube
    youtube = authenticate_youtube()

    # Get all files in specified folder IDs
    folder_ids = os.environ["DRIVE_FOLDER_IDS"].split(",")  # comma-separated IDs
    all_files = []
    for folder_id in folder_ids:
        file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        all_files.extend(file_list)

    if not all_files:
        print("No files found in Google Drive folders.")
        return

    # Process first unposted video (you can improve with posted.json)
    first_file = all_files[0]
    video_filename = first_file['title']
    print("Downloading:", video_filename)
    first_file.GetContentFile(video_filename)

    # Generate caption using your caption_generator.py
    caption = generate_caption(video_filename)

    # Upload video to YouTube
    media_file = MediaFileUpload(video_filename, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": video_filename,
                "description": caption,
                "tags": ["motivation", "shorts", "AI-generated"],
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=media_file
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading... {int(status.progress() * 100)}%")

    print("Uploaded successfully:", video_filename)

    # Delete local file
    os.remove(video_filename)

if __name__ == "__main__":
    main()
