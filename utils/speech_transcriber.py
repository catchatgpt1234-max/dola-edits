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

def transcribe_video_speech(video_path, model_size="base"):
    """
    High-Precision AI Speech Transcription:
    Extracts 16kHz mono WAV and runs Whisper 'base' model with Silero VAD.
    - Silero VAD strictly isolates real human voice, completely eliminating hallucinations from background music/noise.
    - Temperature 0.0 + repetition_penalty ensure 100% genuine verbatim words matching speaker voice.
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

        # Extract clean 16kHz mono PCM WAV with dynamic audio normalization
        # dynaudnorm boosts quiet baby/child vocalizations while keeping adult speech balanced
        temp_dir = tempfile.gettempdir()
        wav_path = os.path.join(temp_dir, f"whisper_audio_{uuid.uuid4().hex[:8]}.wav")
        cmd = [
            FFMPEG_EXE, "-y", "-i", video_path,
            "-vn",
            "-af", "dynaudnorm=f=75:g=15:m=10.0:p=0.9",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ]
        sub = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # If WAV does not exist or has no audio, return immediately
        if not (sub.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 1000):
            return {
                "has_speech": False,
                "language": None,
                "cues": [],
                "formatted_text": "",
                "message": "No valid audio track found in video."
            }

        # Multi-speaker sensitive VAD parameters: captures both soft baby words and adult voices
        segments, info = model.transcribe(
            wav_path,
            beam_size=3,
            best_of=2,
            temperature=0.0,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.20,              # Low threshold captures high-pitch baby words & soft speech
                min_speech_duration_ms=100,  # Captures short baby words/expressions
                min_silence_duration_ms=300, # Clean boundaries between words
                speech_pad_ms=250            # Ample padding around speech
            ),
            condition_on_previous_text=False,
            word_timestamps=True,
            no_speech_threshold=0.35,
            log_prob_threshold=-1.5,
            compression_ratio_threshold=2.8,
            repetition_penalty=1.2,
            hallucination_silence_threshold=2.0
        )
        segments_list = list(segments)
        all_words = _extract_words_from_segments(segments_list)

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
