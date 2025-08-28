import os
import json
import random
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from caption_generator import generate_caption

# -----------------------------
# CONFIG
# -----------------------------
SERVICE_ACCOUNT_FILE = "service_account.json"  # Upload this to repo (or handle via secrets)
SCOPES = ["https://www.googleapis.com/auth/drive.readonly",
          "https://www.googleapis.com/auth/youtube.upload"]

# -----------------------------
# YouTube Authentication
# -----------------------------
def authenticate_youtube():
    print("Authenticating YouTube...")
    with open("youtube_token.pkl", "rb") as f:
        import pickle
        creds = pickle.load(f)
    youtube = build("youtube", "v3", credentials=creds)
    print("YouTube authentication completed.")
    return youtube

# -----------------------------
# Drive Authentication
# -----------------------------
def authenticate_drive():
    print("Authenticating Google Drive API...")
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=creds)
    print("Drive authentication completed.")
    return drive_service

# -----------------------------
# Posted JSON Handling
# -----------------------------
def load_posted():
    print("Loading posted.json...")
    if os.path.exists("posted.json"):
        with open("posted.json", "r") as f:
            data = set(json.load(f))
            print(f"Loaded posted.json, {len(data)} files already posted.")
            return data
    print("No posted.json found, starting fresh.")
    return set()

def save_posted(posted):
    with open("posted.json", "w") as f:
        json.dump(list(posted), f)
    print("Updated posted.json.")

# -----------------------------
# Fallback Captions
# -----------------------------
FALLBACK_CAPTIONS = [
    "Keep grinding 💪 Success is coming! #Motivation #Success #Grind",
    "Your only limit is you 🚀 #Inspiration #DailyMotivation #DreamBig",
    "Don’t stop until you’re proud 🔥 #NeverGiveUp #StayStrong",
    "Every day is a new chance to grow 🌱 #Mindset #Positivity",
    "Small steps lead to big results 🏆 #Focus #Discipline",
] * 20  # total 100

def get_random_caption():
    return random.choice(FALLBACK_CAPTIONS)

# -----------------------------
# Drive: Get files from folder
# -----------------------------
def get_files_in_folder(drive_service, folder_id):
    print(f"Fetching files from folder {folder_id}...")
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])
    print(f"Found {len(files)} files in the folder.")
    return files

# -----------------------------
# Download from Drive
# -----------------------------
def download_file(drive_service, file_id, filename):
    from googleapiclient.http import MediaIoBaseDownload
    import io
    print(f"Downloading file {file_id}...")
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    print(f"Downloaded {filename}.")
    return True

# -----------------------------
# Video Processing
# -----------------------------
def process_video(input_file, output_file):
    print(f"Processing video {input_file}...")
    cmd = [
        "ffmpeg", "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac", "-b:a", "128k",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        output_file, "-y"
    ]
    subprocess.run(cmd, check=True)
    print(f"Processed video saved as {output_file}.")

# -----------------------------
# YouTube Upload
# -----------------------------
def upload_to_youtube(youtube, video_file, title, description):
    print(f"Uploading {video_file} to YouTube...")
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["motivation", "inspiration", "shorts", "success", "discipline"],
            "categoryId": "22"  # People & Blogs
        },
        "status": {"privacyStatus": "public"}
    }
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print(f"Upload completed: {response.get('id')}")
    return response

# -----------------------------
# Main
# -----------------------------
def main():
    youtube = authenticate_youtube()
    drive_service = authenticate_drive()
    posted = load_posted()
    folder_id = os.getenv("DRIVE_FOLDER_ID").strip()

    files = get_files_in_folder(drive_service, folder_id)
    for file in files:
        file_id = file["id"]
        file_name = file["name"]

        if file_id in posted:
            continue

        if not file_name.lower().endswith(".mp4"):
            print(f"Skipping {file_name}, not an mp4 video.")
            continue

        download_file(drive_service, file_id, file_name)
        processed_file = f"processed_{file_name}"
        process_video(file_name, processed_file)

        # Caption generation
        try:
            caption = generate_caption(file_name)
            if not caption or caption.strip() == "":
                raise Exception("Empty caption")
        except Exception as e:
            print("Caption generation failed, using fallback.", e)
            caption = get_random_caption()

        title = caption[:100]
        description = caption
        upload_to_youtube(youtube, processed_file, title, description)

        posted.add(file_id)
        save_posted(posted)

        # Cleanup
        os.remove(file_name)
        os.remove(processed_file)

        break  # Post only one per run

if __name__ == "__main__":
    main()
