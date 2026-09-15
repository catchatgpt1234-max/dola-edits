# High-Performance Dockerfile for Hugging Face Spaces (16 GB RAM, 2 vCPUs)
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    FFMPEG_THREADS=4

# Install essential system dependencies: FFmpeg with libass & freetype, high-quality fonts, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces operates under user ID 1000
RUN useradd -m -u 1000 appuser

WORKDIR /home/appuser/app

# Install Python requirements
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY --chown=appuser:appuser . .

# Ensure upload, output, and temp storage have full read/write permissions
RUN mkdir -p uploads outputs temp scratch && \
    chown -R appuser:appuser /home/appuser/app

USER appuser

EXPOSE 7860

# Run with Gunicorn multi-worker multi-threaded server on port 7860
CMD ["gunicorn", "app:app", "--workers", "2", "--threads", "4", "--timeout", "600", "--bind", "0.0.0.0:7860"]
