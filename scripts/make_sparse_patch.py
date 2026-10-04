#!/usr/bin/env python3
"""稀疏深色笔迹贴片 / 重描源 生成器（贴片隐形的第 1、2、4 要素）。

两种模式：
  patch   裁剪盒 RGBA 贴片 + 超椭圆径向羽化 + placement.json（含切割窗口）
          —— 只留深色笔迹，排线晕染 alpha 归零（light≈155+gamma1.3，勿用默认205）
  retrace 全画布透明笔画图（供场景 from_image 提取后用墨线重描），
          可用 --erase-ellipse 挖掉眼睛（挡眼睛的不描）

窗口/盒子坐标均为铅笔稿像素系 (x0,y0,x1,y1)，终点排他。
placement.json 的 cut_window_xy_bottom_top 直接喂 StrokeSet.cut_out_rectangles()，
切段后必须断言窗口内残留笔画数 = 0（切段静默失效的保险丝）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def sparse_alpha(crop: np.ndarray, dark: float, light: float, gamma: float) -> np.ndarray:
    """深色笔迹 alpha：灰 ≤dark 全实，≥light 归零，中间 gamma 收紧。"""
    return np.clip((light - crop) / (light - dark), 0, 1) ** gamma


def radial_falloff(h: int, w: int, r0: float) -> np.ndarray:
    """超椭圆径向渐隐：d=max(|nx|,|ny|)∈[0,1]，r0 起平滑衰减，边界必为 0。"""
    yy, xx = np.mgrid[:h, :w]
    nx = (2 * xx - w) / max(1, w - 1)
    ny = (2 * yy - h) / max(1, h - 1)
    d = np.maximum(np.abs(nx), np.abs(ny))
    t = np.clip((d - r0) / (1 - r0), 0, 1)
    return 1 - (3 * t ** 2 - 2 * t ** 3)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("patch", "retrace"), required=True)
    ap.add_argument("--pencil", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--box", nargs=4, type=int, required=True,
                    metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--scene-height", type=float, default=7.6)
    ap.add_argument("--scene-center", nargs=2, type=float, default=(0.0, -0.05))
    ap.add_argument("--dark", type=float, default=100.0)
    ap.add_argument("--light", type=float, default=155.0,
                    help="排线晕染归零线；默认 155。勿回升到 205（灰调会带进来）")
    ap.add_argument("--gamma", type=float, default=1.3)
    ap.add_argument("--r0", type=float, default=0.75,
                    help="径向羽化起始比例（0.75：贴脸五官不被削淡）")
    ap.add_argument("--ink", default="#23140F")
    ap.add_argument("--erase-ellipse", nargs=4, type=int, action="append",
                    default=[], metavar=("CX", "CY", "RX", "RY"),
                    help="挖空椭圆（铅笔像素系），retrace 模式挖双眼 → 挡眼不描")
    args = ap.parse_args()

    gray = np.asarray(Image.open(args.pencil).convert("L")).astype(float)
    H, W = gray.shape
    x0, y0, x1, y1 = args.box
    if not (0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H):
        raise SystemExit("box 越界")
    scale = args.scene_height / H
    cx, cy = args.scene_center

    if args.mode == "patch":
        crop = gray[y0:y1, x0:x1]
        h, w = crop.shape
        alpha = sparse_alpha(crop, args.dark, args.light, args.gamma)
        alpha = alpha * radial_falloff(h, w, args.r0)
        rgb = tuple(int(args.ink[i:i + 2], 16) for i in (1, 3, 5))
        rgba = np.zeros((h, w, 4), np.uint8)
        rgba[..., :3] = rgb
        rgba[..., 3] = np.rint(alpha * 255).astype(np.uint8)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgba, "RGBA").save(args.output)
        placement = {
            "source": args.pencil.name, "patch": args.output.name,
            "pixel_box_xyxy_exclusive": list(args.box),
            "manim_center": [cx + ((x0 + x1) / 2 - W / 2) * scale,
                             cy - ((y0 + y1) / 2 - H / 2) * scale],
            "manim_height": h * scale,
            "cut_window_xy_bottom_top": [cx + (x0 - W / 2) * scale,
                                          cx + (x1 - W / 2) * scale,
                                          cy - (y1 - H / 2) * scale,
                                          cy - (y0 - H / 2) * scale],
        }
        args.output.with_suffix(".placement.json").write_text(
            json.dumps(placement, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(json.dumps(placement, ensure_ascii=False, indent=2))
        print("自检：务必合成到纸色底上看（黑底看不出灰块/接缝）；"
              "非透明像素应只有深色笔迹（数千级，不是数万级）。")
    else:
        src = np.zeros((H, W), np.uint8)
        src[y0:y1, x0:x1] = np.rint(
            sparse_alpha(gray[y0:y1, x0:x1], args.dark, args.light, args.gamma)
            * 255).astype(np.uint8)
        if args.erase_ellipse:
            mask = Image.fromarray(src, "L")
            d = ImageDraw.Draw(mask)
            for ecx, ecy, erx, ery in args.erase_ellipse:
                d.ellipse([ecx - erx, ecy - ery, ecx + erx, ecy + ery], fill=0)
            src = np.asarray(mask).copy()
        rgba = np.zeros((H, W, 4), np.uint8)
        rgba[..., 3] = src
        args.output.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(rgba, "RGBA").save(args.output)
        print(f"retrace 源：{int((src > 0).sum())} px → 场景中 from_image 后"
              f"用 adaptive_widths+Create 重描，z 高于贴片。")


if __name__ == "__main__":
    main()
