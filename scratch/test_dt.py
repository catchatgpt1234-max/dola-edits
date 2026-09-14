from utils.watermark_engine import FFMPEG_EXE, CAPTION_FONT_PATH
import subprocess, cv2
font = CAPTION_FONT_PATH.replace('\\', '/').replace(':', '\\:')
vf = f"drawtext=fontfile='{font}':text='Hey no!':fontcolor=white:fontsize=52:box=1:boxcolor=black@0.75:boxborderw=16:x=(w-text_w)/2:y=h-h*0.10"
cmd = [FFMPEG_EXE, '-y', '-f', 'lavfi', '-i', 'color=c=0x1E3A8A:s=720x1280:d=1', '-vf', vf, '-vframes', '1', 'scratch/drawtext_test.png']
subprocess.run(cmd)
im = cv2.imread('scratch/drawtext_test.png')
print('Drawtext test success:', im is not None)
