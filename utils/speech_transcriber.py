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

def get_whisper_model(model_size="base"):
    """
    Returns a singleton WhisperModel instance running locally on CPU.
    Defaults to 'base' for high-accuracy word timestamps with Silero VAD.
    """
    global _whisper_model
    if _whisper_model is None:
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
    return _whisper_model

def split_words_into_balanced_chunks(words, max_words=4):
    """
    Splits a sequence of words into balanced dynamic cues of 3-4 words (minimum 2 words when needed).
    - Uses sentence-ending punctuation (., !, ?) and silence pauses (>= 0.6s) as natural boundaries.
    - Divides long phrases into 3 to 4 word blocks without leaving awkward 1-word orphans.
    - Honors commas / semicolons as secondary split points when at 3 words.
    """
    if not words:
        return []

    # 1. Separate into natural spoken phrases by punctuation and pauses
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

    # 2. Partition each phrase into 3-4 word chunks
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
            # Balance remaining words:
            # 5 words -> 3 + 2
            # 6 words -> 3 + 3
            # 7 words -> 4 + 3
            # 8 words -> 4 + 4
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
                # If word at index 2 has a comma, break at 3 words
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
    Extracts clean 16kHz mono WAV and retries with/without VAD for 100% speech capture.
    """
    if not os.path.exists(video_path):
        return {
            "has_speech": False,
            "language": None,
            "cues": [],
            "formatted_text": "",
            "message": "Video file not found."
        }

    model = get_whisper_model(model_size)
    if model is None:
        return {
            "has_speech": False,
            "language": None,
            "cues": [],
            "formatted_text": "",
            "message": "Speech recognition engine could not be initialized."
        }

    wav_path = None
    try:
        # Duration detection
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

        # Extract clean 16kHz mono PCM WAV for Whisper decoding
        temp_dir = tempfile.gettempdir()
        wav_path = os.path.join(temp_dir, f"whisper_audio_{uuid.uuid4().hex[:8]}.wav")
        cmd = [FFMPEG_EXE, "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path]
        sub = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio_target = wav_path if (sub.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 1000) else video_path

        # 1. First attempt with VAD filter
        try:
            segments, info = model.transcribe(
                audio_target,
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
                word_timestamps=True
            )
            segments_list = list(segments)
        except Exception as ve:
            logger.warning(f"VAD transcribe notice: {ve}")
            segments_list = []
            info = None

        # 2. If VAD detected nothing or empty text, retry directly without VAD
        has_any_text = any(getattr(s, "text", "").strip() for s in segments_list)
        if not segments_list or not has_any_text:
            logger.info("Retrying speech transcription without VAD filter to capture subtle or noisy speech...")
            try:
                segments, info = model.transcribe(
                    audio_target,
                    beam_size=5,
                    vad_filter=False,
                    condition_on_previous_text=False,
                    word_timestamps=True
                )
                segments_list = list(segments)
            except Exception as fbe:
                logger.warning(f"Fallback transcribe notice: {fbe}")

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
                # Proportional fallback for segments without word timings
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
        detected_lang = getattr(info, "language", None) if (info and has_speech) else None

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
        if wav_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                pass

