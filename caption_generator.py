import random

def generate_caption(file_title: str) -> str:
    # Extract base name (without extension)
    base_name = file_title.rsplit(".", 1)[0]

    # Anime-specific caption ideas
    captions = [
        "Relive this epic anime moment 🎥🔥",
        "When anime hits different 🎬💖",
        "One scene, infinite feels 😭❤️",
        "Anime vibes all day 🌙⭐",
        "Ultra HD anime perfection 🎯",
        "Get inspired by this incredible anime shot ✨🎞️",
        "Feel the emotions, live the story 🌸💫",
        "Anime magic in motion 🌀🎥",
    ]

    # High-reach anime hashtags
    hashtags = (
        "#anime #animeedit #animereels #weeb #otaku "
        "#animemoments #manga #japan #animeaesthetic "
        "#amv #animelife #animefan #animelove #weeblife "
        "#animeworld #otakulife #animecommunity #foryou "
	"#getviral #boostreach #boostfollower #lust"
        "#fyp #viralreels #trend #ultrahd #reelsinstagram"
    )

    # Combine random caption + hashtags
    return f"{random.choice(captions)}\n\n{hashtags}"
