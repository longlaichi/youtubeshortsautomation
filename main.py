import os
import json
import subprocess
import cv2
from pydrive2.auth import GoogleAuth, GoogleDrive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from caption_generator import generate_caption
from record_keeper import load_posted, save_posted
from helpers import download_next_reel, cleanup_downloaded

# -------------------------------
# Google Drive Authentication
# -------------------------------
def authenticate_drive():
    from oauth2client.service_account import ServiceAccountCredentials
    creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
    scope = ["https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    return GoogleDrive(gauth)

# -------------------------------
# YouTube Authentication
# -------------------------------
def authenticate_youtube():
    with open("session.json", "r") as f:
        creds_data = json.load(f)

    from google.oauth2.credentials import Credentials
    creds = Credentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"]
    )
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

# -------------------------------
# FFmpeg Ultra HD Preprocess
# -------------------------------
def ffmpeg_ultrahd(input_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "slow",
        "-profile:v", "high",
        "-level", "4.1",
        "-b:v", "20M",
        "-maxrate", "22M",
        "-bufsize", "22M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        output_path
    ]
    print("Running FFmpeg Ultra HD processing...")
    subprocess.run(cmd, check=True)
    print(f"✅ Finished processing: {output_path}")

# -------------------------------
# Shorts Format Check
# -------------------------------
def is_short_format(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps > 0 else 0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()

    if duration <= 60 and height > width and height >= 720:
        return True
    return False

# -------------------------------
# Upload to YouTube
# -------------------------------
def upload_to_youtube(youtube, video_path, title, description):
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["motivation", "money", "shorts", "success", "viral", "inspiration"],
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
    print(f"✅ Uploaded: {title} (videoId: {response['id']})")
    return response['id']

# -------------------------------
# Main Workflow
# -------------------------------
def main():
    print("Authenticating with Google Drive...")
    drive = authenticate_drive()

    print("Authenticating with YouTube...")
    youtube = authenticate_youtube()

    folder_ids = os.environ["DRIVE_FOLDER_IDS"].split(",")
    posted_ids = load_posted()

    print("Looking for next video to upload...")
    file_id, local_path, file_title = download_next_reel(drive, folder_ids, posted_ids)
    if not file_id:
        print("All videos already posted! ✅")
        return

    if not is_short_format(local_path):
        print("❌ Video not in Shorts format, skipping...")
        cleanup_downloaded(local_path)
        return

    processed_path = local_path.rsplit(".", 1)[0] + "_ultrahd.mp4"
    ffmpeg_ultrahd(local_path, processed_path)

    print("Generating AI caption...")
    caption = generate_caption(file_title)

    print(f"Uploading to YouTube: {file_title}")
    video_id = upload_to_youtube(youtube, processed_path, file_title, caption)

    posted_ids.append(file_id)
    save_posted(posted_ids)

    cleanup_downloaded(local_path)
    cleanup_downloaded(processed_path)

    print("✅ Workflow complete.")

if __name__ == "__main__":
    main()
