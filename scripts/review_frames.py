#!/usr/bin/env python3
"""成片抽帧自检：均匀抽 16 帧 + 指定时刻补帧。

用法: python3 review_frames.py <video.mp4> [t1 t2 t3 ...]
输出: ./review_out/f*.png（均匀）与 ./review_out/t*.png（指定时刻）
自检清单：白描连贯？特写贴片隐形？上色浸润？结尾字幕在画内？
"""
import os
import subprocess
import sys

FFMPEG = "/opt/homebrew/bin/ffmpeg" if os.path.exists("/opt/homebrew/bin/ffmpeg") else "ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe" if os.path.exists("/opt/homebrew/bin/ffprobe") else "ffprobe"

vid = sys.argv[1]
extra = [float(x) for x in sys.argv[2:]]
out = "review_out"
os.makedirs(out, exist_ok=True)

dur = float(subprocess.run([FFPROBE, "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", vid],
                           capture_output=True, text=True).stdout.strip())
print(f"时长 {dur:.1f}s")

for i in range(16):
    t = dur * (i + 0.5) / 16
    subprocess.run([FFMPEG, "-y", "-ss", str(t), "-i", vid, "-frames:v", "1",
                    os.path.join(out, f"f{i:02d}_t{int(t):03d}.png")],
                   capture_output=True)
for t in extra:
    subprocess.run([FFMPEG, "-y", "-ss", str(t), "-i", vid, "-frames:v", "1",
                    os.path.join(out, f"t{int(t):03d}.png")], capture_output=True)
print(f"done → {out}/")
