import os
import base64
import json
import tempfile
import re
import yt_dlp
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pydub import AudioSegment
import speech_recognition as sr

from caption_generator import generate_captions


# -----------------------------
# Authenticate Google Drive
# -----------------------------
def authenticate_google_drive():
    sa_json = os.environ["GOOGLE_SERVICE_ACCOUNT"]
    creds_dict = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)


# -----------------------------
# Authenticate YouTube
# -----------------------------
def authenticate_youtube():
    token_b64 = os.environ["YOUTUBE_TOKEN_B64"]
    token_json = base64.b64decode(token_b64).decode("utf-8")
    creds_dict = json.loads(token_json)

    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)


# -----------------------------
# Download next unposted video
# -----------------------------
def get_next_drive_file(drive_service, folder_id, posted_log="posted_videos.txt"):
    # Get list of already posted videos
    posted = set()
    if os.path.exists(posted_log):
        with open(posted_log, "r") as f:
            posted = set(line.strip() for line in f.readlines())

    # List files in Drive
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType contains 'video/'",
        orderBy="name",
        fields="files(id, name)"
    ).execute()
    files = results.get("files", [])

    for file in sorted(files, key=lambda x: x["name"]):
        if file["id"] not in posted:
            return file

    return None


def download_file(drive_service, file_id, filename):
    request = drive_service.files().get_media(fileId=file_id)
    fh = open(filename, "wb")
    downloader = MediaFileUpload(fh, mimetype="video/mp4", resumable=True)
    request.execute()


# -----------------------------
# Extract first 3 sec audio → text
# -----------------------------
def extract_first_3s_text(video_path):
    audio = AudioSegment.from_file(video_path)
    first_3s = audio[:3000]  # 3 seconds

    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    first_3s.export(temp_audio.name, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_audio.name) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            text = ""
        except sr.RequestError:
            text = ""

    return text


# -----------------------------
# Upload video to YouTube
# -----------------------------
def upload_to_youtube(youtube_service, video_path, meta):
    body = {
        "snippet": {
            "title": meta["title"],
            "description": f"{meta['caption']}\n\n{meta['hashtags']}\n\nPro Tip: {meta['pro_tip']}",
            "categoryId": "22"
        },
        "status": {"privacyStatus": "public"}
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube_service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = request.execute()
    return response


# -----------------------------
# MAIN
# -----------------------------
def main():
    drive_service = authenticate_google_drive()
    youtube_service = authenticate_youtube()

    folder_id = os.environ["DRIVE_FOLDER_ID"]
    file = get_next_drive_file(drive_service, folder_id)

    if not file:
        print("No new files found.")
        return

    video_name = file["name"]
    video_path = f"/tmp/{video_name}"

    # Download video
    request = drive_service.files().get_media(fileId=file["id"])
    with open(video_path, "wb") as f:
        f.write(request.execute())

    # Extract text from first 3s
    first_3s_text = extract_first_3s_text(video_path)

    # Generate captions
    meta = generate_captions(first_3s_text)

    # Upload to YouTube
    upload_to_youtube(youtube_service, video_path, meta)

    # Mark as posted
    with open("posted_videos.txt", "a") as f:
        f.write(file["id"] + "\n")

    # Cleanup
    os.remove(video_path)
    print(f"Uploaded {video_name} successfully!")


if __name__ == "__main__":
    main()
