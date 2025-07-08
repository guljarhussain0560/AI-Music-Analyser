from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables
print("🔧 Loading .env file...")
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found. Please check your .env file.")

# Initialize Groq client
print("🤖 Initializing Groq client...")
client = Groq(api_key=GROQ_API_KEY)

def rewrite_lyric_line(line: str, user_prompt: str) -> str:
    """
    Rewrites a single lyric line using Groq, following Indian poetic theme strictly.
    """
    prompt = f"""
You are a professional Indian lyricist. Rewrite the following English lyric line to reflect an Indian cultural theme and poetic tone. Follow these strict rules:

- Use poetic and culturally rich language that fits the Indian theme.
- Preserve rhythm and syllable structure.
- Do NOT return multiple options or explanations.
- DO NOT include quotes or say “Here’s”.
- Only return the rewritten line.

Instruction: {user_prompt}

Original: {line}

Rewritten:
""".strip()

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            max_completion_tokens=100,
            top_p=1.0,
            stream=False
        )
        result = response.choices[0].message.content.strip()

        # Filter clean output
        for l in result.splitlines():
            l = l.strip().strip('"')
            if l and not any(bad in l.lower() for bad in [
                "here's", "option", "alternatively", "let me know", "suggest", "you could"
            ]):
                return l
        return result.strip().strip('"')
    except Exception as e:
        print(f"❌ Error rewriting line: {e}")
        return line


def rewrite_lyrics_with_timestamps(segments: list[dict], user_prompt: str, language: str = "en") -> list[dict]:
    """
    Rewrite lyric segments using Groq while preserving timestamps.

    Args:
        segments: List of dicts with keys 'start', 'end', 'text'
        user_prompt: Prompt instruction to apply to each lyric line
        language: Detected language code ("en", "hi", "ur", etc.)

    Returns:
        List of dicts with keys: 'start', 'end', 'text'
    """
    rewritten = []

    for seg in segments:
        original_text = seg.get("text", "").strip()
        start = seg.get("start")
        end = seg.get("end")

        if not original_text or start is None or end is None:
            rewritten.append({"start": start or 0.0, "end": end or (start or 0.0 + 2.0), "text": ""})
            continue

        try:
            new_text = rewrite_lyric_line(original_text, user_prompt, language)
        except Exception:
            new_text = original_text

        rewritten.append({"start": start, "end": end, "text": new_text})

    return rewritten

