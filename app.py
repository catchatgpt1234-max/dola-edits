import os
import time
import uuid
import threading
import base64
import io
import zipfile
import tempfile
import shutil
import cv2
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from utils.watermark_engine import (
    get_video_metadata,
    get_frame_at_time,
    inpaint_frame,
    process_video,
    auto_detect_dola_watermark,
    create_sample_dola_video,
    enhance_video_quality
)
from utils.speech_transcriber import transcribe_video_speech

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Direct all temp files and multipart stream spools to D: drive (plenty of free space)
tempfile.tempdir = TEMP_DIR
os.environ["TEMP"] = TEMP_DIR
os.environ["TMP"] = TEMP_DIR

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

TASKS = {}
TASK_CLEANUP_SECONDS = 1800  # Auto-cleanup completed tasks after 30 minutes
TRANSCRIPTION_CACHE = {}

@app.errorhandler(Exception)
def handle_all_exceptions(e):
    import traceback
    traceback.print_exc()
    status_code = getattr(e, "code", 500)
    return jsonify({
        "success": False,
        "error": str(e)
    }), status_code

def cleanup_old_tasks():
    """Remove completed/error tasks older than TASK_CLEANUP_SECONDS to prevent memory leak."""
    now = time.time()
    expired = [tid for tid, t in TASKS.items()
               if t.get("status") in ("completed", "error")
               and t.get("created_at", now) < now - TASK_CLEANUP_SECONDS]
    for tid in expired:
        del TASKS[tid]

    if expired:
        print(f"🧹 Cleaned up {len(expired)} old task(s) from memory.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'mov', 'avi', 'mkv', 'webm'}

def get_ga_id():
    env_id = os.environ.get("GA_MEASUREMENT_ID", "").strip()
    if env_id:
        return env_id
    key_file = os.path.join(BASE_DIR, "ga_id.txt")
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and line.startswith("G-"):
                        return line
        except Exception:
            pass
    return "G-XXXXXXXXXX"

@app.route("/")
def index():
    ga_id = get_ga_id()
    return render_template("index.html", ga_id=ga_id)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'robots.txt', mimetype='text/plain')

@app.route("/sitemap.xml")
def sitemap_xml():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml', mimetype='application/xml')

@app.route("/api/upload", methods=["POST"])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported format. Allowed: MP4, MOV, WEBM, AVI, MKV"}), 400
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"upload_{uuid.uuid4().hex[:10]}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    file.save(save_path)

    try:
        meta = get_video_metadata(save_path)
        auto_bbox = auto_detect_dola_watermark(save_path, meta)

        clean_name = f"dolaedits_clean_{unique_name.rsplit('.', 1)[0]}.mp4"
        transcription = None
        # Note: Heavy speech transcription is offloaded to /api/transcribe asynchronously
        # to ensure instant video upload and avoid gateway/server timeouts.
        if (request.form.get("transcribe_on_upload") == "true") and meta.get("has_audio"):
            try:
                transcription = transcribe_video_speech(save_path)
            except Exception as te:
                print(f"Speech transcription warning on upload: {te}")

        return jsonify({
            "success": True,
            "filename": unique_name,
            "original_name": file.filename,
            "video_url": f"/api/media/uploads/{unique_name}",
            "clean_filename": None,
            "clean_video_url": None,
            "metadata": meta,
            "auto_bbox": auto_bbox,
            "transcription": transcription
        })
    except Exception as e:
        return jsonify({"error": f"Failed to analyze video: {str(e)}"}), 500

@app.route("/api/sample", methods=["POST"])
def generate_sample():
    try:
        unique_name = f"sample_dola_{uuid.uuid4().hex[:8]}.mp4"
        sample_path = os.path.join(UPLOAD_DIR, unique_name)
        create_sample_dola_video(sample_path)
        
        meta = get_video_metadata(sample_path)
        auto_bbox = auto_detect_dola_watermark(sample_path, meta)

        clean_name = f"dolaedits_clean_{unique_name.rsplit('.', 1)[0]}.mp4"
        clean_path = os.path.join(OUTPUT_DIR, clean_name)
        clean_video_url = None
        try:
            process_video(
                video_path=sample_path,
                output_path=clean_path,
                bbox=auto_bbox,
                method="crop",
                remove_watermark=True,
                add_captions=False
            )
            clean_video_url = f"/api/media/outputs/{clean_name}"
        except Exception as e:
            print("Auto-clean on sample warning:", e)

        transcription = {"has_speech": False, "cues": [], "formatted_text": ""}
        if meta.get("has_audio"):
            try:
                transcription = transcribe_video_speech(sample_path)
            except Exception as te:
                print("Speech transcription warning on sample:", te)

        return jsonify({
            "success": True,
            "filename": unique_name,
            "original_name": "Demo_Dola_AI_Video.mp4",
            "video_url": f"/api/media/uploads/{unique_name}",
            "clean_filename": clean_name if clean_video_url else None,
            "clean_video_url": clean_video_url,
            "metadata": meta,
            "auto_bbox": auto_bbox,
            "transcription": transcription
        })
    except Exception as e:
        return jsonify({"error": f"Failed to create demo video: {str(e)}"}), 500

@app.route("/api/transcribe", methods=["POST"])
def api_transcribe_audio():
    """
    On-demand AI Audio Speech Analysis endpoint.
    Transcribes spoken words from video with precise timestamps.
    """
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"success": False, "error": "filename is required"}), 400

    video_path = os.path.join(UPLOAD_DIR, secure_filename(filename))
    if not os.path.exists(video_path):
        return jsonify({"success": False, "error": "Video not found"}), 404

    try:
        if video_path in TRANSCRIPTION_CACHE:
            return jsonify({"success": True, **TRANSCRIPTION_CACHE[video_path]})

        result = transcribe_video_speech(video_path)
        if result:
            TRANSCRIPTION_CACHE[video_path] = result
        return jsonify({"success": True, **(result or {"has_speech": False, "cues": []})})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": True,
            "has_speech": False,
            "cues": [],
            "formatted_text": "",
            "message": f"Transcription warning: {str(e)}"
        })

@app.route("/api/process", methods=["POST"])
def start_processing():
    """
    Starts automated backend Dola Edits processing:
    - Watermark removal
    - Caption / Subtitle burning
    - Combined single-pass render
    """
    try:
        data = request.get_json(silent=True) or {}
        filename = data.get("filename")
        if not filename:
            return jsonify({"success": False, "error": "Filename is required"}), 400

        video_path = os.path.join(UPLOAD_DIR, secure_filename(filename))
        if not os.path.exists(video_path):
            return jsonify({"success": False, "error": f"Video file not found: {filename}"}), 404

        # Automated backend defaults
        bbox = data.get("bbox")
        method = data.get("method", "telea")
        feather = int(data.get("feather", 3))

        # Modes and caption options
        remove_watermark = data.get("remove_watermark", True)
        add_captions = data.get("add_captions", False)
        captions = data.get("captions", [])

        caption_style = data.get("caption_style", "classic")
        caption_size = data.get("caption_size", "md")
        caption_line_height = data.get("caption_line_height")
        caption_pos_y = data.get("caption_pos_y")
        quality = str(data.get("quality", "1080")).lower().strip()
        q_label = "original" if quality in ("original", "source") else ("4k" if quality in ("4k", "2160", "2160p") else ("720p" if "720" in quality else "1080p"))

        task_id = uuid.uuid4().hex
        output_filename = f"dolaedits_{task_id[:10]}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        original_name = data.get("original_name") or filename
        # Auto-cleanup old tasks before creating new ones
        cleanup_old_tasks()

        TASKS[task_id] = {
            "status": "processing",
            "percent": 0,
            "current_frame": 0,
            "total_frames": 0,
            "fps": 0.0,
            "eta": 0.0,
            "quality": q_label,
            "original_name": original_name,
            "output_filename": output_filename,
            "download_url": f"/api/download/{task_id}",
            "video_url": f"/api/media/outputs/{output_filename}",
            "error": None,
            "created_at": time.time()
        }

        def background_worker():
            def progress_cb(pct, cur, total, fps, eta):
                TASKS[task_id]["percent"] = pct
                TASKS[task_id]["current_frame"] = cur
                TASKS[task_id]["total_frames"] = total
                TASKS[task_id]["fps"] = fps
                TASKS[task_id]["eta"] = eta

            try:
                actual_captions = captions
                if add_captions and not actual_captions:
                    if video_path in TRANSCRIPTION_CACHE and TRANSCRIPTION_CACHE[video_path].get("cues"):
                        actual_captions = TRANSCRIPTION_CACHE[video_path]["cues"]
                    else:
                        TASKS[task_id]["percent"] = 5
                        try:
                            trans_result = transcribe_video_speech(video_path)
                            if trans_result and trans_result.get("cues"):
                                actual_captions = trans_result["cues"]
                                TRANSCRIPTION_CACHE[video_path] = trans_result
                        except Exception as te:
                            print("Server-side transcription fallback error:", te)

                actual_bbox = bbox
                if not actual_bbox and remove_watermark:
                    TASKS[task_id]["percent"] = 10
                    try:
                        actual_bbox = auto_detect_dola_watermark(video_path)
                    except Exception as be:
                        print("auto_detect_dola_watermark warning:", be)
                        actual_bbox = [0, 0, 100, 50]
                elif not actual_bbox:
                    actual_bbox = [0, 0, 100, 50]

                # High-speed single-pass rendering: directly scales, crops watermark, and burns captions in one pass
                process_video(
                    video_path=video_path,
                    output_path=output_path,
                    bbox=actual_bbox,
                    method=method,
                    feather=feather,
                    progress_callback=progress_cb,
                    remove_watermark=remove_watermark,
                    add_captions=add_captions,
                    captions=actual_captions,
                    caption_style=caption_style,
                    caption_size=caption_size,
                    caption_line_height=caption_line_height,
                    caption_pos_y=caption_pos_y,
                    target_quality=q_label
                )

                # Cache watermark-cleaned version if watermark was removed and no captions
                if remove_watermark and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    clean_name = f"dolaedits_clean_{filename.rsplit('.', 1)[0]}.mp4"
                    clean_path = os.path.join(OUTPUT_DIR, clean_name)
                    if not add_captions and not os.path.exists(clean_path):
                        import shutil
                        try:
                            shutil.copyfile(output_path, clean_path)
                        except Exception:
                            pass

                TASKS[task_id]["status"] = "completed"
                TASKS[task_id]["percent"] = 100
            except Exception as err:
                import traceback
                traceback.print_exc()
                TASKS[task_id]["status"] = "error"
                TASKS[task_id]["error"] = str(err)

        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "task_id": task_id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to start processing: {str(e)}"
        }), 500


@app.route("/api/status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    task = TASKS.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route("/api/download/<task_id>", methods=["GET"])
def download_cleaned(task_id):
    task = TASKS.get(task_id)
    output_path = None

    if task and task.get("output_filename"):
        cand = os.path.join(OUTPUT_DIR, task["output_filename"])
        if os.path.exists(cand) and os.path.getsize(cand) > 1000:
            output_path = cand

    # Robust fallback: if memory cache missed (e.g. worker recycle), search OUTPUT_DIR by task prefix
    if not output_path:
        prefix = task_id[:10] if len(task_id) >= 10 else task_id
        for f in os.listdir(OUTPUT_DIR):
            if prefix in f and f.endswith(".mp4"):
                cand = os.path.join(OUTPUT_DIR, f)
                if os.path.getsize(cand) > 1000:
                    output_path = cand
                    break

    if not output_path or not os.path.exists(output_path):
        return jsonify({"error": "File not ready"}), 404

    quality = request.args.get("quality", "1080").lower().strip()
    q_label = "original" if quality in ("original", "source") else ("4k" if quality in ("4k", "2160", "2160p") else ("720p" if "720" in quality else "1080p"))

    orig_base = "cleaned"
    if task and task.get("original_name"):
        orig_base = os.path.splitext(os.path.basename(task["original_name"]))[0]
    download_name = f"dolaedits_{q_label}_{orig_base[:15]}.mp4"

    return send_file(
        output_path,
        as_attachment=True,
        download_name=download_name,
        mimetype="video/mp4"
    )

@app.route("/api/download-clean/<filename>", methods=["GET"])
def download_clean_file(filename):
    quality = request.args.get("quality", "1080").lower().strip()
    q_label = "original" if quality in ("original", "source") else ("4k" if quality in ("4k", "2160", "2160p") else ("720p" if "720" in quality else "1080p"))

    base_no_ext = filename.replace("dolaedits_clean_", "").rsplit('.', 1)[0]
    clean_name = f"dolaedits_clean_{q_label}_{base_no_ext}.mp4"
    clean_path = os.path.join(OUTPUT_DIR, clean_name)

    if not os.path.exists(clean_path) or os.path.getsize(clean_path) < 1000:
        generic_name = f"dolaedits_clean_{base_no_ext}.mp4"
        generic_path = os.path.join(OUTPUT_DIR, generic_name)
        if q_label != "4k" and os.path.exists(generic_path) and os.path.getsize(generic_path) > 1000:
            clean_path = generic_path
        else:
            raw_cand = os.path.join(UPLOAD_DIR, filename if not filename.startswith("dolaedits_clean_") else f"{base_no_ext}.mp4")
            if not os.path.exists(raw_cand):
                for f in os.listdir(UPLOAD_DIR):
                    if base_no_ext in f:
                        raw_cand = os.path.join(UPLOAD_DIR, f)
                        break
            if os.path.exists(raw_cand):
                meta = get_video_metadata(raw_cand)
                auto_bbox = auto_detect_dola_watermark(raw_cand, meta)
                process_video(video_path=raw_cand, output_path=clean_path, bbox=auto_bbox, method="crop", remove_watermark=True, target_quality=q_label)
            elif os.path.exists(generic_path) and os.path.getsize(generic_path) > 1000:
                if q_label == "4k":
                    process_video(video_path=generic_path, output_path=clean_path, remove_watermark=False, target_quality="4k")
                else:
                    clean_path = generic_path
            else:
                return jsonify({"error": "Clean file not ready"}), 404

    download_name = f"dolaedits_clean_{q_label}_{base_no_ext[:12]}.mp4"

    return send_file(
        clean_path,
        as_attachment=True,
        download_name=download_name,
        mimetype="video/mp4"
    )

@app.route("/api/bulk-download", methods=["GET", "POST"])
def bulk_download():
    task_ids = []
    if request.method == "POST":
        if request.is_json:
            data = request.json or {}
            task_ids = data.get("task_ids", [])
        else:
            task_ids_str = request.form.get("task_ids", "")
            if task_ids_str:
                task_ids = [t.strip() for t in task_ids_str.split(",") if t.strip()]
    else:
        task_ids_str = request.args.get("task_ids", "")
        if task_ids_str:
            task_ids = [t.strip() for t in task_ids_str.split(",") if t.strip()]

    if not task_ids:
        return jsonify({"error": "No task_ids provided"}), 400

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip", dir=OUTPUT_DIR)
    temp_zip_path = temp_zip.name
    temp_zip.close()

    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_STORED) as zf:
            added_count = 0
            for i, tid in enumerate(task_ids):
                file_path = None
                task = TASKS.get(tid)
                if task and task.get("status") == "completed":
                    out_name = task.get("output_filename")
                    if out_name:
                        candidate = os.path.join(OUTPUT_DIR, out_name)
                        if os.path.exists(candidate):
                            file_path = candidate
                if not file_path:
                    # Fallback check for directly existing file
                    for cand_name in (f"dolaedits_{tid[:10]}.mp4", f"dolaremover_{tid[:10]}.mp4"):
                        candidate = os.path.join(OUTPUT_DIR, cand_name)
                        if os.path.exists(candidate):
                            file_path = candidate
                            break
                if file_path and os.path.exists(file_path):
                    orig_name = None
                    if task and task.get("original_name"):
                        orig_name = os.path.splitext(os.path.basename(task["original_name"]))[0]
                    if orig_name:
                        clean_arcname = f"{orig_name}_cleaned.mp4"
                    else:
                        clean_arcname = f"dolaedits_video_{i+1:02d}_{tid[:6]}.mp4"
                    zf.write(file_path, arcname=clean_arcname)
                    added_count += 1

        if added_count == 0:
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
            return jsonify({"error": "No completed files found to download"}), 404

        # Schedule background cleanup of temp ZIP after browser download completes
        def cleanup_zip():
            import time as _time
            _time.sleep(60)
            try:
                if os.path.exists(temp_zip_path):
                    os.remove(temp_zip_path)
            except Exception:
                pass
        threading.Thread(target=cleanup_zip, daemon=True).start()

        return send_file(
            temp_zip_path,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"dolaedits_bulk_{added_count}_videos.zip"
        )
    except Exception as e:
        if os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except Exception:
                pass
        return jsonify({"error": f"Failed to generate zip: {str(e)}"}), 500

@app.route("/api/media/<folder>/<filename>")
def serve_media(folder, filename):
    if folder not in ("uploads", "outputs"):
        return jsonify({"error": "Invalid folder"}), 400
    target_dir = UPLOAD_DIR if folder == "uploads" else OUTPUT_DIR
    return send_from_directory(target_dir, secure_filename(filename))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Dola Edits server on port {port} ...")
    app.run(host="0.0.0.0", port=port, debug=False)
