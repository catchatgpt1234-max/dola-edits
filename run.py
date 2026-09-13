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
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
