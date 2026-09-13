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

@app.route("/")
def index():
    return render_template("index.html")

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

        # AI Speech Analysis: Analyze video audio to transcribe spoken words into 3-4 word cues
        transcription = {"has_speech": False, "cues": [], "formatted_text": ""}
        skip_transcription = (request.form.get("skip_transcription") == "true") or (request.headers.get("X-Skip-Transcription") == "true")
        if not skip_transcription and meta.get("has_audio"):
            try:
                transcription = transcribe_video_speech(save_path)
            except Exception as te:
                print("Speech transcription warning on upload:", te)

        # Clean video path definition: Auto-clean watermark on upload so clean video is immediately ready
        clean_name = f"dolaedits_clean_{unique_name.rsplit('.', 1)[0]}.mp4"
        clean_path = os.path.join(OUTPUT_DIR, clean_name)
        clean_video_url = None

        skip_preclean = (request.form.get("skip_preclean") == "true")
        if not skip_preclean:
            try:
                process_video(
                    video_path=save_path,
                    output_path=clean_path,
                    bbox=auto_bbox,
                    method="crop",
                    remove_watermark=True,
                    add_captions=False
                )
                if os.path.exists(clean_path) and os.path.getsize(clean_path) > 1000:
                    clean_video_url = f"/api/media/outputs/{clean_name}"
            except Exception as ce:
                print("Auto-clean on upload warning:", ce)

        has_clean_file = (clean_video_url is not None) or (os.path.exists(clean_path) and os.path.getsize(clean_path) > 1000)
        return jsonify({
            "success": True,
            "filename": unique_name,
            "original_name": file.filename,
            "video_url": f"/api/media/uploads/{unique_name}",
            "clean_filename": clean_name if has_clean_file else None,
            "clean_video_url": clean_video_url or (f"/api/media/outputs/{clean_name}" if has_clean_file else None),
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
    data = request.json or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename is required"}), 400

    video_path = os.path.join(UPLOAD_DIR, secure_filename(filename))
    if not os.path.exists(video_path):
        return jsonify({"error": "Video not found"}), 404

    try:
        result = transcribe_video_speech(video_path)
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"error": f"Speech transcription failed: {str(e)}"}), 500

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
        if not bbox:
            try:
                bbox = auto_detect_dola_watermark(video_path)
            except Exception as be:
                print("auto_detect_dola_watermark warning:", be)
                bbox = [0, 0, 100, 50]
            
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
                # High-speed single-pass rendering: directly scales and crops in one pass with hardware acceleration
                process_video(
                    video_path=video_path,
                    output_path=output_path,
                    bbox=bbox,
                    method=method,
                    feather=feather,
                    progress_callback=progress_cb,
                    remove_watermark=remove_watermark,
                    add_captions=add_captions,
                    captions=captions,
                    caption_style=caption_style,
                    caption_size=caption_size,
                    caption_line_height=caption_line_height,
                    caption_pos_y=caption_pos_y,
                    target_quality=q_label
                )

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
    if not task or task.get("status") != "completed":
        return jsonify({"error": "File not ready"}), 404

    output_path = os.path.join(OUTPUT_DIR, task["output_filename"])
    if not os.path.exists(output_path):
        return jsonify({"error": "Output file missing"}), 404

    quality = request.args.get("quality", "1080").lower().strip()
    serve_path = output_path

    orig_base = "cleaned"
    if task.get("original_name"):
        orig_base = os.path.splitext(os.path.basename(task["original_name"]))[0]
    download_name = f"{orig_base}_cleaned.mp4"

    if quality in ("original", "source", "720", "720p", "1080", "1080p", "4k", "2160", "2160p"):
        q_label = "original" if quality in ("original", "source") else ("4k" if quality in ("4k", "2160", "2160p") else ("720p" if "720" in quality else "1080p"))
        if task.get("quality") == q_label:
            serve_path = output_path
            download_name = f"{orig_base}_cleaned_{q_label}.mp4"
        else:
            enhanced_name = f"enhanced_{q_label}_{task['output_filename']}"
            enhanced_path = os.path.join(OUTPUT_DIR, enhanced_name)
            try:
                if not os.path.exists(enhanced_path) or os.path.getsize(enhanced_path) < 1000:
                    enhance_video_quality(output_path, enhanced_path, target_quality=q_label)
                serve_path = enhanced_path
                download_name = f"{orig_base}_cleaned_{q_label}.mp4"
            except Exception as e:
                print(f"Enhance notice: {e}, falling back to master video")
                serve_path = output_path

    return send_file(
        serve_path,
        as_attachment=True,
        download_name=download_name,
        mimetype="video/mp4"
    )

@app.route("/api/download-clean/<filename>", methods=["GET"])
def download_clean_file(filename):
    if not filename.startswith("dolaedits_clean_"):
        clean_name = f"dolaedits_clean_{filename.rsplit('.', 1)[0]}.mp4"
    else:
        clean_name = filename

    clean_path = os.path.join(OUTPUT_DIR, clean_name)
    if not os.path.exists(clean_path):
        raw_cand = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(raw_cand):
            meta = get_video_metadata(raw_cand)
            auto_bbox = auto_detect_dola_watermark(raw_cand, meta)
            process_video(video_path=raw_cand, output_path=clean_path, bbox=auto_bbox, method="crop", remove_watermark=True)
        else:
            return jsonify({"error": "Clean file not ready"}), 404

    quality = request.args.get("quality", "1080").lower().strip()
    serve_path = clean_path
    download_name = f"dolaedits_clean_{clean_name[:12]}.mp4"

    if quality in ("original", "source", "720", "720p", "1080", "1080p", "4k", "2160", "2160p"):
        q_label = "original" if quality in ("original", "source") else ("4k" if quality in ("4k", "2160", "2160p") else ("720p" if "720" in quality else "1080p"))
        enhanced_name = f"enhanced_{q_label}_{clean_name}"
        enhanced_path = os.path.join(OUTPUT_DIR, enhanced_name)
        try:
            if not os.path.exists(enhanced_path) or os.path.getsize(enhanced_path) < 1000:
                enhance_video_quality(clean_path, enhanced_path, target_quality=q_label)
            serve_path = enhanced_path
            download_name = f"dolaedits_clean_{q_label}_{clean_name[:8]}.mp4"
        except Exception as e:
            print(f"Clean enhance notice: {e}, falling back to master clean video")
            serve_path = clean_path

    return send_file(
        serve_path,
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
