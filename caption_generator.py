import random
import json
import os

# -----------------------------
# Caption & Hashtag Pool
# -----------------------------
CAPTION_POOL = [
    "Never give up on your dreams. Hard work pays off.",
    "Success comes to those who stay focused and consistent.",
    "Discipline is the bridge between goals and accomplishment.",
    "Every day is a new opportunity to improve yourself.",
    "Small steps every day lead to big results in life.",
    "Push yourself, because no one else is going to do it for you.",
    "Consistency beats talent every single time.",
    "Your only limit is the one you set for yourself.",
    "Dream big, work hard, stay focused, and surround yourself with good people.",
    "Believe in yourself and all that you are.",
    "Opportunities don't happen, you create them.",
    "Focus on your goals, not your fears.",
    "Hustle in silence and let your success make the noise.",
    "Success is the sum of small efforts repeated day in and day out.",
    "You are stronger than you think.",
    "The harder you work for something, the greater you'll feel when you achieve it.",
    "Do something today that your future self will thank you for.",
    "Don’t watch the clock; do what it does. Keep going.",
    "Dream it. Wish it. Do it.",
    "Great things never come from comfort zones.",
    "Success doesn’t just find you. You have to go out and get it.",
    "Push harder than yesterday if you want a different tomorrow.",
    "Don’t wait for opportunity. Create it.",
    "Believe you can and you’re halfway there.",
    "The key to success is to start before you are ready.",
    "Work hard in silence, let success make the noise.",
    "Don’t stop when you’re tired. Stop when you’re done.",
    "Success is not for the lazy.",
    "Your future is created by what you do today, not tomorrow.",
    "Make each day your masterpiece.",
    "Don’t wait. The time will never be just right.",
    "Focus on being productive instead of busy.",
    "Your limitation—it’s only your imagination.",
    "Sometimes later becomes never. Do it now.",
    "Success is the best revenge for failure.",
    "Don’t be afraid to give up the good to go for the great.",
    "Opportunities are usually disguised as hard work.",
    "Stop wishing, start doing.",
    "Don’t let small minds convince you that your dreams are too big.",
    "The way to get started is to quit talking and begin doing.",
    "Action is the foundational key to all success.",
    "Little things make big days.",
    "Stay patient and trust your journey.",
    "Dreams don’t work unless you do.",
    "The secret of getting ahead is getting started.",
    "Great things take time.",
    "Motivation gets you going, discipline keeps you growing.",
    "Success is no accident. It’s hard work, perseverance, learning, studying, sacrifice, and most of all, love of what you are doing.",
    "Don’t limit your challenges, challenge your limits.",
    "Be so good they can’t ignore you.",
    "Work until your idols become your rivals.",
]

HASHTAGS_POOL = [
    "#motivation", "#success", "#shorts", "#inspiration", "#dailygrind", "#mindset",
    "#selfimprovement", "#discipline", "#goals", "#productivity", "#hustle",
    "#nevergiveup", "#growth", "#focus", "#achievement", "#positivity", "#determination",
    "#lifeadvice", "#personaldevelopment", "#dreambig"
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