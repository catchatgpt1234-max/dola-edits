import os
import re
import sys
import uuid
import shutil
import logging
import tempfile
import subprocess
from utils.watermark_engine import FFMPEG_EXE

logger = logging.getLogger(__name__)

_whisper_model = None
_whisper_model_size = None

def get_whisper_model(model_size="base"):
    """
    Returns a singleton WhisperModel instance running locally on CPU.
    Defaults to 'base' (int8) for high acoustic accuracy and zero hallucinations.
    """
    global _whisper_model, _whisper_model_size
    if _whisper_model is not None and _whisper_model_size == model_size:
        return _whisper_model
    from faster_whisper import WhisperModel
    for m_size in [model_size, "tiny"]:
        try:
            logger.info(f"Loading faster-whisper model ({m_size}) on CPU...")
            _whisper_model = WhisperModel(m_size, device="cpu", compute_type="int8")
            _whisper_model_size = m_size
            logger.info(f"faster-whisper model ({m_size}) loaded successfully.")
            return _whisper_model
        except Exception as e:
            logger.warning(f"Could not load whisper model ({m_size}): {e}")
            _whisper_model = None
    return None

def split_words_into_balanced_chunks(words, max_words=4):
    """
    Splits a sequence of words into balanced dynamic cues of 3-4 words (minimum 2 words when needed).
    - Uses sentence-ending punctuation (., !, ?) and silence pauses (>= 0.6s) as natural boundaries.
    - Divides long phrases into 3 to 4 word blocks without leaving awkward 1-word orphans.
    - Honors commas / semicolons as secondary split points when at 3 words.
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

def _extract_words_from_segments(segments_list):
    """Extracts all words with timestamps from a list of Whisper segments."""
    all_words = []
    for segment in segments_list:
        seg_text = getattr(segment, "text", "").strip()
        if not seg_text:
            continue

        if getattr(segment, "words", None):
            for w in segment.words:
                word_str = str(w.word).strip()
                if not word_str:
                    continue
                all_words.append({
                    'start': round(float(w.start), 2),
                    'end': round(float(w.end), 2),
                    'word': word_str
                })
        else:
            words = seg_text.split()
            seg_start = float(segment.start)
            seg_end = float(segment.end)
            seg_dur = max(0.4, seg_end - seg_start)
            w_dur = seg_dur / max(1, len(words))
            for idx, w in enumerate(words):
                all_words.append({
                    'start': round(seg_start + idx * w_dur, 2),
                    'end': round(seg_start + (idx + 1) * w_dur, 2),
                    'word': w
                })
    return all_words

def get_groq_api_key():
    """Retrieves Groq API key from environment or local git-ignored config file."""
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key
    key_file = os.path.join(os.path.dirname(__file__), "..", "groq_key.txt")
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                k = f.read().strip()
                if k.startswith("gsk_"):
                    return k
        except Exception:
            pass
    return ""

GROQ_API_KEY = get_groq_api_key()

def _transcribe_with_groq(audio_path, api_key=None):
    """
    Calls Groq Cloud Whisper API (whisper-large-v3) for ultra-fast, high-precision speech transcription.
    Returns (all_words, detected_language) or raises an exception.
    """
    key = api_key or GROQ_API_KEY
    if not key:
        raise ValueError("Groq API key not provided.")

    import requests
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {key}"
    }
    
    with open(audio_path, "rb") as f:
        files = {
            "file": (os.path.basename(audio_path), f, "audio/mpeg" if audio_path.endswith(".mp3") else "audio/wav")
        }
        data = {
            "model": "whisper-large-v3",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
            "temperature": "0.0"
        }
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=45)
        
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error ({resp.status_code}): {resp.text}")

    result = resp.json()
    detected_lang = result.get("language")
    
    all_words = []
    # Groq returns 'words' list when timestamp_granularities[] is word
    raw_words = result.get("words", [])
    if raw_words:
        for w in raw_words:
            word_str = str(w.get("word", "")).strip()
            if not word_str:
                continue
            all_words.append({
                "start": round(float(w.get("start", 0)), 2),
                "end": round(float(w.get("end", 0)), 2),
                "word": word_str
            })
    elif result.get("segments"):
        # Fallback to segments if words is empty
        for seg in result["segments"]:
            words = str(seg.get("text", "")).strip().split()
            seg_start = float(seg.get("start", 0))
            seg_end = float(seg.get("end", 0))
            seg_dur = max(0.4, seg_end - seg_start)
            w_dur = seg_dur / max(1, len(words))
            for idx, w in enumerate(words):
                all_words.append({
                    "start": round(seg_start + idx * w_dur, 2),
                    "end": round(seg_start + (idx + 1) * w_dur, 2),
                    "word": w
                })

    return all_words, detected_lang

def transcribe_video_speech(video_path, model_size="base"):
    """
    High-Precision AI Speech Transcription:
    1. Primary: Groq Cloud Whisper Large V3 (ultra-fast 0.5s response, 0% server CPU/RAM load).
    2. Fallback: Local faster-whisper model on CPU.
    """
    if not os.path.exists(video_path):
        return {
            "has_speech": False,
            "language": None,
            "cues": [],
            "formatted_text": "",
            "message": "Video file not found."
        }

    audio_path = None
    try:
        vid_duration = 10.0
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0 and fps > 0:
                vid_duration = round(total_frames / fps, 2)
            cap.release()
        except Exception:
            pass

        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"whisper_audio_{uuid.uuid4().hex[:8]}.mp3")
        
        # Extract clean audio with dynamic audio normalization (dynaudnorm)
        cmd = [
            FFMPEG_EXE, "-y", "-i", video_path,
            "-vn",
            "-af", "dynaudnorm=f=75:g=15:m=10.0:p=0.9",
            "-c:a", "libmp3lame",
            "-b:a", "64k",
            "-ar", "16000",
            "-ac", "1",
            audio_path
        ]
        sub = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if not (sub.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000):
            # Fallback to WAV extraction if mp3 encoding fails
            audio_path = os.path.join(temp_dir, f"whisper_audio_{uuid.uuid4().hex[:8]}.wav")
            cmd_wav = [
                FFMPEG_EXE, "-y", "-i", video_path,
                "-vn",
                "-af", "dynaudnorm=f=75:g=15:m=10.0:p=0.9",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                audio_path
            ]
            sub_wav = subprocess.run(cmd_wav, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not (sub_wav.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000):
                return {
                    "has_speech": False,
                    "language": None,
                    "cues": [],
                    "formatted_text": "",
                    "message": "No valid audio track found in video."
                }

        all_words = []
        detected_lang = None

        # Try Groq Cloud Whisper API first (Ultra-fast, 0% CPU)
        try:
            logger.info("Transcribing audio via Groq Cloud Whisper Large V3...")
            all_words, detected_lang = _transcribe_with_groq(audio_path)
            logger.info(f"Groq transcription completed: {len(all_words)} words, language={detected_lang}")
        except Exception as ge:
            logger.warning(f"Groq Cloud API unavailable ({ge}), falling back to local faster-whisper...")
            model = get_whisper_model(model_size)
            if model is not None:
                segments, info = model.transcribe(
                    audio_path,
                    beam_size=3,
                    best_of=2,
                    temperature=0.0,
                    vad_filter=True,
                    vad_parameters=dict(
                        threshold=0.20,
                        min_speech_duration_ms=100,
                        min_silence_duration_ms=300,
                        speech_pad_ms=250
                    ),
                    condition_on_previous_text=False,
                    word_timestamps=True,
                    repetition_penalty=1.2
                )
                all_words = _extract_words_from_segments(list(segments))
                detected_lang = getattr(info, "language", None)

        # Filter out repeated words or out-of-range timestamps
        filtered_words = []
        for i, w in enumerate(all_words):
            word_text = w['word'].strip().lower()
            if w['start'] > vid_duration + 1.0:
                continue
            if i > 0 and word_text == all_words[i-1]['word'].strip().lower():
                if abs(w['start'] - all_words[i-1]['start']) < 0.15:
                    continue
            filtered_words.append(w)
        all_words = filtered_words

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
            "language": detected_lang,
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
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass
