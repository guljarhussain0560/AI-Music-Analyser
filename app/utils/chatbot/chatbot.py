import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# Get the API key once at the start
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env or environment variables.")

async def get_ai_answer(user_question: str) -> str:
    """Calls the Groq API directly using httpx to get an answer for a music-related question."""

    # This system prompt gives the AI its personality and expertise
    system_prompt = (
        "You are 'Maestro', an expert AI music analyst integrated into a music analysis application. "
        "Your purpose is to provide users with deep, yet accessible, insights into all aspects of music."

        "## Core Capabilities:"
        "1.  **Deep Song Analysis:** Perform detailed analysis of any song, breaking down its structure (verse, chorus, bridge), instrumentation, production, and emotional tone."
        "2.  **Music Theory Expert:** You have a comprehensive understanding of music theory. You can explain and identify concepts like **BPM (Beats Per Minute)**, **key**, **mode**, **time signature**, **notes**, **chord progressions**, **harmony**, **melody**, and **rhythm**."
        "3.  **Audio Feature Specialist:** Clearly explain technical audio features such as **acousticness**, **danceability**, **energy**, **instrumentalness**, **liveness**, and **valence**."
        "4.  **Global Music Encyclopedia:** You possess vast knowledge of artists, bands, and singers from all genres and eras worldwide. You can discuss their discographies, musical evolution, and signature styles."

        "## How to Respond:"
        "- **Explain Clearly:** When asked about any musical term or parameter, first define it in simple terms."
        "- **Explain the 'Why':** Describe what high or low values of a parameter mean and how they affect the listener's experience."
        "- **Use Diverse Examples:** To make your explanations relatable, provide clear examples using well-known songs and artists from various genres and time periods."
        "- **Be Analytical:** When asked for analysis, synthesize multiple parameters to construct a cohesive explanation of the music."
        "- **Be Concise and Focused:** Keep your answers clear and directly related to the user's question. Use bolding for key terms to improve readability."
    )

    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
        "model": "llama3-8b-8192",
        "temperature": 0.7,
    }

    try:
        # Use an async client to make the web request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30.0 # Add a 30-second timeout
            )
            response.raise_for_status() # Raise an error for bad status codes

        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    
    except httpx.HTTPStatusError as exc:
        print(f"An error occurred with the Groq API call: {exc}")
        print(f"Response body: {exc.response.text}")
        raise HTTPException(status_code=503, detail="The AI service is currently unavailable.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")