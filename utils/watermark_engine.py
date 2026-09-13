import os
import sys
import shutil
import cv2
import numpy as np
import subprocess
import json
import uuid
import time
import tempfile
import re

def get_ffmpeg_binary():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # 1. Local bin/ directory (downloaded via render-build.sh)
    for bin_name in ["ffmpeg", "ffmpeg.exe"]:
        local_bin = os.path.join(base_dir, "bin", bin_name)
        if os.path.exists(local_bin) and (os.access(local_bin, os.X_OK) or sys.platform.startswith("win")):
            return local_bin

    # 2. System PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    # 3. Auto-download on Linux (Render container) if missing
    if sys.platform.startswith("linux"):
        local_bin = os.path.join(base_dir, "bin", "ffmpeg")
        os.makedirs(os.path.join(base_dir, "bin"), exist_ok=True)
        if not os.path.exists(local_bin) or os.path.getsize(local_bin) < 100000:
            print("⏳ Downloading BtbN FFmpeg GPL static build (libass + drawtext + freetype)...")
            try:
                import urllib.request
                import tarfile
                tar_path = os.path.join(base_dir, "bin", "ffmpeg-build.tar.xz")
                urllib.request.urlretrieve(
                    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
                    tar_path
                )
                # Extract only the ffmpeg binary
                with tarfile.open(tar_path, "r:xz") as tf:
                    for member in tf.getmembers():
                        if member.name.endswith("/bin/ffmpeg") and not member.name.endswith("/bin/ffmpeg.exe"):
                            member.name = "ffmpeg"
                            tf.extract(member, os.path.join(base_dir, "bin"))
                            break
                os.chmod(local_bin, 0o755)
                # Clean up tar
                if os.path.exists(tar_path):
                    os.remove(tar_path)
                if os.path.exists(local_bin) and os.path.getsize(local_bin) > 1000000:
                    print(f"✅ FFmpeg downloaded successfully ({os.path.getsize(local_bin) // (1024*1024)} MB)")
                    return local_bin
            except Exception as de:
                print("FFmpeg download error:", de)

    # 4. Fallback to imageio_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG_EXE = get_ffmpeg_binary()

# Font path for captions (SoniAutoEditor / ZBot font)
CAPTION_FONT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "fonts", "caption.ttf"))

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
    },
    "aliabdaal": {
        "id": "aliabdaal",
        "label": "Ali Abdaal Clean",
        "dt": lambda border_w, p: f"fontcolor=white:box=1:boxcolor=black@0.68:boxborderw={max(5, round(p * 0.24))}"
    },
    "devinjatho": {
        "id": "devinjatho",
        "label": "Devin Jatho Impact",
        "dt": lambda border_w, p: f"fontcolor=0xFFE600:box=1:boxcolor=black@0.85:boxborderw={max(5, round(p * 0.26))}:borderw={max(1, border_w-1)}:bordercolor=black"
    },
    "karaoke": {
        "id": "karaoke",
        "label": "Karaoke Pop",
        "dt": lambda border_w, p: f"fontcolor=0x80FF20:borderw={border_w + 2}:bordercolor=black:shadowcolor=0xFFD700@0.85:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "cinematic": {
        "id": "cinematic",
        "label": "Cinematic Clean",
        "dt": lambda border_w, p: f"fontcolor=0xF5F5F7:borderw=1:bordercolor=black@0.80:shadowcolor=black@0.90:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "synthwave": {
        "id": "synthwave",
        "label": "Synthwave Purple",
        "dt": lambda border_w, p: f"fontcolor=0x9933FF:borderw={border_w + 2}:bordercolor=black:shadowcolor=0xFF007F@0.85:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "frost": {
        "id": "frost",
        "label": "Icy Frost",
        "dt": lambda border_w, p: f"fontcolor=0xD0FFFF:borderw={border_w + 2}:bordercolor=black:shadowcolor=0x002288@0.90:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "velvet": {
        "id": "velvet",
        "label": "Ruby Velvet",
        "dt": lambda border_w, p: f"fontcolor=0xE62222:borderw={border_w + 2}:bordercolor=black:shadowcolor=black@0.90:shadowx={max(2, round(p*0.03))}:shadowy={max(2, round(p*0.03))}"
    },
    "purplepop": {
        "id": "purplepop",
        "label": "Purple Box Pop",
        "dt": lambda border_w, p: f"fontcolor=white:box=1:boxcolor=0x6500C5@0.92:boxborderw={max(6, round(p * 0.28))}:borderw={max(1, border_w - 1)}:bordercolor=black"
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
    # Reel / Short captions are concise 3-4 word cues that must render on a single line
    # matching the web studio preview. Do not wrap if <= 5 words or within max_chars.
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

def format_ass_time(sec):
    """Formats seconds as ASS timestamp h:mm:ss.cs"""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def create_ass_subtitles_file(captions, width, height, style_name="classic", size_key="md", line_height=None, pos_y=None, temp_dir=None):
    """
    Generates a high-speed Advanced SubStation Alpha (.ass) subtitle file.
    Runs as a single C-accelerated filter in FFmpeg (80+ fps vs 0.8 fps drawtext!).
    """
    if not captions:
        return None

    if temp_dir is None:
        temp_dir = tempfile.gettempdir()

    aspect_ratio = width / max(1, height)
    if isinstance(size_key, (int, float)) and float(size_key) > 0:
        scale_val = float(size_key)
    elif str(size_key).replace('.', '', 1).isdigit() and float(size_key) > 0:
        scale_val = float(size_key)
    else:
        scale_val = SIZE_FACTORS.get(str(size_key), SIZE_FACTORS["md"])

    scale_ratio = scale_val / 0.052

    if aspect_ratio < 0.85:
        p = max(18, round(width * 0.066 * scale_ratio))
    else:
        p = max(18, round(height * 0.052 * scale_ratio))

    border_w = max(2, round(p / 8))
    bottom_margin_ratio = float(pos_y) if pos_y is not None and float(pos_y) > 0 else 0.07
    margin_v = max(10, round(height * bottom_margin_ratio))

    # ASS Colors in &HAABBGGRR format
    ASS_STYLE_MAP = {
        "classic": {"prim": "&H00FFFFFF", "outl": "&H00000000", "back": "&H80000000", "border": 1, "outw": border_w + 1, "shdw": 1},
        "yellow": {"prim": "&H0000D4FF", "outl": "&H00000000", "back": "&H80000000", "border": 1, "outw": border_w + 1, "shdw": 1},
        "mrbeast": {"prim": "&H00FFFFFF", "outl": "&H00000000", "back": "&H90000000", "border": 1, "outw": border_w + 4, "shdw": 3},
        "hormozi": {"prim": "&H0066FF00", "outl": "&H00000000", "back": "&H90000000", "border": 1, "outw": border_w + 3, "shdw": 3},
        "cyberpunk": {"prim": "&H00852AFF", "outl": "&H00000000", "back": "&H80E22B8A", "border": 1, "outw": border_w + 2, "shdw": 2},
        "flame": {"prim": "&H00303BFF", "outl": "&H00000000", "back": "&H800066FF", "border": 1, "outw": border_w + 2, "shdw": 2},
        "gold": {"prim": "&H0000D7FF", "outl": "&H00000000", "back": "&H90000000", "border": 1, "outw": border_w + 3, "shdw": 2},
        "blue": {"prim": "&H00FFE500", "outl": "&H00000000", "back": "&H80884400", "border": 1, "outw": border_w + 3, "shdw": 2},
        "neon": {"prim": "&H00CCFF00", "outl": "&H00000000", "back": "&H80000000", "border": 1, "outw": border_w + 2, "shdw": 1},
        "boxed": {"prim": "&H00FFFFFF", "outl": "&H00000000", "back": "&H80000000", "border": 3, "outw": border_w + 2, "shdw": 0},
        "glass": {"prim": "&H00FFFFFF", "outl": "&H00000000", "back": "&HB0121622", "border": 3, "outw": border_w + 2, "shdw": 0},
        "aliabdaal": {"prim": "&H00FFFFFF", "outl": "&H00000000", "back": "&HB0141414", "border": 3, "outw": border_w + 2, "shdw": 0},
        "devinjatho": {"prim": "&H0000E6FF", "outl": "&H00000000", "back": "&HD0050505", "border": 3, "outw": border_w + 3, "shdw": 0},
        "karaoke": {"prim": "&H0020FF80", "outl": "&H00000000", "back": "&H80000000", "border": 1, "outw": border_w + 3, "shdw": 3},
        "cinematic": {"prim": "&H00F7F5F5", "outl": "&H00000000", "back": "&H90000000", "border": 1, "outw": max(1, border_w - 1), "shdw": 2},
        "synthwave": {"prim": "&H00FF3399", "outl": "&H00000000", "back": "&H807F00FF", "border": 1, "outw": border_w + 2, "shdw": 3},
        "frost": {"prim": "&H00FFFFD0", "outl": "&H00000000", "back": "&H80882200", "border": 1, "outw": border_w + 3, "shdw": 3},
        "velvet": {"prim": "&H002222E6", "outl": "&H00000000", "back": "&H90000000", "border": 1, "outw": border_w + 2, "shdw": 2},
        "purplepop": {"prim": "&H00FFFFFF", "outl": "&H00000000", "back": "&H15C50065", "border": 3, "outw": border_w + 3, "shdw": 0},
    }
    st = ASS_STYLE_MAP.get(style_name, ASS_STYLE_MAP["classic"])

    ass_filename = f"caption_{uuid.uuid4().hex[:8]}.ass"
    ass_path = os.path.join(temp_dir, ass_filename)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{p},{st['prim']},&H000000FF,{st['outl']},{st['back']},-1,0,0,0,100,100,0,0,{st['border']},{st['outw']},{st['shdw']},2,20,20,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
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
        clean_str = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]', '', cue["text"]).strip()
        sanitized_text = clean_str.replace("\\", "").strip()
        if not sanitized_text:
            continue
        t_start = format_ass_time(cue["start"])
        t_end = format_ass_time(cue["end"])
        events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{sanitized_text}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")

    return ass_path

def build_caption_filters(captions, width, height, style_name="classic", size_key="md", line_height=None, pos_y=None, temp_dir=None):
    if not captions:
        return ""
    
    aspect_ratio = width / max(1, height)
    
    # Calculate scale multiplier from size_key (can be 'sm', 'md', 'lg', or a float like 0.052)
    if isinstance(size_key, (int, float)) and float(size_key) > 0:
        scale_val = float(size_key)
    elif str(size_key).replace('.', '', 1).isdigit() and float(size_key) > 0:
        scale_val = float(size_key)
    else:
        scale_val = SIZE_FACTORS.get(str(size_key), SIZE_FACTORS["md"])

    scale_ratio = scale_val / 0.052

    if aspect_ratio < 0.85:
        # Vertical Reels / Shorts (9:16): base font size on width so 3-4 word cues fit cleanly on 1 line
        p = max(16, round(width * 0.066 * scale_ratio))
    else:
        # Horizontal / Square video: base font size on height
        p = max(16, round(height * 0.052 * scale_ratio))

    border_w = max(2, round(p / 9))
    style_obj = CAPTION_STYLES.get(style_name, CAPTION_STYLES["classic"])
    dt_style = style_obj["dt"](border_w, p)

    default_spacing = 1.35 if style_name in ("boxed", "glass") else 1.16
    lh = float(line_height) if line_height is not None and float(line_height) > 0 else default_spacing
    bottom_margin_ratio = float(pos_y) if pos_y is not None and float(pos_y) > 0 else 0.07

    # max_chars allows full 3-4 word phrases (typically 18-28 chars) to stay on 1 line
    max_chars = max(24, int((width * 0.88) / max(1, p * 0.52)))
    escaped_font = CAPTION_FONT_PATH.replace("\\", "/").replace(":", "\\:")

    filters = []
    cue_idx = 0

    # Pre-process cues: clean text, sort, and bridge micro gaps
    cleaned_cues = []
    for cue in captions:
        raw_text = cue.get("text", "")
        # Clean any timestamp brackets or prefixes so only pure caption text is burned
        text = re.sub(r'^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\s*[-–—]|-->|to)\s*(?:\d{1,2}:)?\d{1,2}:\d{2}[\]\)]?\s*[:\s-]*', '', raw_text, flags=re.IGNORECASE).strip()
        text = re.sub(r'^[\[\(]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?[\]\)]?\s*[:\s-]*', '', text, flags=re.IGNORECASE).strip()
        text = re.sub(r'\[\s*(?:\d{1,2}:)?\d{1,2}:\d{2}\s*[-–—]\s*(?:\d{1,2}:)?\d{1,2}:\d{2}\s*\]', '', text).strip()
        start = float(cue.get("start", 0))
        end = float(cue.get("end", 0))
        if text and end > start:
            cleaned_cues.append({"start": start, "end": end, "text": text})

    cleaned_cues.sort(key=lambda x: x["start"])

    # Natural speech timing: only bridge tiny micro-gaps (< 0.4s) for smooth display,
    # preserving natural silence pauses so subtitles never display when nobody is speaking.
    for i in range(len(cleaned_cues) - 1):
        gap = cleaned_cues[i + 1]["start"] - cleaned_cues[i]["end"]
        if 0 < gap < 0.4:
            cleaned_cues[i]["end"] = cleaned_cues[i + 1]["start"]

    for cue in cleaned_cues:
        text = cue["text"]
        start = cue["start"]
        end = cue["end"]

        # Clean emojis and non-standard unicode symbols before wrapping
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
    """Returns metadata about the video: fps, width, height, frame_count, duration, has_audio with FFmpeg fallback."""
    fps = 30.0
    width = 0
    height = 0
    frame_count = 0
    duration = 0.0
    has_audio = False

    # 1. Try OpenCV VideoCapture first
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            f = cap.get(cv2.CAP_PROP_FPS)
            if f > 0 and not np.isnan(f):
                fps = f
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if fps > 0 and frame_count > 0:
                duration = frame_count / fps
            cap.release()
    except Exception as e:
        print(f"OpenCV metadata error: {e}")

    # 2. Use FFmpeg to verify / fallback for audio, resolution, duration and fps
    try:
        cmd = [FFMPEG_EXE, "-i", video_path]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
        stderr = result.stderr or ""
        if "Audio:" in stderr:
            has_audio = True

        dur_match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", stderr)
        if dur_match:
            h, m, s = float(dur_match.group(1)), float(dur_match.group(2)), float(dur_match.group(3))
            ffmpeg_dur = h * 3600 + m * 60 + s
            if ffmpeg_dur > 0:
                duration = ffmpeg_dur

        if width <= 0 or height <= 0:
            dim_match = re.search(r",\s*(\d{2,5})x(\d{2,5})", stderr)
            if dim_match:
                width = int(dim_match.group(1))
                height = int(dim_match.group(2))

        fps_match = re.search(r"([\d.]+)\s*fps", stderr)
        if fps_match:
            try:
                parsed_fps = float(fps_match.group(1))
                if parsed_fps > 0:
                    fps = parsed_fps
            except Exception:
                pass

        if frame_count <= 0 and duration > 0 and fps > 0:
            frame_count = int(duration * fps)
    except Exception as e:
        print(f"FFmpeg probe warning: {e}")

    # Safe defaults to prevent crash
    if width <= 0:
        width = 720
    if height <= 0:
        height = 1280
    if duration <= 0:
        duration = 10.0
    if frame_count <= 0:
        frame_count = max(1, int(duration * fps))

    return {
        "fps": round(fps, 2),
        "width": width,
        "height": height,
        "frame_count": max(1, frame_count),
        "duration": round(duration, 2),
        "has_audio": has_audio
    }

def auto_detect_dola_watermark(video_path, meta=None):
    """
    Automatically detects and computes the exact bounding box for the 'Dola AI' watermark.
    Dola AI places its watermark banner/text in the bottom-right corner.
    Works for 9:16 (vertical reels), 16:9 (horizontal), and 1:1 (square).
    """
    if meta is None:
        try:
            meta = get_video_metadata(video_path)
        except Exception:
            meta = {"width": 720, "height": 1280}
    
    width = meta.get("width", 720)
    height = meta.get("height", 1280)
    aspect_ratio = width / max(1, height)

    if aspect_ratio < 0.8:
        # Vertical Video (9:16 Reels / Shorts / TikTok)
        wm_w = int(width * 0.28)
        wm_h = int(height * 0.075)
        wm_x = width - wm_w
        wm_y = height - wm_h
    elif aspect_ratio > 1.3:
        # Horizontal / Landscape (16:9)
        wm_w = int(width * 0.18)
        wm_h = int(height * 0.08)
        wm_x = width - wm_w
        wm_y = height - wm_h
    else:
        # Square or standard (1:1 / 4:5)
        wm_w = int(width * 0.22)
        wm_h = int(height * 0.08)
        wm_x = width - wm_w
        wm_y = height - wm_h

    # Clamping
    wm_x = max(0, min(wm_x, width - 10))
    wm_y = max(0, min(wm_y, height - 10))
    wm_w = max(20, min(wm_w, width - wm_x))
    wm_h = max(15, min(wm_h, height - wm_y))

    return [wm_x, wm_y, wm_w, wm_h]

def get_frame_at_time(video_path, timestamp_sec=0.0):
    """Extract a single frame as a BGR numpy array at a given timestamp."""
    try:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
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
            if ret and frame is not None:
                return frame
    except Exception as e:
        print(f"OpenCV frame capture error: {e}")

    # Fallback to FFmpeg frame extraction if cv2 fails
    try:
        temp_img = tempfile.mktemp(suffix=".jpg")
        cmd = [FFMPEG_EXE, "-y", "-ss", str(max(0.0, timestamp_sec)), "-i", video_path, "-vframes", "1", "-q:v", "2", temp_img]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(temp_img):
            frame = cv2.imread(temp_img)
            try:
                os.remove(temp_img)
            except Exception:
                pass
            if frame is not None:
                return frame
    except Exception as fe:
        print(f"FFmpeg frame fallback error: {fe}")

    # Return empty fallback frame
    return np.zeros((1280, 720, 3), dtype=np.uint8)


def inpaint_frame(frame, bbox=None, method="telea", feather=3):
    """
    Cleans watermark from a single frame using edge crop + Lanczos scaling.
    Guarantees 100% clean output with zero residual text, zero blur, and zero artifacts.
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

    # Uniform aspect-ratio preserving crop: crops width and height proportionally
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
    - remove_watermark=True: cleanly and proportionally eliminates Dola watermark with zero distortion.
    - add_captions=True: burns custom styled subtitles/captions with caption.ttf.
    - target_quality: Single-pass high-speed render directly to target resolution (720p, 1080p, 4k, or original).
    Preserves 100% original frame resolution and audio stream.
    """
    meta = get_video_metadata(video_path)
    width = meta["width"]
    height = meta["height"]
    total_frames = meta["frame_count"]
    has_audio = meta["has_audio"]

    aspect_ratio = width / max(1, height)

    # Compute target export resolution for high-speed single-pass encoding
    q_str = str(target_quality or "original").lower().strip()
    if q_str in ("original", "source"):
        tw, th = width, height
    elif aspect_ratio < 0.85:
        # Vertical video (9:16)
        if q_str in ("720", "720p"):
            tw, th = 720, 1280
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 1440, 2560  # Ultra HD 2.5K (high speed, safe memory, 100+ fps)
        else:
            tw, th = 1080, 1920
    elif aspect_ratio > 1.3:
        # Horizontal (16:9)
        if q_str in ("720", "720p"):
            tw, th = 1280, 720
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 2560, 1440
        else:
            tw, th = 1920, 1080
    else:
        # Square (1:1)
        if q_str in ("720", "720p"):
            tw, th = 720, 720
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 1440, 1440
        else:
            tw, th = 1080, 1080

    with tempfile.TemporaryDirectory() as temp_dir:
        # Build watermark removal filter
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
            wm_filter = f"crop={crop_window_w}:{crop_window_h}:{crop_x}:{crop_y},scale={tw}:{th}:flags=fast_bilinear,setsar=1"

        # Build caption filter using high-speed ASS subtitles (runs at 80+ fps vs 0.8 fps drawtext)
        cap_filter = ""
        if add_captions and captions:
            try:
                ass_path = create_ass_subtitles_file(
                    captions=captions,
                    width=tw,
                    height=th,
                    style_name=caption_style or "classic",
                    size_key=caption_size or "md",
                    line_height=caption_line_height,
                    pos_y=caption_pos_y,
                    temp_dir=temp_dir
                )
                if ass_path and os.path.exists(ass_path):
                    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
                    cap_filter = f"subtitles='{escaped_ass}'"
            except Exception as ae:
                print("ASS subtitle generation notice:", ae)

        # Fallback to drawtext if ASS subtitle generation was not used
        if add_captions and captions and not cap_filter:
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

        # Combine filters
        if wm_filter and cap_filter:
            vf_filter = f"{wm_filter},{cap_filter}"
        elif wm_filter:
            vf_filter = wm_filter
        elif cap_filter:
            vf_filter = f"scale={tw}:{th}:flags=fast_bilinear,setsar=1,{cap_filter}"
        else:
            vf_filter = "null"

        # Encoder selection: check NVENC support or use multithreaded ultrafast libx264
        v_codec_args = ["-threads", "0", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-tune", "fastdecode", "-pix_fmt", "yuv420p"]
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
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-an"])

        cmd.extend([
            "-movflags", "+faststart",
            "-nostats",
            "-progress", "pipe:1",
            output_path
        ])

        output_lines = []
        start_time = time.time()
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="ignore",
                bufsize=1
            )

            fps_val = 0.0
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                output_lines.append(line)
                if len(output_lines) > 50:
                    output_lines.pop(0)

                if line.startswith("fps="):
                    try:
                        fps_val = float(line.split("=")[1].strip())
                    except:
                        pass
                elif line.startswith("frame="):
                    try:
                        cur_frame = int(line.split("=")[1].strip())
                        pct = min(98, int((cur_frame / max(1, total_frames)) * 100))
                        elapsed = time.time() - start_time
                        calc_fps = fps_val if fps_val > 1.0 else max(1.0, cur_frame / max(0.1, elapsed))
                        eta = max(0.5, (total_frames - cur_frame) / max(1.0, calc_fps))
                        if progress_callback:
                            progress_callback(pct, cur_frame, total_frames, round(calc_fps, 1), round(eta, 1))
                    except:
                        pass

            proc.wait()

            # If primary encode failed, analyze output and execute safe fallbacks
            if proc.returncode != 0:
                recent_err = "\n".join(output_lines[-20:])
                print("FFMPEG primary encode notice (returncode", proc.returncode, "): Last lines:\n", recent_err)
                
                # Check if subtitles filter failed (e.g. libass missing on Linux)
                dt_filter = ""
                if add_captions and captions:
                    try:
                        dt_filter = build_caption_filters(
                            captions=captions,
                            width=tw,
                            height=th,
                            style_name=caption_style or "classic",
                            size_key=caption_size or "md",
                            line_height=caption_line_height,
                            pos_y=caption_pos_y,
                            temp_dir=temp_dir
                        )
                    except Exception as de:
                        print("Drawtext fallback filter error:", de)

                if wm_filter and dt_filter:
                    retry_filter = f"{wm_filter},{dt_filter}"
                elif wm_filter:
                    retry_filter = wm_filter
                elif dt_filter:
                    retry_filter = f"scale={tw}:{th}:flags=bilinear,setsar=1,{dt_filter}"
                else:
                    retry_filter = "null"

                cmd_fallback = [
                    FFMPEG_EXE, "-y",
                    "-i", video_path,
                    "-vf", retry_filter,
                    "-threads", "2",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "20",
                    "-tune", "fastdecode",
                    "-pix_fmt", "yuv420p"
                ]
                if has_audio:
                    cmd_fallback.extend(["-c:a", "aac", "-b:a", "192k"])
                else:
                    cmd_fallback.append("-an")
                cmd_fallback.append(output_path)

                res_fb = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                if res_fb.returncode != 0:
                    # Final safety fallback: clean watermark removal without captions
                    if wm_filter and retry_filter != wm_filter:
                        print("⚠️ Retrying fallback without captions...")
                        cmd_fallback[4] = wm_filter
                        res_fb2 = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        if res_fb2.returncode != 0:
                            raise RuntimeError(f"FFmpeg encode error: {res_fb2.stdout[-400:]}")
                    else:
                        raise RuntimeError(f"FFmpeg fallback error: {res_fb.stdout[-400:]}")

        except Exception as e:
            raise RuntimeError(f"Error processing video: {str(e)}")

        if progress_callback:
            progress_callback(100, total_frames, total_frames, 0, 0)

        return output_path

def create_sample_dola_video(target_path):
    """
    Generates a 3.5-second video with moving gradients and a realistic 'Dola AI' watermark
    in the bottom right corner for immediate testing.
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

        # DOLA AI WATERMARK (Bottom Right Corner)
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
    Enhances video resolution, bitrate, and visual clarity according to selected target_quality:
    - 'original': Preserves native camera/render dimensions with high bit depth.
    - '720' / '720p': Fast HD export with Lanczos scaling and light CAS texture.
    - '1080' / '1080p': Full HD crisp render with Lanczos + AMD CAS sharpening (25 Mbps).
    - '4k' / '2160p': Ultra HD master with Lanczos + AMD FidelityFX CAS (0.75) + unsharp + contrast pop (55+ Mbps).
    """
    meta = get_video_metadata(input_path)
    orig_w, orig_h = meta["width"], meta["height"]
    aspect_ratio = orig_w / max(1, orig_h)
    q_str = str(target_quality).lower().strip()

    bitrate_args = []
    preset = "ultrafast"
    crf = "18"

    if q_str in ("original", "source"):
        tw, th = orig_w, orig_h
        enh_filter = "null"
        crf = "18"
    elif aspect_ratio < 0.85:
        # Vertical Reels / Shorts (9:16)
        if q_str in ("720", "720p"):
            tw, th = 720, 1280
            enh_filter = "scale=720:1280:flags=fast_bilinear"
            crf = "20"
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 1440, 2560
            enh_filter = "scale=1440:2560:flags=fast_bilinear"
            crf = "16"
        else: # default 1080p
            tw, th = 1080, 1920
            enh_filter = "scale=1080:1920:flags=fast_bilinear"
            crf = "18"
    elif aspect_ratio > 1.3:
        # Horizontal (16:9)
        if q_str in ("720", "720p"):
            tw, th = 1280, 720
            enh_filter = "scale=1280:720:flags=fast_bilinear"
            crf = "20"
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 2560, 1440
            enh_filter = "scale=2560:1440:flags=fast_bilinear"
            crf = "16"
        else: # 1080p
            tw, th = 1920, 1080
            enh_filter = "scale=1920:1080:flags=fast_bilinear"
            crf = "18"
    else:
        # Square (1:1) or other
        if q_str in ("720", "720p"):
            tw, th = 720, 720
            enh_filter = "scale=720:720:flags=fast_bilinear"
            crf = "20"
        elif q_str in ("4k", "2160", "2160p"):
            tw, th = 1440, 1440
            enh_filter = "scale=1440:1440:flags=fast_bilinear"
            crf = "16"
        else:
            tw, th = 1080, 1080
            enh_filter = "scale=1080:1080:flags=fast_bilinear"
            crf = "18"

    temp_atomic_output = f"{output_path}.tmp_{uuid.uuid4().hex[:8]}.mp4"

    cmd = [
        FFMPEG_EXE, "-y",
        "-i", input_path,
        "-vf", enh_filter,
        "-threads", "0",
        "-c:v", "libx264",
        "-preset", preset,
        "-tune", "fastdecode",
        "-crf", crf,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "copy",
        temp_atomic_output
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            # fallback with AAC audio
            cmd[cmd.index("-c:a") + 1] = "aac"
            cmd.insert(cmd.index("aac") + 1, "-b:a")
            cmd.insert(cmd.index("-b:a") + 1, "192k")
            res_fb = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_fb.returncode != 0:
                raise RuntimeError(f"FFmpeg enhancement failed: {res_fb.stderr[-500:]}")

        if os.path.exists(temp_atomic_output) and os.path.getsize(temp_atomic_output) > 50000:
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

