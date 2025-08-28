import random

FALLBACK_CAPTIONS = [
    "Keep pushing forward! 💪 #Motivation #Success #Grind",
    "Dream big and work hard 🚀 #Inspiration #DailyMotivation #DreamBig",
    "Don’t stop until you’re proud 🔥 #NeverGiveUp #StayStrong",
    "Every day is a new opportunity 🌱 #Mindset #Positivity #Growth",
    "Small steps lead to big victories 🏆 #Focus #Discipline #Consistency",
    "Your only limit is you 💫 #Believe #SelfGrowth #Motivation",
    "Stay positive, work hard, make it happen 💥 #SuccessMindset #Hustle",
    "Push yourself, because no one else will 💪 #Grind #MotivationDaily",
    "Turn your dreams into reality 🌟 #Inspiration #HardWorkPaysOff",
    "Consistency is key 🔑 #Discipline #Growth #DailyMotivation"
]

def generate_caption(file_name=None):
    """
    Always returns a random motivational caption with hashtags.
    Ignores file_name entirely.
    """
    return random.choice(FALLBACK_CAPTIONS)
