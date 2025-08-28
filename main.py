import os
import json
import random
import requests
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
from caption_generator import generate_caption
from bs4 import BeautifulSoup

# Load OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_api_key

# -----------------------------
# YouTube Authentication using pickle
# -----------------------------
def authenticate_youtube():
    with open("youtube_token.pkl", "rb") as f:
        creds = pickle.load(f)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

# -----------------------------
# Posted JSON Handling
# -----------------------------
def load_posted():
    if os.path.exists("posted.json"):
        with open("posted.json", "r") as f:
            return set(json.load(f))
    return set()

def save_posted(posted):
    with open("posted.json", "w") as f:
        json.dump(list(posted), f)

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
# Google Drive Helpers
# -----------------------------
def get_file_ids_in_folder(folder_id):
    """
    Fetch all file IDs from a public Google Drive folder
    """
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    r = requests.get(folder_url)
    if r.status_code != 200:
        print(f"Could not fetch folder {folder_id}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    file_ids = set()

    # Find all links containing "id=" which are likely files
    for a in soup.find_all("a", href=True):
        href = a['href']
        if "/file/d/" in href:
            fid = href.split("/file/d/")[1].split("/")[0]
            file_ids.add(fid)
        elif "id=" in href:
            fid = href.split("id=")[1].split("&")[0]
            file_ids.add(fid)

    return list(file_ids)

def download_from_gdrive(file_id, filename):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return True
    return False

# -----------------------------
# Video Processing
# -----------------------------
def process_video(input_file, output_file):
    cmd = [
        "ffmpeg", "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac", "-b:a", "128k",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        output_file, "-y"
    ]
    subprocess.run(cmd, check=True)

# -----------------------------
# YouTube Upload
# -----------------------------
def upload_to_youtube(youtube, video_file, title, description):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["motivation", "inspiration", "shorts", "success", "discipline"],
            "categoryId": "22"
        },
        "status": {"privacyStatus": "public"}
    }
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response

# -----------------------------
# Main Logic
# -----------------------------
def main():
    youtube = authenticate_youtube()
    posted = load_posted()
    folder_ids = os.getenv("DRIVE_FOLDER_IDS").split(",")

    for folder_id in folder_ids:
        folder_id = folder_id.strip()
        file_ids = get_file_ids_in_folder(folder_id)

        for file_id in file_ids:
            if file_id in posted:
                continue

            filename = f"{file_id}.mp4"

            if not download_from_gdrive(file_id, filename):
                print(f"Skipping {file_id}, could not download.")
                continue

            if not filename.endswith(".mp4"):
                print(f"Skipping {file_id}, not a video.")
                continue

            processed_file = f"processed_{filename}"
            process_video(filename, processed_file)

            # Try caption generation
            try:
                caption = generate_caption(filename)
                if not caption or caption.strip() == "":
                    raise Exception("Empty caption")
            except Exception as e:
                print("Caption generation failed, using fallback.", e)
                caption = get_random_caption()

            title = caption[:100]  # Shorts title limit
            description = caption

            response = upload_to_youtube(youtube, processed_file, title, description)
            print("Uploaded:", response)

            posted.add(file_id)
            save_posted(posted)

            os.remove(filename)
            os.remove(processed_file)
            break  # Post only one per run

if __name__ == "__main__":
    main()