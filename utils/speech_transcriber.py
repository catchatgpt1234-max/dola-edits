"""
Speech Transcriber Module for Dola Edits
Uses local high-speed faster-whisper with word-level timestamps to analyze video audio
and chunk spoken words dynamically into 3-4 word segments (Reels / Shorts / TikTok style).
Dola Edits AI Studio
"""

import os
import logging

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
    
    Uses Silero Voice Activity Detection (VAD) to prevent false early triggers on
    background noise/music, ensuring subtitles appear precisely when the speaker talks.
    """
    if not os.path.exists(video_path):
        return {
            "has_speech": False,
            "language": None,
            "cues": [],
            "formatted_text": "",
            "message": "Video file not found."
        }

    # Verify audio stream exists to avoid container demux errors
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
        import cv2
        import re
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

        # High-accuracy transcription with Silero VAD, beam_size=5, and repetition suppression
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
            # Skip segments with high probability of no speech
            if getattr(segment, 'no_speech_prob', 0) > 0.85:
                continue
            if segment.words:
                for w in segment.words:
                    word_str = str(w.word).strip()
                    # Filter out zero-duration micro-ticks or empty tokens
                    if not word_str or (float(w.end) - float(w.start) < 0.04):
                        continue
                    # Repetition filter: discard pure single-letter spam (e.g. GEEEEEEEEEE or GGGGG)
                    clean_letters = re.sub(r'[^\w]', '', word_str)
                    if len(clean_letters) >= 4 and len(set(clean_letters.lower())) <= 1:
                        continue
                    # Compress excessive repetitive characters in word (e.g. Ahhhh -> Ahh)
                    cleaned_word = re.sub(r'([a-zA-Z])\1{2,}', r'\1\1', word_str)
                    all_words.append({
                        'start': float(w.start),
                        'end': float(w.end),
                        'word': cleaned_word
                    })
            else:
                # Proportional fallback for segments without word timings
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
            # Sort chronologically
            cues.sort(key=lambda x: x["start"])

            # Only bridge tiny micro-gaps (< 0.4s) to eliminate visual flicker.
            # Real pauses/silence (>= 0.4s) are preserved so subtitles don't display before the person speaks!
            for i in range(len(cues) - 1):
                gap = cues[i + 1]["start"] - cues[i]["end"]
                if 0 < gap < 0.4:
                    cues[i]["end"] = cues[i + 1]["start"]
                elif gap <= 0:
                    cues[i]["end"] = max(cues[i]["start"] + 0.5, cues[i + 1]["start"])

            # Final cue handling: only extend slightly if video ends very soon
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
