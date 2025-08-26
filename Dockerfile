# --- STAGE 1: Build Stage ---
# Use a specific, slim base image for consistency and size.
FROM python:3.10.13-slim-bookworm AS builder

# Set environment variables to prevent Python from writing .pyc files and to buffer output.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build-time and runtime dependencies in a single layer to reduce image size.
# Clean up apt cache in the same RUN command.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker's build cache.
WORKDIR /app
COPY requirements.txt .

# Install Python dependencies globally. Upgrade yt-dlp separately to ensure it's the latest version.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
    # pip install --no-cache-dir --upgrade yt-dlp spotdl



# --- STAGE 2: Final Production Image ---
# Start from a clean, slim base image for the final stage.
FROM python:3.10.13-slim-bookworm AS final

# Set same environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install only the essential runtime system dependency (ffmpeg).
# Create a non-root user for better security.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home --shell /bin/bash appuser

# Copy the installed Python packages from the builder stage.
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
# Copy any command-line tools that were installed by pip (like uvicorn, yt-dlp).
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code.
WORKDIR /app
COPY --chown=appuser:appuser . .

COPY --chown=appuser:appuser cookies.txt /app/cookies.txt

# Switch to the non-root user.
USER appuser

# Expose the port Cloud Run uses (8080) for documentation purposes.
EXPOSE 8080

# Set the command to run the application, respecting the $PORT variable from Cloud Run.
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]