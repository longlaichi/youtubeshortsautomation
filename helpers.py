import os
import tempfile
from pydrive2.drive import GoogleDrive

def download_next_reel(drive: GoogleDrive, folder_ids: list, posted_ids: list):
    for folder_id in folder_ids:
        file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        file_list.sort(key=lambda x: x['title'])
        for file in file_list:
            if file['id'] not in posted_ids:
                local_path = os.path.join(tempfile.gettempdir(), file['title'])
                print(f"Downloading {file['title']} from folder {folder_id}...")
                file.GetContentFile(local_path)
                print(f"✅ Downloaded to {local_path}")
                return file['id'], local_path, file['title']
    return None, None, None

def cleanup_downloaded(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted local file: {file_path}")
    else:
        print(f"File not found for cleanup: {file_path}")
