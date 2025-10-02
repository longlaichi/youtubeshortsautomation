import json
import os

POSTED_FILE = "posted.json"

def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return json.load(f)
    return []

def save_posted(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(posted, f, indent=2)
