import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from caption_generator import generate_caption

# ======================
# Google Drive Auth
# ======================
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from google.oauth2.service_account import Credentials
import json
import os

def authenticate_google_drive():
    creds_json = os.environ["GDRIVE_CREDS_JSON_B64"]
    creds_dict = json.loads(base64.b64decode(creds_json).decode("utf-8"))
    creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/drive"])
    
    gauth = GoogleAuth()
    gauth.credentials = creds
    return GoogleDrive(gauth)
# ======================
# YouTube API Auth
# ======================
def authenticate_youtube():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)

# ======================
# Main Posting Logic
# ======================
def main():
    drive = authenticate_google_drive()
    youtube = authenticate_youtube()

    folder_ids = os.environ["DRIVE_FOLDER_IDS"].split(",")
    all_files = []
    for folder_id in folder_ids:
        file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        all_files.extend(file_list)

    if not all_files:
        print("No files found in Google Drive folders.")
        return

    first_file = all_files[0]
    video_filename = first_file['title']
    print("Downloading:", video_filename)
    first_file.GetContentFile(video_filename)

    caption = generate_caption(video_filename)

    media_file = MediaFileUpload(video_filename, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": video_filename,
                "description": caption,
                "tags": ["motivation", "shorts", "AI-generated"],
                "categoryId": "22",
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=media_file
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading... {int(status.progress() * 100)}%")

    print("Uploaded successfully:", video_filename)
    os.remove(video_filename)

if __name__ == "__main__":
    main()