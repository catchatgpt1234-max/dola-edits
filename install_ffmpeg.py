import os
import sys
import shutil
import tarfile
import urllib.request

def install_ffmpeg():
    bin_dir = os.path.abspath('bin')
    os.makedirs(bin_dir, exist_ok=True)
    target = os.path.join(bin_dir, 'ffmpeg')

    if os.path.exists(target) and os.path.getsize(target) > 10000000:
        print(f'FFmpeg already installed at {target} ({os.path.getsize(target) // (1024*1024)} MB)')
        return

    # Reliable static builds containing libass, freetype, fontconfig
    urls = [
        'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz',
        'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz'
    ]

    for url in urls:
        print(f'Downloading static FFmpeg from: {url} ...')
        tmp_archive = '/tmp/ffmpeg_dl.tar.xz'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as resp, open(tmp_archive, 'wb') as out_f:
                shutil.copyfileobj(resp, out_f)

            print('Archive downloaded. Extracting ffmpeg binary...')
            with tarfile.open(tmp_archive, 'r:xz') as tf:
                found = False
                for member in tf.getmembers():
                    if member.name.endswith('/ffmpeg') or member.name == 'ffmpeg':
                        with tf.extractfile(member) as src, open(target, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        os.chmod(target, 0o755)
                        found = True
                        print(f'Successfully extracted FFmpeg ({os.path.getsize(target) // (1024*1024)} MB)')
                        break
            if os.path.exists(tmp_archive):
                os.remove(tmp_archive)
            if found and os.path.exists(target):
                return
        except Exception as e:
            print(f'Warning: {url} failed with: {e}')
            if os.path.exists(tmp_archive):
                os.remove(tmp_archive)

    if not os.path.exists(target):
        print('FATAL: Could not install FFmpeg binary.')
        sys.exit(1)

if __name__ == '__main__':
    install_ffmpeg()
