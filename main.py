import os
import json
import subprocess
import pickle
import base64
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Import caption generator
from caption_generator import get_unique_caption  # <-- use your caption_generator.py

# -----------------------------
# CONFIG
# -----------------------------
SCOPES_DRIVE = ["https://www.googleapis.com/auth/drive.readonly"]
SCOPES_YT = ["https://www.googleapis.com/auth/youtube.upload"]

POSTED_FILE = "posted.json"

# -----------------------------
# Posted video helper
# -----------------------------
def load_posted():
    if os.path.exists(POSTED_FILE):
        try:
            with open(POSTED_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load {POSTED_FILE}: {e}")
    return []

def save_posted(posted):
    try:
        with open(POSTED_FILE, "w") as f:
            json.dump(posted, f, indent=2)
        print(f"✅ Updated {POSTED_FILE} with {len(posted)} videos")
    except Exception as e:
        print(f"❌ Failed to save {POSTED_FILE}: {e}")

# -----------------------------
# Google Drive
# -----------------------------
def authenticate_drive():
    from oauth2client.service_account import ServiceAccountCredentials
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT")
    if not service_account_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT environment variable not set!")

    creds_dict = json.loads(service_account_json)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES_DRIVE)

    gauth = GoogleAuth()
    gauth.credentials = credentials
    return GoogleDrive(gauth)

def get_next_file(drive, folder_ids, posted_ids):
    for folder_id in folder_ids:
        file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
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
    print(f"✅ Processed video saved as {output_path}")

# -----------------------------
# YouTube Upload using token from GitHub secret
# -----------------------------
def authenticate_youtube():
    b64_token = os.environ.get("YOUTUBE_TOKEN_B64")
    if not b64_token:
        raise ValueError("YOUTUBE_TOKEN_B64 secret not set!")
    token_bytes = base64.b64decode(b64_token)
    creds = pickle.loads(token_bytes)
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

    posted_ids = load_posted()

    folder_ids_str = os.getenv("DRIVE_FOLDER_ID")
    if not folder_ids_str:
        raise ValueError("DRIVE_FOLDER_ID environment variable not set!")
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
    video_id = upload_to_youtube(youtube, processed_file, caption_text, description)
    print(f"✅ Uploaded video ID: {video_id}")

    posted_ids.append(file_id)
    save_posted(posted_ids)

    os.remove(local_file)
    os.remove(processed_file)
    print("🧹 Cleanup done. Process finished successfully!")

if __name__ == "__main__":
    main()
