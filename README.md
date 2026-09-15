---
title: Dola Edits Video Studio
emoji: 🎬
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Dola Edits — AI Video Studio 🎬⚡

**Dola Edits** is a high-speed AI video editing studio designed to remove Dola AI watermarks and burn viral TikTok & Reels style subtitles/captions automatically with custom fonts, colors, and line spacing.

---

## 🌟 Key Features

- **Automated Watermark Removal**: Automatically detects and seamlessly removes Dola AI logos using intelligent crop and inpainting algorithms.
- **AI Captions & Subtitles**: Transcribes speech with aster-whisper and burns viral, readable 3-4 word captions onto video reels.
- **Bulk Processing Queue**: Process up to 50 videos concurrently with high-speed multi-threaded rendering and batch ZIP downloads.
- **Real-Time Studio Preview**: Compare Before vs. After results side-by-side before exporting.

---

## 🛠 Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-CORS, Gunicorn
- **Video & Image Processing**: OpenCV (opencv-python-headless), FFmpeg (imageio-ffmpeg), NumPy
- **Speech-to-Text**: aster-whisper with Silero VAD
- **Frontend**: Responsive Dark Neon / Glassmorphism UI (HTML5, Modern CSS3, Vanilla JavaScript)

---

## 🚀 Local Installation & Run

1. **Clone the repository:**
   `ash
   git clone https://github.com/catchatgpt1234-max/dola-edits.git
   cd dola-edits
   `

2. **Create a virtual environment & activate:**
   `ash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   `

3. **Install dependencies:**
   `ash
   pip install -r requirements.txt
   `

4. **Start the server:**
   `ash
   python app.py
   # Or using run.py
   python run.py
   `
   Open http://localhost:5000 in your web browser.

---

## 🌐 Deploying Live Online & Connecting .online Domain

### Option A: **Hugging Face Spaces** (🚀 RECOMMENDED: 16 GB RAM + 2 vCPU, 100% Free Forever)

Hugging Face Spaces provides **32x more RAM than Render (16 GB vs 0.5 GB)** and dedicated multi-core CPUs without requiring any credit card:

1. Create a free account at [huggingface.co](https://huggingface.co).
2. Go to **Spaces** -> Click **Create new Space**.
3. Settings:
   - **Space name**: `dola-edits`
   - **License**: `mit`
   - **Select the Space SDK**: Choose **Docker** -> **Blank**.
   - **Space hardware**: Choose **CPU basic (2 vCPU · 16 GB RAM - FREE)**.
4. Clone the space repo or connect your GitHub repository `catchatgpt1234-max/dola-edits`.
5. Hugging Face will automatically detect the [Dockerfile](file:///d:/Dola%20Watermark%20removel/Dockerfile) and launch your AI Video Studio with 16 GB RAM in ~2 minutes!
6. In your Space's **Settings**, go to **Custom Domains** and attach `dolaedits.online`.

---

### Option B: **Render.com** (Free Web Service, 512 MB RAM)

1. Sign up on [Render.com](https://render.com) and connect your GitHub account.
2. Click **New +** -> **Web Service**.
3. Select this repository: `catchatgpt1234-max/dola-edits`.
4. Configure:
   - **Environment**: Python 3
   - **Build Command**: `chmod +x render-build.sh && ./render-build.sh`
   - **Start Command**: `gunicorn app:app --workers 1 --threads 4 --timeout 600 --bind 0.0.0.0:$PORT`
5. Under **Environment Variables**, add:
   - `GROQ_API_KEY`: Your key from [console.groq.com](https://console.groq.com)
   - `FFMPEG_THREADS`: `2` (recommended for Render 512MB RAM)
6. Click **Create Web Service**.

#### Connecting your .online Domain on Render:
1. In Render, open your service settings -> **Custom Domains**.
2. Add your domain name (e.g. `dolaedits.online` and `www.dolaedits.online`).
3. Add the DNS records shown by Render into your domain registrar (Hostinger, Namecheap, GoDaddy, etc.).
4. Free SSL (HTTPS) certificate will be automatically issued within 10-15 minutes!
