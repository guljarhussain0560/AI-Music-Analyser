import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import your application's route modules
from app.api.routes import auth, get_analytics, process
from app.api.routes.chatbot import bot

# Load environment variables from a .env file
load_dotenv()

app = FastAPI()


allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "*")
allowed_origins = allowed_origins_str.split(',') if allowed_origins_str else []

# Add the CORSMiddleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# -------------------------


@app.get("/")
def read_root():
    return {"msg": "AI Lyrics Replacer is running!"}

# Include your application's routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(process.router, prefix="/api/process" , tags=["Processing"])
app.include_router(get_analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(bot.router, prefix="/api/chat", tags=["Chatbot"])

