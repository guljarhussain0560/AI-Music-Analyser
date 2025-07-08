from fastapi import FastAPI
from app.api.routes import process 

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "AI Lyrics Replacer is running!"}

app.include_router(process.router, prefix="/process")