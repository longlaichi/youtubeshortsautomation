import os
import json
import random
import requests
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import openai
from caption_generator import generate_caption

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load YouTube token.pkl
def authenticate_youtube():
    with open("youtube_token.pkl", "rb") as f:
        creds = pickle.load(f)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

# Load posted.json to avoid reuploads
def load_posted():
    if os.path.exists("posted.json"):
        with open("posted.json", "r") as f:
            return set(json.load(f))
    return set()

def save_posted(posted):
    with open("posted.json", "w") as f:
        json.dump(list(posted), f)

# Fallback captions
FALLBACK_CAPTIONS = [
    "Keep grinding 💪 Success is coming! #Motivation #Success #Grind",
    "Your only limit is you 🚀 #Inspiration #DailyMotivation #DreamBig",
    "Don’t stop until you’re proud 🔥 #NeverGiveUp #StayStrong",
    "Every day is a new chance to grow 🌱 #Mindset #Positivity",
    "Small steps lead to big results 🏆 #Focus #Discipline",
] * 20  # total 100

# Pick random fallback caption
def get_random_caption():
    return random.choice(FALLBACK_CAPTIONS)

# Download file from public GDrive link
def download_from_gdrive(file_id, filename):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return True
    return False

# Process video with ffmpeg
def process_video(input_file, output_file):
    cmd = [
        "ffmpeg", "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac", "-b:a", "128k",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        output_file, "-y"
    ]
    subprocess.run(cmd, check=True)

# Upload to YouTube Shorts
def upload_to_youtube(youtube, video_file, title, description):
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
    return response

def main():
    youtube = authenticate_youtube()
    posted = load_posted()
    folder_ids = os.getenv("DRIVE_FOLDER_IDS").split(",")

    for folder_id in folder_ids:
        # For simplicity: assume file IDs are in DRIVE_FOLDER_IDS (public links pre-collected)
        file_id = folder_id.strip()
        if file_id in posted:
            continue

        # Check extension first
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

        # Clean up
        os.remove(filename)
        os.remove(processed_file)
        break  # post only one per run

if __name__ == "__main__":
    main()