# AI Music Analyser

AI Music Analyser is a powerful, high-performance web API designed to deeply analyze, decompose, and process music tracks. Whether providing a YouTube URL, Spotify link, or directly uploading an audio file, this system leverages advanced machine learning models and heavy **parallel processing** to extract lyrics, separate instrumental stems, and perform deep audio analysis with Librosa.

## 🚀 Key Features

*   **Multi-Source Input:** Seamlessly handles audio from YouTube links, Spotify links, or direct file uploads.
*   **AI Stem Separation:** Uses **Spleeter** to decompose music into 5 distinct stems (Vocals, Bass, Drums, Piano, Other).
*   **Lightning Fast Transcription:** Integrates with **Groq's Whisper** API for rapid, timestamped lyric transcription.
*   **Deep Audio Analytics:** Uses **Librosa** to extract profound musical insights including tempo, pitch, rhythm, harmonics, and dynamic variation for the master track and individual stems (including specialized analysis for Guitar, Violin, and Flute).
*   **Intense Parallel Processing:** Designed for speed. Employs `ThreadPoolExecutor` and `multiprocessing.Pool` to run heavy I/O and CPU-bound tasks concurrently.
*   **Cloud Storage Integration:** Automatically converts processed audio chunks and stems into MP3 and stores them in AWS S3.
*   **Integrated Chatbot:** An LLM-powered chatbot to query data.

---

## 🏗️ System Architecture & Design

The core philosophy behind this system is to execute non-dependent tasks concurrently. Music processing is inherently heavy; by splitting the workflow into multi-threaded and multi-processed pools, processing time is dramatically reduced.

### System Flow Diagram

```text
                              [ Client Request ]
                                      │
                       (Audio URL or File Upload)
                                      ▼
                           [ Audio Acquisition ]
                                      │
                                      ▼
                        [ Phase 1: ThreadPool ]
                                      │
         ┌────────────────────┬───────┴────────┬────────────────────┐
         ▼                    ▼                ▼                    ▼
   [ S3 Uploader ]       [ Librosa ]      [ Spleeter ]      [ Groq Whisper ]
  (Original to S3)    (Master Analytics) (Split 5 Stems)  (Transcribe Lyrics)
         │                    │                │                    │
         │                    │                ▼                    │
         │                    │    [ Phase 2: Parallel ]            │
         │                    │                │                    │
         │                    │       ┌────────┴────────┐           │
         │                    │       ▼                 ▼           │
         │                    │ [ Thread Pool ]  [ Multiprocess ]   │
         │                    │ (Upload Stems)   (Stem Analysis)    │
         │                    │       │                 │           │
         └────────────────────┴───────┼─────────────────┴───────────┘
                                      ▼
                           [ PostgreSQL Database ]
```
### Parallel Processing Breakdown

This project makes extensive use of parallel execution to minimize bottlenecks:

1.  **Phase 1 - Initial Breakdown (`ThreadPoolExecutor`)**:
    *   Once the audio is acquired, a pool of 4 workers is spun up.
    *   **Worker 1:** Uploads the master track to S3.
    *   **Worker 2:** Runs the master `librosa` analytics (tempo, key, chroma, RMS, etc.).
    *   **Worker 3:** Runs `spleeter` to split the audio into 5 stems.
    *   **Worker 4:** Calls Groq's Whisper API to transcribe the track.
2.  **Phase 2 - Stem Uploading (`ThreadPoolExecutor`)**:
    *   Waits for Spleeter to finish.
    *   A pool of 5 workers takes the 5 output `.wav` files, converts them to `.mp3` using `pydub`, and uploads them to S3 concurrently.
3.  **Phase 3 - Deep Stem Analytics (`multiprocessing.Pool`)**:
    *   Unlike I/O tasks, audio analysis is highly CPU-bound.
    *   A multiprocessing pool is created to analyze the 8 instrument profiles (vocal, bass, drums, piano, other, guitar, violin, flute) simultaneously, completely bypassing the Python Global Interpreter Lock (GIL).

---

## 🛠️ Technology Stack

*   **Backend Framework:** FastAPI
*   **Database:** PostgreSQL with SQLAlchemy ORM & Alembic for migrations
*   **Audio Processing:** Librosa, Pydub, Soundfile
*   **Machine Learning / AI:** Spleeter (TensorFlow 2.9.3), Groq (Whisper-large-v3)
*   **Concurrency:** `concurrent.futures.ThreadPoolExecutor`, `multiprocessing`
*   **Cloud Storage:** AWS S3 (`boto3`)
*   **Downloaders:** `yt-dlp`, `spotdl`

---

## 📂 Project Structure

```text
.
├── app/
│   ├── api/            # FastAPI Routers (Auth, Process, Analytics, Chatbot)
│   ├── crud/           # Database CRUD operations
│   ├── db/             # Database connection & models
│   ├── dto/            # Pydantic schemas for data validation
│   ├── services/       # Core business logic (Audio Processing Pipeline, S3, Email)
│   └── utils/          # Utilities (Librosa Extractors, Groq Whisper, Spleeter, Multiprocessing)
├── alembic/            # Database migration scripts
├── Dockerfile          # Containerization
├── requirements.txt    # Python dependencies
└── .env                # Environment variables
```

## ⚙️ Setup & Installation

1. **Clone the repository.**
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   *Note: Requires specific versions of TensorFlow (2.9.3) and NumPy (1.23.5) for Spleeter compatibility.*
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables & Configuration:**
   Copy the provided `.env.example` file to create your own `.env` file:
   ```bash
   cp .env.example .env
   ```
   Fill in your credentials, including:
   *   `DATABASE_URL` (PostgreSQL connection string)
   *   `GROQ_API_KEY`, `GOOGLE_CLIENT_ID`, `SPOTIPY_CLIENT_ID`, etc.
   *   AWS Credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET_NAME`)
   
5. **YouTube Cookies (Important):**
   To process songs from YouTube URLs (via `yt-dlp`), you **must** provide a `cookies.txt` file in the root directory to bypass age restrictions and bot blocks. Export your YouTube cookies using a browser extension (like "Get cookies.txt LOCALLY") and save it as `cookies.txt`. Ensure the `YT_COOKIES_PATH` in your `.env` points to this file.
6. **Run Database Migrations:**
   ```bash
   alembic upgrade head
   ```
7. **Start the Application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## 🔌 API Endpoints (Detailed Reference)

### 🔐 Authentication (`/api/auth`)
*   `POST /signup`: Register a new user.
*   `POST /signin`: Authenticate and receive a JWT Bearer token.
*   `POST /google`: Authenticate via Google OAuth token.
*   `GET /users/me`: Retrieve the currently authenticated user's profile.

### ⚙️ Processing Pipeline (`/api/process`)
*   `POST /process_url`: Submits a YouTube or Spotify URL for synchronous, full-pipeline processing (download, analysis, splitting, transcription).
*   `POST /process_audio_file`: Submits a direct audio file upload (multipart/form-data) for full-pipeline processing.
*   `GET /get-lyrics/{song_id}`: Retrieves the extracted `.lrc` lyrics with timestamps for a processed song.
*   `POST /rewrite-lyrics/{song_id}`: Uses an LLM to rewrite the existing lyrics based on a user-provided prompt while retaining the original timestamp alignment.

### 📊 Analytics & Stems (`/api/analytics`)
*   `GET /songs/{song_id}`: Retrieves the master record of a processed song including its global librosa analytics.
*   `GET /splits/vocals/{song_id}`: Retrieves the vocal stem audio URL and deep vocal-specific analytics (pitch, vibrato, gender prediction, etc.).
*   `GET /splits/bass/{song_id}`: Retrieves the bass stem audio URL and rhythmic/low-end analytics.
*   `GET /splits/drums/{song_id}`: Retrieves the drum stem audio URL and groove/tempo analytics.
*   `GET /splits/piano/{song_id}`: Retrieves the piano stem audio URL and harmonic/dynamic analytics.
*   `GET /splits/other/{song_id}`: Retrieves the "other" stem audio URL and texture analytics.
*   *Note: Deep analytics are also available via similar endpoints for `guitar`, `violin`, and `flute`.*

### 🤖 Chatbot (`/api/chat`)
*   `POST /ask`: Interact with the built-in LLM. Submit a question regarding the music data and receive an intelligent, contextual answer.
