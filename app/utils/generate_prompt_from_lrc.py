# generate_prompt_from_lrc.py

import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

# Create Groq client
client = Groq(api_key=GROQ_API_KEY)


def generate_music_prompt_from_lrc(lrc_string: str) -> str:
    """
    Generate a vivid music prompt from LRC lyrics using Groq API.
    """
    system_prompt = """
    You are a poetic music producer assistant.

    You will be given a set of lyrics in LRC format (timestamped lines). Your task is to analyze the lyrical content and convert it into a vivid, emotional, and descriptive prompt suitable for an AI music generation model (such as MusicGen).

    Your music prompt should reflect:
    - The **genre or style** implied by the lyrics (e.g., classical, hip hop, lo-fi, cinematic, electronic, folk, etc.)
    - The **overall mood** or emotion (e.g., melancholic, uplifting, suspenseful, romantic, triumphant, etc.)
    - Relevant **instruments or sound palette** (e.g., acoustic guitar, synth pads, strings, drums, piano, etc.)
    - Any **setting or cultural vibe** (e.g., modern city, ancient temple, outer space, a forest night, a festival crowd, etc.) if inferred from the lyrics

    Your output must be:
    - Maintained in a single paragraph.
    - Rich in descriptive language.
    - All content / important details should be included.
    

    Generate only the music prompt.
    """

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": lrc_string}
            ],
            temperature=1.0,
            max_completion_tokens=128,
            top_p=1.0,
            stream=False
        )
        prompt = response.choices[0].message.content.strip()
        print(f"\n🎵 Generated Music Prompt:\n{prompt}")
        return prompt

    except Exception as e:
        print(f"❌ Failed to generate prompt: {e}")
        return ""
