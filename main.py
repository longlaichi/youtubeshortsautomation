import os
import base64
import json
import pickle
import tempfile
import io
import re
from pydub import AudioSegment
import speech_recognition as sr
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
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
    token_bytes = base64.b64decode(token_b64)
    creds = pickle.loads(token_bytes)
    return build("youtube", "v3", credentials=creds)

# -----------------------------
# Get next unposted video
# -----------------------------
def get_next_drive_file(drive_service, folder_id, posted_log="posted_videos.txt"):
    posted = set()
    if os.path.exists(posted_log):
        with open(posted_log, "r") as f:
            posted = set(line.strip() for line in f.readlines())

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

# -----------------------------
# Download file from Drive
# -----------------------------
def download_file(drive_service, file_id, filename):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.close()

# -----------------------------
# Extract first 3 seconds audio → text
# -----------------------------
def extract_first_3s_text(video_path):
    audio = AudioSegment.from_file(video_path)
    first_3s = audio[:3000]  # first 3 seconds
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

    folder_id = os.environ["DRIVE_FOLDER_IDS"]
    file = get_next_drive_file(drive_service, folder_id)

    if not file:
        print("No new videos found.")
        return

    video_name = file["name"]
    video_path = f"/tmp/{video_name}"

    # Download video
    download_file(drive_service, file["id"], video_path)

    # Extract text from first 3 seconds
    first_3s_text = extract_first_3s_text(video_path)

    # Generate captions from first 3 seconds only
    meta = generate_captions(first_3s_text)

    # Upload to YouTube
    upload_to_youtube(youtube_service, video_path, meta)

    # Mark as posted
    with open("posted_videos.txt", "a") as f:
        f.write(file["id"] + "\n")

    # Cleanup
    os.remove(video_path)
    print(f"✅ Uploaded {video_name} successfully!")

if __name__ == "__main__":
    main()
