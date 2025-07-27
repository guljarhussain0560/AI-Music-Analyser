from groq import Groq
from dotenv import load_dotenv
import os

# Load .env file
print("🔧 Loading .env file...")
load_dotenv()

# Get GROQ API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print(f"🔑 GROQ_API_KEY loaded: {GROQ_API_KEY is not None}")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found. Please check your .env file or environment variables.")

# Initialize Groq client
print("🤖 Initializing Groq client...")
client = Groq(api_key=GROQ_API_KEY)




def rewrite_lyrics_with_timestamps(lrc_string: str, language: str, duration: float, user_prompt: str) -> str:
    """
    Rewrite the entire lyrics (LRC string) using Groq AI in one go, not segment-wise.

    Args:
        lrc_string: The full LRC lyrics as a string (with timestamps).
        language: The language of the lyrics (e.g., 'en').
        duration: The total duration of the song in seconds.
        user_prompt: Prompt instruction to apply to the entire lyrics.

    Returns:
        The rewritten LRC string (with timestamps preserved if possible).
    """
    print(f"📝 Rewriting entire lyrics with Groq AI. Language: {language}, Duration: {duration}, Prompt: {user_prompt}")
    print(f"[DEBUG] Original LRC:\n{lrc_string}")

    system_prompt = f"""
You are a creative and poetic songwriting assistant. Your task is to rewrite the following song lyrics in LRC format, based on the user's instruction.
Keep the timestamps and structure of the LRC file unchanged.
Rewrite the lyrics in the same language: {language}.
The total song duration is {duration} seconds.
Apply the following user instruction to the entire lyrics: {user_prompt}
Only return the new LRC content, do not add any explanation or extra text.
"""

    print(f"[DEBUG] System prompt sent to Groq:\n{system_prompt.strip()}")

    try:
        print("🚀 Sending full lyrics to Groq API...")
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": lrc_string}
            ],
            temperature=1.0,
            max_completion_tokens=2048,
            top_p=1.0,
            stream=False
        )
        print("✅ Received response from Groq API.")
        rewritten_lrc = response.choices[0].message.content.strip()
        print(f"✅ Rewritten LRC:\n{rewritten_lrc}\n")
        return rewritten_lrc
    except Exception as e:
        print(f"❌ Error calling Groq for full lyrics: {e}")
        raise e
