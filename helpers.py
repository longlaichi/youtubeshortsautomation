import os
from pydrive2.drive import GoogleDrive

def download_next_reel(drive: GoogleDrive, folder_ids: list, posted_ids: list):
    """
    Finds the next unposted reel in the given Google Drive folders and downloads it.
    Returns a tuple: (file_id, local_path, file_title)
    """
    for folder_id in folder_ids:
        file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        # Sort files by title to maintain order
        file_list.sort(key=lambda x: x['title'])
        for file in file_list:
            if file['id'] not in posted_ids:
                local_path = file['title']
                file.GetContentFile(local_path)
                return file['id'], local_path, file['title']
    return None, None, None

def cleanup_downloaded(file_path):
    """Delete a local file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)
