import json
import os

POSTED_FILE = "posted.json"

def load_posted():
    """
    Load the list of already posted reel IDs from posted.json.
    Returns an empty list if the file doesn't exist.
    """
    if not os.path.exists(POSTED_FILE):
        return []
    with open(POSTED_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_posted(posted_list):
    """
    Save the list of posted reel IDs to posted.json
    """
    with open(POSTED_FILE, "w") as f:
        json.dump(posted_list, f, indent=2)
