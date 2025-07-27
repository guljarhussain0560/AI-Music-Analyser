from fastapi import FastAPI
from app.api.routes import auth, process 

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "AI Lyrics Replacer is running!"}

# Include the authentication router
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

app.include_router(process.router, prefix="/process")