import os
import json
import subprocess
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from instagrapi import Client
from caption_generator import generate_caption
from record_keeper import load_posted, save_posted
from helpers import download_next_reel, cleanup_downloaded

# Import IG session from session.py
from session import IG_SESSION_PATH  # session.py should define: IG_SESSION_PATH = "session.json"

def authenticate_drive():
    from oauth2client.service_account import ServiceAccountCredentials
    creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
    scope = ["https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gauth = GoogleAuth()
    gauth.credentials = credentials
    return GoogleDrive(gauth)

def ffmpeg_ultrahd(input_path, output_path):
    """
    Convert 60 fps video to Instagram-friendly Ultra HD (1080x1920, 30fps)
    keeping the highest quality possible for Instagram.
    """
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-r", "30",                  # convert 60fps -> 30fps
        "-c:v", "libx264",
        "-preset", "slow",           # best balance speed/quality in GitHub Actions
        "-profile:v", "high",
        "-level", "4.1",
        "-b:v", "20M",               # maximum video bitrate
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


def main():
    print("Authenticating with Google Drive...")
    drive = authenticate_drive()

    print("Authenticating with Instagram (using session.py)...")
    cl = Client()
    if not os.path.exists(IG_SESSION_PATH):
        raise FileNotFoundError(f"{IG_SESSION_PATH} not found. Please login and save session first.")

    cl.load_settings(IG_SESSION_PATH)
    cl.get_timeline_feed()  # validate session
    print("✅ IG session OK.")

    folder_ids = os.environ["DRIVE_FOLDER_IDS"].split(",")
    posted_ids = load_posted()

    print("Looking for next reel to upload...")
    file_id, local_path, file_title = download_next_reel(drive, folder_ids, posted_ids)
    if not file_id:
        print("All reels already posted! ✅")
        return

    # Preprocess with FFmpeg to Ultra HD
    processed_path = local_path.rsplit(".", 1)[0] + "_ultrahd.mp4"
    ffmpeg_ultrahd(local_path, processed_path)

    print("Generating caption...")
    caption = generate_caption(file_title)

    print(f"Uploading to Instagram: {file_title}")
    cl.clip_upload(processed_path, caption)

    print("Updating history (posted.json)...")
    posted_ids.append(file_id)
    save_posted(posted_ids)

    print("Cleaning up local files...")
    cleanup_downloaded(local_path)
    cleanup_downloaded(processed_path)

    if os.path.exists("posted.json"):
        print("✅ posted.json saved.")
    else:
        print("⚠️ posted.json not found after save!")

    print("✅ Done.")

if __name__ == "__main__":
    main()
