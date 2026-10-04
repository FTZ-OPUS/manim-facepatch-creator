#!/usr/bin/env python3
"""渲染安全包装：沙箱"批量删除保护"终极解药 + 缓存串味防护。

用法: python3 render_safe.py [-ql|-qm|-qh] [fps] [scene.py] [-- extra manim args]

两条铁律（都实测踩过）：
1. manim/依赖在渲染中清理缓存（media/texts、partial movie files）会触发
   SAFE_DELETE_BULK_CONFIRM_REQUIRED 直接退出，场景里设
   no_latex_cleanup/max_files_cached 都拦不住 → 本包装把渲染进程内的
   os.remove/unlink/os.rmdir/shutil.rmtree/Path.unlink 全部 no-op（缓存留着无害）。
2. 每次渲染前必须换新 media/videos/<场景> 目录（改名移走即可，别删）——
   manim 复用旧 partial 缓存，同名图片素材改了内容也不生效，
   表现为抽出的帧与旧版逐字节相同。
"""
import os
import shutil
import sys
import pathlib

if os.environ.get("ALLOW_DELETE") != "1":
    def _noop(*args, **kwargs):
        return None

    os.remove = _noop
    os.unlink = _noop
    os.rmdir = _noop
    shutil.rmtree = _noop
    pathlib.Path.unlink = _noop

quality, fps, scene = "-ql", None, None
args = sys.argv[1:]
if args and args[0] in ("-ql", "-qm", "-qh", "-qk"):
    quality = args.pop(0)
if args and args[0].isdigit():
    fps = args.pop(0)
if args and args[0].endswith(".py"):
    scene = args.pop(0)
if not scene:
    raise SystemExit("用法: render_safe.py [-ql|-qh] [fps] <scene.py> [类名]")

klass = args[0] if args else "YeFeng"
cmd = ["manim", quality, "--media_dir", "./media"]
if fps:
    cmd += ["--fps", fps]
cmd += [scene, klass]
print("RUN:", " ".join(cmd), flush=True)

sys.argv = cmd
from manim.__main__ import main  # noqa: E402
main()
