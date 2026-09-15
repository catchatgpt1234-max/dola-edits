import webbrowser
import threading
import time
import os
import sys

def open_browser():
    time.sleep(1.5)
    print("🌐 Opening Dola Edits in your default browser...")
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    from app import app
    print("=" * 60)
    print("  Dola Edits - AI Video Watermark Remover & Caption Studio")
    print("  Dola Edits AI Studio")
    print("=" * 60)
    print("Server running at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop.")
    
    # Only open browser if NO_BROWSER is not set
    if os.environ.get("NO_BROWSER") != "1":
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        from waitress import serve
        print("🚀 Starting Waitress production WSGI server (16 threads, 300s timeout)...")
        serve(app, host="0.0.0.0", port=5000, threads=16, channel_timeout=300, connection_limit=200)
    except ImportError:
        print("⚠️ Waitress not installed, falling back to Flask development server...")
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
