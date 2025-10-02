import random
import json
import os

# -----------------------------
# Short Punchy Caption Pool (2–3 words only)
# -----------------------------
CAPTION_POOL = [
    "Chasing speed", "Born driven", "No limits", "Fuel dreams", "Stay hungry",
    "Keep pushing", "Dream louder", "Built different", "Full throttle", "Never settle",
    "Only forward", "Stay relentless", "Road to win", "Prove them", "Drive harder",
    "Engine roar", "Skyline dreams", "Speed within", "Dream machine", "Peak power",
    "Drive fierce", "Stay unstoppable", "Push harder", "Street king", "Driven soul",
    "No excuses", "Chasing dreams", "On fire", "Stay wild", "Fearless ride",
    "Next level", "Keep moving", "Rise higher", "Stay focused", "Limitless drive"
]

HASHTAGS_POOL = [
    "#motivation", "#success", "#shorts", "#inspiration", "#dailygrind", "#mindset",
    "#selfimprovement", "#discipline", "#goals", "#productivity", "#hustle",
    "#nevergiveup", "#growth", "#focus", "#achievement", "#positivity", "#determination",
    "#lifeadvice", "#personaldevelopment", "#dreambig", "#carreels", "#carlovers",
    "#carsofinstagram", "#supercars", "#luxurycars", "#fastcars", "#viralreels", "#explorepage"
]

USED_CAPTIONS = []

# -----------------------------
# Generate unique caption with SEO hashtags
# -----------------------------
def get_unique_caption():
    global USED_CAPTIONS
    available = [c for c in CAPTION_POOL if c not in USED_CAPTIONS]

    if not available:
        print("⚠️ All captions used! Resetting used captions list.")
        USED_CAPTIONS = available = CAPTION_POOL.copy()

    caption_text = random.choice(available)
    USED_CAPTIONS.append(caption_text)

    hashtags = " ".join(random.sample(HASHTAGS_POOL, k=random.randint(10, 15)))

    return caption_text, hashtags

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    caption, tags = get_unique_caption()
    print("Caption:", caption)
    print("Hashtags:", tags)
