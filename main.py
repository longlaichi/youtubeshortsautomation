import os
import json
import random
import subprocess
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# -----------------------------
# CONFIG
# -----------------------------
SERVICE_ACCOUNT_FILE = "service_account.json"  # Handle via secrets
SCOPES = ["https://www.googleapis.com/auth/drive.readonly",
          "https://www.googleapis.com/auth/youtube.upload"]

FALLBACK_CAPTIONS = [
    "Keep grinding 💪 Success is coming! #Motivation #Success #Grind",
    "Your only limit is you 🚀 #Inspiration #DailyMotivation #DreamBig",
    "Don’t stop until you’re proud 🔥 #NeverGiveUp #StayStrong",
    "Every day is a new chance to grow 🌱 #Mindset #Positivity",
    "Small steps lead to big results 🏆 #Focus #Discipline",
] * 20  # repeat for randomness

# -----------------------------
# Helper Functions
# -----------------------------
def load_posted():
    if os.path.exists("posted.json"):
        with open("posted.json", "r") as f:
            return json.load(f)
    return []

def save_posted(posted):
    with open("posted.json", "w") as f:
        json.dump(posted, f, indent=2)

def get_random_caption():
    return random.choice(FALLBACK_CAPTIONS)

# -----------------------------
# Google Drive
# -----------------------------
def authenticate_drive():
    from oauth2client.service_account import ServiceAccountCredentials
    creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
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

# -----------------------------
# YouTube Upload
# -----------------------------
def authenticate_youtube():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
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
    folder_ids = os.environ["DRIVE_FOLDER_IDS"].split(",")

    print("📂 Looking for next video to upload...")
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
    caption = get_random_caption()

    print("📤 Uploading to YouTube...")
    video_id = upload_to_youtube(youtube, processed_file, caption, caption)
    print(f"✅ Uploaded video ID: {video_id}")

    posted_ids.append(file_id)
    save_posted(posted_ids)

    # Cleanup
    os.remove(local_file)
    os.remove(processed_file)
    print("🧹 Cleanup done. Process finished.")

if __name__ == "__main__":
    main()
