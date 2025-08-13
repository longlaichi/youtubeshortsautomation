import json
import os

POSTED_FILE = "posted.json"

def load_posted():
    """Load the list of already posted reels."""
    if not os.path.exists(POSTED_FILE):
        return []
    with open(POSTED_FILE, "r") as f:
        return json.load(f)

def save_posted(posted_list):
    """Save the list of posted reels."""
    with open(POSTED_FILE, "w") as f:
        json.dump(posted_list, f)
