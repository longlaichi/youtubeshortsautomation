import os
import subprocess
import json
import base64
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

from caption_generator import get_unique_caption
from record_keeper import load_posted, save_posted

# -----------------------------
# CONFIG
# -----------------------------
POSTED_FILE = "posted.json"

# -----------------------------
# Google Drive (service account)
# -----------------------------
def authenticate_drive():
    from oauth2client.service_account import ServiceAccountCredentials
    creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    return GoogleDrive(gauth)

def get_next_file(drive, folder_ids, posted_ids):
    for folder_id in folder_ids:
        try:
            file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        except Exception as e:
            print(f"❌ Failed to list files in folder {folder_id}: {e}")
            continue
        for file in file_list:
            if file['id'] not in posted_ids and file['title'].lower().endswith(".mp4"):
                return file['id'], file['title']
    return None, None

def download_file(drive, file_id, filename):
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(filename)
    print(f"✅ Downloaded {filename}")

# -----------------------------
# FFmpeg Processing
# -----------------------------
def ffmpeg_process(input_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"🎬 Processed video saved to {output_path}")

# -----------------------------
# YouTube (personal account via OAuth token)
# -----------------------------
def authenticate_youtube():
    b64_token = os.environ.get("YOUTUBE_TOKEN_B64")
    if not b64_token:
        raise ValueError("YOUTUBE_TOKEN_B64 secret not set!")
    token_json = base64.b64decode(b64_token).decode("utf-8")
    creds_dict = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(
        creds_dict, ["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(youtube, video_file, title, description):
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": ["motivation", "inspiration", "shorts", "success", "discipline"],
            "categoryId": "22"
        },
        "status": {"privacyStatus": "public"}
    }
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response.get("id")

# -----------------------------
# Main
# -----------------------------
def main():
    print("🔑 Authenticating Google Drive and YouTube...")
    drive = authenticate_drive()
    youtube = authenticate_youtube()

    # Load posted video IDs
    posted_ids = load_posted()

    # Get folders
    folder_ids_str = os.getenv("DRIVE_FOLDER_IDS")
    if not folder_ids_str:
        raise ValueError("DRIVE_FOLDER_IDS environment variable not set!")
    folder_ids = [fid.strip() for fid in folder_ids_str.split(",") if fid.strip()]

    print(f"📂 Searching in folders: {folder_ids}")
    file_id, file_title = get_next_file(drive, folder_ids, posted_ids)
    if not file_id:
        print("🎉 All videos already posted!")
        return

    local_file = file_title
    download_file(drive, file_id, local_file)
    processed_file = f"processed_{local_file}"

    print("🎥 Processing video...")
    ffmpeg_process(local_file, processed_file)

    print("✍️ Generating caption...")
    caption_text, hashtags = get_unique_caption()
    description = f"{caption_text}\n\n{hashtags}"

    print(f"📤 Uploading to YouTube: {file_title}")
    try:
        video_id = upload_to_youtube(youtube, processed_file, caption_text, description)
        print(f"✅ Uploaded video ID: {video_id}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return

    posted_ids.append(file_id)
    save_posted(posted_ids)

    # Cleanup
    os.remove(local_file)
    os.remove(processed_file)
    print("🧹 Cleanup done. Process finished successfully!")

if __name__ == "__main__":
    main()
