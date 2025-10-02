from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import os

from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)

gauth = GoogleAuth()
gauth.credentials = credentials
drive = GoogleDrive(gauth)

folder_id = "<one-folder-id-from-DRIVE_FOLDER_IDS>"
file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

for f in file_list:
    print(f"{f['title']} | {f['id']}")
