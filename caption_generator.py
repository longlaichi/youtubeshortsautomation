import random

def generate_caption(file_title: str) -> str:
    # Extract base name (without extension)
    base_name = file_title.rsplit(".", 1)[0]

    # Anime-specific caption ideas
    captions = [
        f"{base_name} 🌸✨",
        f"Relive this epic anime moment 🎥🔥",
        f"When anime hits different 🎬💖",
        f"{base_name} — One scene, infinite feels 😭❤️",
        f"Anime vibes all day 🌙⭐",
        f"{base_name} — Ultra HD anime perfection 🎯"
    ]

    # High-reach anime hashtags
    hashtags = (
        "#anime #animeedit #animereels #weeb #otaku "
        "#animemoments #manga #japan #animeaesthetic "
        "#amv #animelife #animefan #animelove #weeblife "
        "#animeworld #otakulife #animecommunity #foryou "
        "#fyp #viralreels #trend #ultrahd #reelsinstagram"
    )

    # Combine random caption + hashtags
    return f"{random.choice(captions)}\n\n{hashtags}"
