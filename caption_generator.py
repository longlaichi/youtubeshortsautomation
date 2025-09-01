from transformers import pipeline

# Load lightweight free model
generator = pipeline("text-generation", model="gpt2", tokenizer="gpt2")

def generate_captions(first_3_seconds_text: str = ""):
    """
    Generate SEO title, caption, hashtags, and pro tip for a video
    using only the first 3 seconds' text content.
    """

    prompt = f"""
    You are a YouTube SEO expert.
    Generate:
    1. A short catchy TITLE for the video (with a hook).
    2. A motivating CAPTION for YouTube Shorts (2–3 lines).
    3. 8–10 relevant HASHTAGS (mix trending + motivational).
    4. A PRO TIP (1 line) for viewers.

    First 3 seconds of the clip: {first_3_seconds_text}
    """

    response = generator(prompt, max_length=180, num_return_sequences=1, do_sample=True, temperature=0.9)
    text = response[0]["generated_text"]

    # Simple parsing
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    title = lines[0] if len(lines) > 0 else "Motivational Video"
    caption = " ".join(lines[1:3]) if len(lines) > 2 else "Stay motivated!"
    hashtags = "#motivation #success #life"
    pro_tip = "Consistency beats talent."

    return {
        "title": title,
        "caption": caption,
        "hashtags": hashtags,
        "pro_tip": pro_tip
    }
