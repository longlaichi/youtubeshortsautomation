import json
import os

POSTED_FILE = "posted.json"

# -------------------------------
# Load posted video IDs
# -------------------------------
def load_posted():
    """
    Load the list of already posted video IDs from posted.json.
    Returns an empty list if the file doesn't exist or is corrupted.
    """
    if not os.path.exists(POSTED_FILE):
        return []

    try:
        with open(POSTED_FILE, "r") as f:
            posted_ids = json.load(f)
        return posted_ids
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error loading {POSTED_FILE}: {e}")
        return []

# -------------------------------
# Save posted video IDs
# -------------------------------
def save_posted(posted_ids):
    """
    Save the updated list of posted video IDs to posted.json.
    """
    try:
        with open(POSTED_FILE, "w") as f:
            json.dump(posted_ids, f, indent=2)
        print(f"✅ Updated {POSTED_FILE} with {len(posted_ids)} videos")
    except Exception as e:
        print(f"❌ Error saving {POSTED_FILE}: {e}")
