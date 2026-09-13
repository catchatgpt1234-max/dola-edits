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

### Recommended Hosting: **Render.com** (Easiest & Best for Python/FFmpeg)

1. Sign up on [Render.com](https://render.com) and connect your GitHub account.
2. Click **New +** -> **Web Service**.
3. Select this repository: catchatgpt1234-max/dola-edits.
4. Configure:
   - **Environment**: Python 3
   - **Build Command**: pip install -r requirements.txt
   - **Start Command**: gunicorn app:app --workers 2 --timeout 300 --bind 0.0.0.0:
5. Click **Create Web Service**.

### Connecting your .online Domain:
1. In Render, open your service settings -> **Custom Domains**.
2. Add your domain name (e.g. yourname.online and www.yourname.online).
3. Go to your domain provider (Hostinger, Namecheap, GoDaddy, etc.) and add DNS records:
   - **CNAME Record**: Name: www | Value: <your-service>.onrender.com
   - **A Record**: Name: @ | Value: 216.24.57.1 (or the IP provided by Render)
4. Free SSL (HTTPS) certificate will be automatically issued within 10-15 minutes!
