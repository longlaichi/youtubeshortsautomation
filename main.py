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
import re

# -----------------------------
# YouTube Authentication using pickle
# -----------------------------
def authenticate_youtube():
    print("Authenticating YouTube...")
    with open("youtube_token.pkl", "rb") as f:
        creds = pickle.load(f)
    youtube = build("youtube", "v3", credentials=creds)
    print("YouTube authentication completed.")
    return youtube

# -----------------------------
# Posted JSON Handling
# -----------------------------
def load_posted():
    print("Loading posted.json...")
    if os.path.exists("posted.json"):
        with open("posted.json", "r") as f:
            posted = set(json.load(f))
            print(f"Loaded posted.json, {len(posted)} files already posted.")
            return posted
    print("No posted.json found, starting fresh.")
    return set()

def save_posted(posted):
    with open("posted.json", "w") as f:
        json.dump(list(posted), f)
    print("posted.json updated.")

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
# Public Google Drive Folder Scraping
# -----------------------------
def get_file_ids_from_public_folder(folder_url):
    print(f"Fetching files from folder {folder_url}...")
    r = requests.get(folder_url)
    if r.status_code != 200:
        print("Failed to access folder URL.")
        return []
    
    soup = BeautifulSoup(r.text, "html.parser")
    file_ids = set()
    for a in soup.find_all("a", href=True):
        href = a['href']
        if "/file/d/" in href:
            fid = href.split("/file/d/")[1].split("/")[0]
            file_ids.add(fid)
        elif "id=" in href:
            fid = href.split("id=")[1].split("&")[0]
            file_ids.add(fid)
    print(f"Found {len(file_ids)} files in the folder.")
    return list(file_ids)

# -----------------------------
# Download & Process
# -----------------------------
def download_from_gdrive(file_id, filename):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        print(f"Downloaded {filename}")
        return True
    print(f"Failed to download {file_id}")
    return False

def process_video(input_file, output_file):
    cmd = [
        "ffmpeg", "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac", "-b:a", "128k",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        output_file, "-y"
    ]
    subprocess.run(cmd, check=True)
    print(f"Processed {output_file}")

# -----------------------------
# Upload to YouTube
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
    print(f"Uploaded: {video_file}")
    return response

# -----------------------------
# Main Logic
# -----------------------------
def main():
    youtube = authenticate_youtube()
    posted = load_posted()

    folder_url = "https://drive.google.com/drive/folders/1svFyekf17TKmZ28gtwZqiT5M9I3HbD01"
    file_ids = get_file_ids_from_public_folder(folder_url)

    for file_id in file_ids:
        if file_id in posted:
            continue

        filename = f"{file_id}.mp4"
        if not download_from_gdrive(file_id, filename):
            continue

        if not filename.endswith(".mp4"):
            print(f"Skipping {filename}, not a video.")
            continue

        processed_file = f"processed_{filename}"
        process_video(filename, processed_file)

        # Caption
        try:
            caption = generate_caption(filename)
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

        os.remove(filename)
        os.remove(processed_file)
        break  # post only one per run

if __name__ == "__main__":
    main()
