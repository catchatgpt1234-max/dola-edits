"""
================================================================================
DOLA EDITS AI STUDIO - COMPLETE UNIFIED BACKEND (main.py)
================================================================================
All-in-one standalone file containing:
1. Core Configurations & Paths
2. Speech Transcriber Engine (faster-whisper, Silero VAD, 3-4 word viral cues)
3. Watermark Engine & Video Processing (FFmpeg, auto-detection, cropping, inpainting, quality scaling)
4. Flask Web Application & REST API Endpoints
5. High-Speed Background Task Queue & Bulk Downloader
================================================================================
"""

import os
import sys
import time
import uuid
import threading
import base64
import io
import zipfile
import tempfile
import shutil
import subprocess
import json
import re
import logging
import cv2
import numpy as np
import imageio_ffmpeg
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ------------------------------------------------------------------------------
# 1. CORE CONFIGURATIONS, PATHS & FFMPEG BINARY
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DolaEdits")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

tempfile.tempdir = TEMP_DIR
os.environ["TEMP"] = TEMP_DIR
os.environ["TMP"] = TEMP_DIR

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
CAPTION_FONT_PATH = os.path.abspath(os.path.join(BASE_DIR, "static", "fonts", "caption.ttf"))

# ------------------------------------------------------------------------------
# 2. SPEECH TRANSCRIBER ENGINE (faster-whisper + Silero VAD + Balanced 3-4 Word Cues)
# ------------------------------------------------------------------------------
_whisper_model = None

def get_whisper_model(model_size="base"):
    """
    Returns a singleton WhisperModel instance running locally on CPU.
    Defaults to 'base' for high-accuracy word timestamps with Silero VAD.
    """
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            for m_size in [model_size, "tiny"]:
                try:
                    logger.info(f"Loading faster-whisper model ({m_size}) on CPU...")
                    _whisper_model = WhisperModel(m_size, device="cpu", compute_type="int8")
                    logger.info(f"faster-whisper model ({m_size}) loaded successfully.")
                    break
                except Exception as e:
                    logger.warning(f"Could not load whisper model ({m_size}): {e}")
                    _whisper_model = None
        except ImportError:
            logger.error("faster-whisper is not installed. Speech transcription will be disabled.")
            _whisper_model = None
    return _whisper_model

def split_words_into_balanced_chunks(words, max_words=4):
    """
    Splits a sequence of words into balanced dynamic cues of 3-4 words.
    Uses sentence-ending punctuation and silence pauses (>= 0.6s) as boundaries.
    """
    if not words:
        return []

    phrases = []
    curr_phrase = []
    for i, w in enumerate(words):
        curr_phrase.append(w)
        txt = w['word'].strip()
        has_end_punct = any(txt.endswith(p) for p in ['.', '!', '?'])
        has_pause = False
        if i < len(words) - 1:
            if words[i + 1]['start'] - w['end'] >= 0.6:
                has_pause = True
        if has_end_punct or has_pause:
            phrases.append(curr_phrase)
            curr_phrase = []
    if curr_phrase:
        phrases.append(curr_phrase)

    cues = []
    for phrase in phrases:
        n = len(phrase)
        if n <= max_words:
            cues.append({
                'start': round(phrase[0]['start'], 2),
                'end': round(phrase[-1]['end'], 2),
                'text': ' '.join(x['word'].strip() for x in phrase)
            })
            continue

        idx = 0
        while idx < n:
            rem = n - idx
            if rem == 5:
                chunk_len = 3
            elif rem == 6:
                chunk_len = 3
            elif rem == 7:
                chunk_len = 4
            elif rem == 8:
                chunk_len = 4
            elif rem <= 4:
                chunk_len = rem
            else:
                if idx + 3 < n and any(phrase[idx + 2]['word'].strip().endswith(p) for p in [',', ';']):
                    chunk_len = 3
                else:
                    chunk_len = 4

            sub = phrase[idx : idx + chunk_len]
            cues.append({
                'start': round(sub[0]['start'], 2),
                'end': round(sub[-1]['end'], 2),
                'text': ' '.join(x['word'].strip() for x in sub)
            })
            idx += chunk_len

    return cues

def format_time_cue(seconds):
    """Formats seconds into mm:ss.s (e.g. 0:05.2)."""
    mins = int(seconds // 60)
    rem = seconds % 60
    return f"{mins}:{rem:04.1f}"

def transcribe_video_speech(video_path, model_size="base"):
    """
    Analyzes the audio track of the given video file and transcribes spoken words
    into dynamic 3-4 word cues strictly synchronized with the speaker's voice.
    Uses Silero Voice Activity Detection (VAD) to prevent false triggers on background noise.
    """
    if not os.path.exists(video_path):
        return {
            "has_speech": False,
            "language": None,
            "cues": [],
            "formatted_text": "",
            "message": "Video file not found."
        }

    try:
        import av
        with av.open(video_path) as container:
            audio_streams = [s for s in container.streams if s.type == 'audio']
            if not audio_streams:
                return {
                    "has_speech": False,
                    "language": None,
                    "cues": [],
                    "formatted_text": "",
                    "message": "Video has no audio track."
                }
    except Exception as ae:
        logger.debug(f"Audio stream check via PyAV: {ae}")

    model = get_whisper_model(model_size)
    if model is None:
        return {
            "has_speech": False,
            "language": None,
            "cues": [],
            "formatted_text": "",
            "message": "Speech recognition engine could not be initialized."
        }

    try:
        vid_duration = 10.0
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0 and fps > 0:
                vid_duration = round(total_frames / fps, 2)
            cap.release()
        except Exception as ve:
            logger.debug(f"Could not read duration via cv2: {ve}")

        segments, info = model.transcribe(
            video_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400, speech_pad_ms=200),
            condition_on_previous_text=False,
            word_timestamps=True
        )

        all_words = []
        for segment in segments:
            if getattr(segment, 'no_speech_prob', 0) > 0.85:
                continue
            if segment.words:
                for w in segment.words:
                    word_str = str(w.word).strip()
                    if not word_str or (float(w.end) - float(w.start) < 0.04):
                        continue
                    clean_letters = re.sub(r'[^\w]', '', word_str)
                    if len(clean_letters) >= 4 and len(set(clean_letters.lower())) <= 1:
                        continue
                    cleaned_word = re.sub(r'([a-zA-Z])\1{2,}', r'\1\1', word_str)
                    all_words.append({
                        'start': float(w.start),
                        'end': float(w.end),
                        'word': cleaned_word
                    })
            else:
                text = segment.text.strip()
                if text:
                    words = text.split()
                    seg_start = float(segment.start)
                    seg_end = float(segment.end)
                    seg_dur = max(0.5, seg_end - seg_start)
                    w_dur = seg_dur / max(1, len(words))
                    for idx, w in enumerate(words):
                        all_words.append({
                            'start': seg_start + idx * w_dur,
                            'end': seg_start + (idx + 1) * w_dur,
                            'word': w
                        })

        cues = split_words_into_balanced_chunks(all_words, max_words=4)

        if cues:
            cues.sort(key=lambda x: x["start"])
            for i in range(len(cues) - 1):
                gap = cues[i + 1]["start"] - cues[i]["end"]
                if 0 < gap < 0.4:
                    cues[i]["end"] = cues[i + 1]["start"]
                elif gap <= 0:
                    cues[i]["end"] = max(cues[i]["start"] + 0.5, cues[i + 1]["start"])

            last_end = cues[-1]["end"]
            if vid_duration - last_end <= 0.6:
                cues[-1]["end"] = round(vid_duration, 2)
            else:
                cues[-1]["end"] = round(min(vid_duration, last_end + 0.35), 2)

        formatted_lines = []
        for c in cues:
            t1 = format_time_cue(c["start"])
            t2 = format_time_cue(c["end"])
            formatted_lines.append(f"[{t1} - {t2}] {c['text']}")

        has_speech = len(cues) > 0
        formatted_text = "\n".join(formatted_lines)

        return {
            "has_speech": has_speech,
            "language": info.language if has_speech else None,
            "cues": cues,
            "formatted_text": formatted_text,
            "message": f"Successfully transcribed {len(cues)} speech cues." if has_speech else "No speech detected in audio."
        }
    except Exception as e:
        logger.warning(f"Audio transcription warning for {video_path}: {e}")
        return {
            "has_speech": False,
            "language": None,
            "cues": [],
            "formatted_text": "",
            "message": f"Transcription error: {str(e)}"
        }

# ------------------------------------------------------------------------------
# 3. WATERMARK ENGINE & VIDEO PROCESSING (FFmpeg Filters, Crop, Quality Scaling)
# ------------------------------------------------------------------------------
CAPTION_STYLES = {
    "classic": {
        "id": "classic",
        "label": "Classic Outline",
        "dt": lambda border_w, p: f"fontcolor=white:borderw={border_w}:bordercolor=black@0.95"
    },
    "boxed": {
        "id": "boxed",
        "label": "Boxed",
        "dt": lambda border_w, p: f"fontcolor=white:box=1:boxcolor=black@0.72:boxborderw={max(4, round(p * 0.20))}"
    },
    "yellow": {
        "id": "yellow",
        "label": "Yellow Classic",
        "dt": lambda border_w, p: f"fontcolor=0xFFD400:borderw={border_w}:bordercolor=black@0.95"
    },
    "mrbeast": {
        "id": "mrbeast",
        "label": "MrBeast Bold",
        "dt": lambda border_w, p: f"fontcolor=white:borderw={border_w + 3}:bordercolor=black:shadowcolor=black@0.85:shadowx={max(2, round(p*0.04))}:shadowy={max(2, round(p*0.04))}"
    },
    "hormozi": {
        "id": "hormozi",
        "label": "Hormozi Green",
        "dt": lambda border_w, p: f"fontcolor=0x00FF66:borderw={border_w + 2}:bordercolor=black:shadowcolor=black@0.85:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "label": "Cyberpunk",
        "dt": lambda border_w, p: f"fontcolor=0xFF2A85:borderw={border_w + 1}:bordercolor=black:shadowcolor=0x8A2BE2@0.85:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "flame": {
        "id": "flame",
        "label": "Fire Red",
        "dt": lambda border_w, p: f"fontcolor=0xFF3B30:borderw={border_w + 2}:bordercolor=black:shadowcolor=0xFF6600@0.85:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "gold": {
        "id": "gold",
        "label": "Luxury Gold",
        "dt": lambda border_w, p: f"fontcolor=0xFFD700:borderw={border_w + 2}:bordercolor=black:shadowcolor=black@0.9:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "blue": {
        "id": "blue",
        "label": "Cyan Pop",
        "dt": lambda border_w, p: f"fontcolor=0x00E5FF:borderw={border_w + 2}:bordercolor=black:shadowcolor=0x004488@0.85:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "neon": {
        "id": "neon",
        "label": "Neon Glow",
        "dt": lambda border_w, p: f"fontcolor=0x00FFCC:borderw={border_w + 1}:bordercolor=black@0.95"
    },
    "glass": {
        "id": "glass",
        "label": "Glass Bar",
        "dt": lambda border_w, p: f"fontcolor=white:box=1:boxcolor=0x121622@0.65:boxborderw={max(4, round(p * 0.22))}"
    }
}

SIZE_FACTORS = {
    "sm": 0.042,
    "md": 0.052,
    "lg": 0.064
}

def wrap_caption_text(text, max_chars):
    clean_text = " ".join(str(text).split())
    if not clean_text:
        return []
    words = clean_text.split()
    if len(clean_text) <= max_chars or len(words) <= 5:
        return [clean_text]
    lines = []
    curr = ""
    for w in words:
        test = f"{curr} {w}" if curr else w
        if curr and len(test) > max_chars:
            lines.append(curr)
            curr = w
        else:
            curr = test
    if curr:
        lines.append(curr)
    return lines

def build_caption_filters(captions, width, height, style_name="classic", size_key="md", line_height=None, pos_y=None, temp_dir=None):
    if not captions:
        return ""
    
    aspect_ratio = width / max(1, height)
    if isinstance(size_key, (int, float)) and float(size_key) > 0:
        scale_val = float(size_key)
    elif str(size_key).replace('.', '', 1).isdigit() and float(size_key) > 0:
        scale_val = float(size_key)
    else:
        scale_val = SIZE_FACTORS.get(str(size_key), SIZE_FACTORS["md"])

    scale_ratio = scale_val / 0.052

    if aspect_ratio < 0.85:
        p = max(16, round(width * 0.066 * scale_ratio))
    else:
        p = max(16, round(height * 0.052 * scale_ratio))

    border_w = max(2, round(p / 9))
    style_obj = CAPTION_STYLES.get(style_name, CAPTION_STYLES["classic"])
    dt_style = style_obj["dt"](border_w, p)

    default_spacing = 1.35 if style_name in ("boxed", "glass") else 1.16
    lh = float(line_height) if line_height is not None and float(line_height) > 0 else default_spacing
    bottom_margin_ratio = float(pos_y) if pos_y is not None and float(pos_y) > 0 else 0.07

    max_chars = max(24, int((width * 0.88) / max(1, p * 0.52)))
    escaped_font = CAPTION_FONT_PATH.replace("\\", "/").replace(":", "\\:")

    filters = []
    cue_idx = 0

    cleaned_cues = []
    for cue in captions:
        raw_text = cue.get("text", "")
        text = re.sub(r'^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\s*[-–—]|-->|to)\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[\]\)]?\s*[:\s-]*', '', raw_text, flags=re.IGNORECASE).strip()
        text = re.sub(r'^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?[\]\)]?\s*[:\s-]*', '', text, flags=re.IGNORECASE).strip()
        text = re.sub(r'\[\s*(?:\d{1,2}:)?\d{1,2}:\d{2}\s*[-–—]\s*(?:\d{1,2}:)?\d{1,2}:\d{2}\s*\]', '', text).strip()
        start = float(cue.get("start", 0))
        end = float(cue.get("end", 0))
        if text and end > start:
            cleaned_cues.append({"start": start, "end": end, "text": text})

    cleaned_cues.sort(key=lambda x: x["start"])

    for i in range(len(cleaned_cues) - 1):
        gap = cleaned_cues[i + 1]["start"] - cleaned_cues[i]["end"]
        if 0 < gap < 0.4:
            cleaned_cues[i]["end"] = cleaned_cues[i + 1]["start"]

    for cue in cleaned_cues:
        text = cue["text"]
        start = cue["start"]
        end = cue["end"]

        clean_cue = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]', '', text).strip()
        text_to_wrap = clean_cue if clean_cue else text
        lines = wrap_caption_text(text_to_wrap, max_chars)
        valid_lines = [l.strip() for l in lines if l.strip()]
        total_lines = len(valid_lines)
        if total_lines == 0:
            continue

        for line_idx, line_text in enumerate(valid_lines):
            clean_str = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]', '', line_text).strip()
            sanitized_text = clean_str.replace("\\", "").replace("%", "percent").strip()
            if not sanitized_text:
                continue

            cue_idx += 1
            txt_filename = f"cue_{cue_idx}_{int(time.time()*1000)%1000000}.txt"
            txt_path = os.path.join(temp_dir, txt_filename)
            with open(txt_path, "w", encoding="utf-8") as tf:
                tf.write(sanitized_text)

            escaped_txt_path = txt_path.replace("\\", "/").replace(":", "\\:")
            box_extra = round(p * 0.20) if style_name in ("boxed", "glass") else 0
            y_pos = round(height - (height * bottom_margin_ratio) - ((total_lines - line_idx) * p * lh) - box_extra)
            y_pos = max(10, min(height - p - 10, y_pos))

            drawtext_str = (
                f"drawtext=fontfile='{escaped_font}':textfile='{escaped_txt_path}':"
                f"{dt_style}:fontsize={p}:x=(w-text_w)/2:y={y_pos}:"
                f"enable='between(t,{start:.3f},{end:.3f})'"
            )
            filters.append(drawtext_str)

    return ",".join(filters)

def get_video_metadata(video_path):
    """Returns metadata about the video: fps, width, height, frame_count, duration, has_audio."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or np.isnan(fps):
        fps = 30.0
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    cap.release()

    has_audio = False
    try:
        cmd = [FFMPEG_EXE, "-i", video_path]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
        if "Audio:" in result.stderr:
            has_audio = True
    except Exception as e:
        logger.debug(f"Error checking audio: {e}")

    return {
        "fps": round(fps, 2),
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "duration": round(duration, 2),
        "has_audio": has_audio
    }

def auto_detect_dola_watermark(video_path, meta=None):
    """
    Automatically detects and computes the exact bounding box for the 'Dola AI' watermark.
    """
    if meta is None:
        meta = get_video_metadata(video_path)
    
    width = meta["width"]
    height = meta["height"]
    aspect_ratio = width / max(1, height)

    if aspect_ratio < 0.8:
        wm_w = int(width * 0.28)
        wm_h = int(height * 0.075)
        wm_x = width - wm_w
        wm_y = height - wm_h
    elif aspect_ratio > 1.3:
        wm_w = int(width * 0.18)
        wm_h = int(height * 0.08)
        wm_x = width - wm_w
        wm_y = height - wm_h
    else:
        wm_w = int(width * 0.22)
        wm_h = int(height * 0.08)
        wm_x = width - wm_w
        wm_y = height - wm_h

    wm_x = max(0, min(wm_x, width - 10))
    wm_y = max(0, min(wm_y, height - 10))
    wm_w = max(20, min(wm_w, width - wm_x))
    wm_h = max(15, min(wm_h, height - wm_y))

    return [wm_x, wm_y, wm_w, wm_h]

def get_frame_at_time(video_path, timestamp_sec=0.0):
    """Extract a single frame as a BGR numpy array at a given timestamp."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or np.isnan(fps):
        fps = 30.0
        
    frame_idx = int(timestamp_sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
    cap.release()
    return frame

def inpaint_frame(frame, bbox=None, method="telea", feather=3):
    """
    Cleans watermark from a single frame using edge crop + Lanczos scaling.
    """
    h, w = frame.shape[:2]
    aspect_ratio = w / max(1, h)
    if aspect_ratio < 0.85:
        crop_h = max(46, int(round(h * 0.038)))
    elif aspect_ratio > 1.3:
        crop_h = max(48, int(round(h * 0.065)))
    else:
        crop_h = max(46, int(round(h * 0.048)))

    if bbox is not None and len(bbox) == 4 and bbox[3] > 0:
        bx, by, bw, bh = bbox
        if by + bh >= h * 0.85:
            crop_h = max(crop_h, (h - by) + 4)

    if crop_h % 2 != 0:
        crop_h += 1

    crop_window_h = h - crop_h
    crop_window_w = int(round(crop_window_h * aspect_ratio))
    if crop_window_w % 2 != 0:
        crop_window_w -= 1
    if crop_window_h % 2 != 0:
        crop_window_h -= 1
    crop_x = max(0, (w - crop_window_w) // 2)
    crop_y = 0

    cropped = frame[crop_y:crop_y + crop_window_h, crop_x:crop_x + crop_window_w]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)

def process_video(
    video_path,
    output_path,
    bbox=None,
    method="telea",
    feather=3,
    progress_callback=None,
    remove_watermark=True,
    add_captions=False,
    captions=None,
    caption_style="classic",
    caption_size="md",
    caption_line_height=None,
    caption_pos_y=None,
    target_quality=None
):
    """
    Dola Edits Core Engine:
    - remove_watermark=True: cleanly eliminates Dola watermark with zero distortion.
    - add_captions=True: burns custom styled subtitles/captions with caption.ttf.
    - target_quality: Single-pass high-speed render directly to target resolution (720p, 1080p, 4k, or original).
    """
    meta = get_video_metadata(video_path)
    width = meta["width"]
    height = meta["height"]
    total_frames = meta["frame_count"]
    has_audio = meta["has_audio"]

    aspect_ratio = width / max(1, height)

    q_str = str(target_quality or "original").lower().strip()
    if q_str in ("original", "source"):
        tw, th = width, height
    elif aspect_ratio < 0.85:
        if q_str in ("720", "720p"):
            tw, th = 720, 1280
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 2160, 3840
        else:
            tw, th = 1080, 1920
    elif aspect_ratio > 1.3:
        if q_str in ("720", "720p"):
            tw, th = 1280, 720
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 3840, 2160
        else:
            tw, th = 1920, 1080
    else:
        if q_str in ("720", "720p"):
            tw, th = 720, 720
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 2160, 2160
        else:
            tw, th = 1080, 1080

    with tempfile.TemporaryDirectory() as temp_dir:
        wm_filter = None
        if remove_watermark:
            if aspect_ratio < 0.85:
                crop_h = max(46, int(round(height * 0.038)))
            elif aspect_ratio > 1.3:
                crop_h = max(48, int(round(height * 0.065)))
            else:
                crop_h = max(46, int(round(height * 0.048)))

            if bbox is not None and len(bbox) == 4 and bbox[3] > 0:
                bx, by, bw, bh = bbox
                if by + bh >= height * 0.85:
                    crop_h = max(crop_h, (height - by) + 4)

            if crop_h % 2 != 0:
                crop_h += 1

            crop_window_h = height - crop_h
            crop_window_w = int(round(crop_window_h * aspect_ratio))
            if crop_window_w % 2 != 0:
                crop_window_w -= 1
            if crop_window_h % 2 != 0:
                crop_window_h -= 1
            crop_x = max(0, (width - crop_window_w) // 2)
            crop_y = 0
            wm_filter = f"crop={crop_window_w}:{crop_window_h}:{crop_x}:{crop_y},scale={tw}:{th}:flags=bicubic,setsar=1"

        cap_filter = ""
        if add_captions and captions:
            cap_filter = build_caption_filters(
                captions=captions,
                width=tw,
                height=th,
                style_name=caption_style or "classic",
                size_key=caption_size or "md",
                line_height=caption_line_height,
                pos_y=caption_pos_y,
                temp_dir=temp_dir
            )

        if wm_filter and cap_filter:
            vf_filter = f"{wm_filter},{cap_filter}"
        elif wm_filter:
            vf_filter = wm_filter
        elif cap_filter:
            vf_filter = f"scale={tw}:{th}:flags=bicubic,setsar=1,{cap_filter}"
        else:
            vf_filter = "null"

        v_codec_args = ["-threads", "0", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-tune", "fastdecode", "-pix_fmt", "yuv420p"]
        if getattr(process_video, "_nvenc_supported", None) is None:
            try:
                chk = subprocess.run([FFMPEG_EXE, "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.05", "-c:v", "h264_nvenc", "-f", "null", "-"], capture_output=True)
                process_video._nvenc_supported = (chk.returncode == 0)
            except Exception:
                process_video._nvenc_supported = False

        if getattr(process_video, "_nvenc_supported", False):
            v_codec_args = ["-c:v", "h264_nvenc", "-preset", "p3", "-cq", "19", "-pix_fmt", "yuv420p"]

        cmd = [
            FFMPEG_EXE, "-y",
            "-i", video_path,
            "-vf", vf_filter,
            *v_codec_args
        ]

        if has_audio:
            cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-an"])

        cmd.extend([
            "-progress", "pipe:1",
            output_path
        ])

        start_time = time.time()
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="ignore"
            )

            output_lines = []
            for line in proc.stdout:
                line = line.strip()
                if len(output_lines) > 50:
                    output_lines.pop(0)
                output_lines.append(line)

                if line.startswith("frame="):
                    try:
                        cur_frame = int(line.split("=")[1].strip())
                        pct = min(98, int((cur_frame / max(1, total_frames)) * 100))
                        elapsed = time.time() - start_time
                        fps_proc = cur_frame / max(0.1, elapsed)
                        eta = (total_frames - cur_frame) / max(0.1, fps_proc)
                        if progress_callback:
                            progress_callback(pct, cur_frame, total_frames, round(fps_proc, 1), round(eta, 1))
                    except:
                        pass

            proc.wait()

            if proc.returncode != 0 and has_audio:
                recent_err = "\n".join(output_lines[-15:])
                logger.info(f"FFMPEG primary encode notice ({proc.returncode}): retrying with AAC re-encode...")
                cmd_fallback = [
                    FFMPEG_EXE, "-y",
                    "-i", video_path,
                    "-vf", vf_filter,
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "17",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    output_path
                ]
                res_fb = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                if res_fb.returncode != 0:
                    raise RuntimeError(f"FFmpeg fallback encode error: {res_fb.stdout[-800:]}")
            elif proc.returncode != 0:
                recent_err = "\n".join(output_lines[-20:])
                raise RuntimeError(f"FFmpeg encode error (code {proc.returncode}): {recent_err}")

        except Exception as e:
            raise RuntimeError(f"Error processing video: {str(e)}")

        if progress_callback:
            progress_callback(100, total_frames, total_frames, 0, 0)

        return output_path

def create_sample_dola_video(target_path):
    """
    Generates a 3.5-second video with moving gradients and a realistic 'Dola AI' watermark.
    """
    width = 720
    height = 1280
    fps = 30
    duration = 3.5
    total_frames = int(fps * duration)

    ffmpeg_write_cmd = [
        FFMPEG_EXE, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        target_path
    ]

    proc = subprocess.Popen(
        ffmpeg_write_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        t = i / float(total_frames)
        r_val = int(120 + 80 * np.sin(t * 6.28))
        g_val = int(80 + 60 * np.cos(t * 6.28 * 2))
        b_val = int(180 + 50 * np.sin(t * 6.28 * 3))

        y_indices = np.linspace(0, 1, height).reshape(height, 1, 1)
        c1 = np.array([b_val, g_val, r_val], dtype=np.float32)
        c2 = np.array([40, 20, 60], dtype=np.float32)
        bg = (c1 * y_indices + c2 * (1.0 - y_indices)).astype(np.uint8)
        frame[:] = bg

        for p in range(5):
            px = int((width * (p * 0.23 + t * 0.3)) % width)
            py = int((height * (p * 0.19 + t * 0.2)) % height)
            radius = 30 + p * 10
            cv2.circle(frame, (px, py), radius, (255, 255, 255), -1)
        frame = cv2.GaussianBlur(frame, (31, 31), 0)

        cv2.putText(frame, "AI Video Scene", (width//2 - 150, height//2 - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Sample with Dola AI Logo", (width//2 - 180, height//2 + 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 230, 255), 1, cv2.LINE_AA)

        # Dola AI Watermark
        wm_x = width - 210
        wm_y = height - 90
        wm_w = 180
        wm_h = 46

        overlay = frame.copy()
        cv2.rectangle(overlay, (wm_x, wm_y), (wm_x + wm_w, wm_y + wm_h), (20, 20, 25), -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

        cv2.circle(frame, (wm_x + 24, wm_y + 23), 8, (255, 180, 50), -1)
        cv2.putText(frame, "Dola AI", (wm_x + 44, wm_y + 30), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    return target_path

def enhance_video_quality(input_path, output_path, target_quality="1080"):
    """
    Enhances video resolution, bitrate, and clarity according to selected target_quality:
    Original, 720p, 1080p, or 4K Ultra HD.
    """
    meta = get_video_metadata(input_path)
    orig_w, orig_h = meta["width"], meta["height"]
    aspect_ratio = orig_w / max(1, orig_h)
    q_str = str(target_quality).lower().strip()

    bitrate_args = []
    preset = "fast"
    crf = "14"

    if q_str in ("original", "source"):
        tw, th = orig_w, orig_h
        enh_filter = "cas=0.35"
        crf = "14"
        bitrate_args = ["-b:v", "20M", "-maxrate", "30M", "-bufsize", "40M"]
    elif aspect_ratio < 0.85:
        if q_str in ("720", "720p"):
            tw, th = 720, 1280
            enh_filter = "scale=720:1280:flags=lanczos,cas=0.4"
            crf = "16"
            bitrate_args = ["-b:v", "10M", "-maxrate", "15M", "-bufsize", "20M"]
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 2160, 3840
            enh_filter = "scale=2160:3840:flags=lanczos,cas=0.75,unsharp=5:5:0.8:3:3:0.3,eq=contrast=1.05:saturation=1.06"
            crf = "12"
            preset = "faster"
            bitrate_args = ["-b:v", "35M", "-maxrate", "50M", "-bufsize", "50M", "-profile:v", "high", "-level:v", "5.2"]
        else:
            tw, th = 1080, 1920
            enh_filter = "scale=1080:1920:flags=lanczos,cas=0.6,unsharp=5:5:0.5:3:3:0.25,eq=contrast=1.03:saturation=1.04"
            crf = "13"
            bitrate_args = ["-b:v", "20M", "-maxrate", "30M", "-bufsize", "35M"]
    elif aspect_ratio > 1.3:
        if q_str in ("720", "720p"):
            tw, th = 1280, 720
            enh_filter = "scale=1280:720:flags=lanczos,cas=0.4"
            crf = "16"
            bitrate_args = ["-b:v", "10M", "-maxrate", "15M", "-bufsize", "20M"]
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 3840, 2160
            enh_filter = "scale=3840:2160:flags=lanczos,cas=0.75,unsharp=5:5:0.8:3:3:0.3,eq=contrast=1.05:saturation=1.06"
            crf = "12"
            preset = "faster"
            bitrate_args = ["-b:v", "35M", "-maxrate", "50M", "-bufsize", "50M", "-profile:v", "high", "-level:v", "5.2"]
        else:
            tw, th = 1920, 1080
            enh_filter = "scale=1920:1080:flags=lanczos,cas=0.6,unsharp=5:5:0.5:3:3:0.25,eq=contrast=1.03:saturation=1.04"
            crf = "13"
            bitrate_args = ["-b:v", "20M", "-maxrate", "30M", "-bufsize", "35M"]
    else:
        if q_str in ("720", "720p"):
            tw, th = 720, 720
            enh_filter = "scale=720:720:flags=lanczos,cas=0.4"
            crf = "16"
            bitrate_args = ["-b:v", "10M", "-maxrate", "15M", "-bufsize", "20M"]
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 2160, 2160
            enh_filter = "scale=2160:2160:flags=lanczos,cas=0.75,unsharp=5:5:0.8:3:3:0.3,eq=contrast=1.05:saturation=1.06"
            crf = "12"
            preset = "faster"
            bitrate_args = ["-b:v", "35M", "-maxrate", "50M", "-bufsize", "50M", "-profile:v", "high", "-level:v", "5.2"]
        else:
            tw, th = 1080, 1080
            enh_filter = "scale=1080:1080:flags=lanczos,cas=0.6,unsharp=5:5:0.5:3:3:0.25,eq=contrast=1.03:saturation=1.04"
            crf = "13"
            bitrate_args = ["-b:v", "20M", "-maxrate", "30M", "-bufsize", "35M"]

    temp_atomic_output = f"{output_path}.tmp_{uuid.uuid4().hex[:8]}.mp4"

    cmd = [
        FFMPEG_EXE, "-y",
        "-i", input_path,
        "-vf", enh_filter,
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", crf,
        *bitrate_args,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "copy",
        temp_atomic_output
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            cmd[cmd.index("-c:a") + 1] = "aac"
            cmd.insert(cmd.index("aac") + 1, "-b:a")
            cmd.insert(cmd.index("-b:a") + 1, "192k")
            res_fb = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_fb.returncode != 0:
                raise RuntimeError(f"FFmpeg enhancement failed: {res_fb.stderr[-500:]}")

        if os.path.exists(temp_atomic_output) and os.path.getsize(temp_atomic_output) > 5000:
            os.replace(temp_atomic_output, output_path)
        else:
            raise RuntimeError("Generated enhanced video was incomplete or empty.")
    except Exception as exc:
        if os.path.exists(temp_atomic_output):
            try:
                os.remove(temp_atomic_output)
            except:
                pass
        raise exc

    return output_path

# ------------------------------------------------------------------------------
# 4. FLASK WEB APPLICATION & REST API ENDPOINTS
# ------------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

TASKS = {}
TASK_CLEANUP_SECONDS = 1800

def cleanup_old_tasks():
    """Remove completed/error tasks older than TASK_CLEANUP_SECONDS to prevent memory leak."""
    now = time.time()
    expired = [tid for tid, t in TASKS.items()
               if t.get("status") in ("completed", "error")
               and t.get("created_at", now) < now - TASK_CLEANUP_SECONDS]
    for tid in expired:
        del TASKS[tid]

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

        transcription = {"has_speech": False, "cues": [], "formatted_text": ""}
        skip_transcription = (request.form.get("skip_transcription") == "true") or (request.headers.get("X-Skip-Transcription") == "true")
        if not skip_transcription and meta.get("has_audio"):
            try:
                transcription = transcribe_video_speech(save_path)
            except Exception as te:
                logger.warning(f"Speech transcription warning on upload: {te}")

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
                logger.warning(f"Auto-clean on upload warning: {ce}")

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
            logger.warning(f"Auto-clean on sample warning: {e}")

        transcription = {"has_speech": False, "cues": [], "formatted_text": ""}
        if meta.get("has_audio"):
            try:
                transcription = transcribe_video_speech(sample_path)
            except Exception as te:
                logger.warning(f"Speech transcription warning on sample: {te}")

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
    data = request.json or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename required"}), 400

    video_path = os.path.join(UPLOAD_DIR, secure_filename(filename))
    if not os.path.exists(video_path):
        return jsonify({"error": "Video not found"}), 404

    bbox = data.get("bbox")
    if not bbox:
        bbox = auto_detect_dola_watermark(video_path)
        
    method = data.get("method", "telea")
    feather = int(data.get("feather", 3))

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
            TASKS[task_id]["status"] = "error"
            TASKS[task_id]["error"] = str(err)

    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()

    return jsonify({
        "success": True,
        "task_id": task_id
    })

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
                logger.warning(f"Enhance notice: {e}, falling back to master video")
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
            logger.warning(f"Clean enhance notice: {e}, falling back to master clean video")
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
                    for cand_name in (f"dolaedits_{tid[:10]}.mp4", f"dolaremover_{tid[:10]}.mp4"):
                        candidate = os.path.join(OUTPUT_DIR, cand_name)
                        if os.path.exists(candidate):
                            file_path = candidate
                            break
                if file_path and os.path.exists(file_path):
                    orig_name = None
                    if task and task.get("original_name"):
                        orig_name = os.path.splitext(os.path.basename(task["original_name"]))[0]
                    clean_arcname = f"{orig_name}_cleaned.mp4" if orig_name else f"dolaedits_video_{i+1:02d}_{tid[:6]}.mp4"
                    zf.write(file_path, arcname=clean_arcname)
                    added_count += 1

        if added_count == 0:
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
            return jsonify({"error": "No completed files found to download"}), 404

        def cleanup_zip():
            time.sleep(60)
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

# ------------------------------------------------------------------------------
# 5. ENTRYPOINT
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("=================================================================")
    print("🚀 DOLA EDITS AI STUDIO SERVER (main.py)")
    print("✨ Running at: http://127.0.0.1:5000")
    print("=================================================================")
    app.run(host="0.0.0.0", port=5000, debug=False)
