from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_caption(file_title: str) -> str:
    """
    Generate an engaging motivational caption with relevant hashtags for YouTube Shorts.
    Handles numbered file titles automatically.
    """
    # If file title is numeric, provide default context
    if file_title.replace(".mp4", "").isnumeric():
        video_context = "This is a motivational short about success, money-making, and inspiration."
    else:
        video_context = file_title

    prompt = f"""
    Generate a catchy, motivational caption for a YouTube Shorts video.
    Video context: "{video_context}"
    Include 10-15 highly relevant hashtags at the end for maximum reach on YouTube Shorts.
    Target audience: 12-25 years old.
    Keep it engaging, inspiring, and not too long.
    Format: Caption text, then hashtags on a new line.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=120
        )
        caption = response.choices[0].message.content.strip()
        return caption
    except Exception as e:
        print(f"❌ Error generating caption: {e}")
        fallback_caption = f"Watch this amazing short: {video_context}\n#motivation #money #success #shorts #viral #inspiration"
        return fallback_caption
