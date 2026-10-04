"""《飓风战魂》叶枫 · 铅笔稿描摹 + 原图上色（v4）

v4 修订（用户反馈 v3 贴片内刘海粗细与全图墨线不匹配、对接突兀）：
  切片范围内的刘海/线条用与全图一致的墨线（adaptive 2.4/1.9）重新描出
  （bangs_source.png：眼窗内深色笔画、双眼椭圆挖空——挡眼睛的不描），
  覆盖切片里的铅笔细线，消除复制粘贴感。
其余同 v3：稀疏深色贴片（light155+gamma1.3）、选择性聚光（0.8 内全实/远处 0.12）、
  淡彩打底→分区加深的浸润上色、placement.json 切割窗口断言。
"""
import json
import os

import numpy as np
from manim import (
    Circle, Create, Dot, FadeIn, FadeOut, Group, ImageMobject, Line,
    Transform, VGroup, config, linear, smooth, UP,
)

import manim_handdraw as hd

config.frame_width = 16
config.frame_height = 9
config.background_color = hd.PAPER
# 沙箱批量删除保护解药：关掉辅助文件清理、拉高 partial 缓存上限
config["no_latex_cleanup"] = True
config["max_files_cached"] = 1000000

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets_v4")

EYES_PL = json.load(open(os.path.join(A, "eyes_ink.placement.json")))
MOUTH_PL = json.load(open(os.path.join(A, "mouth_ink.placement.json")))

INK_W = 3.0
SIZE = 7.6
CENTER = (0.0, -0.05)

TAG_FS = 33
TAG_Y = -4.02
LAYER_FADE = 4.0
LAYER_PAUSE = 1.6

PEN_SPEED = 4.5
MIN_TIME = 0.035

ZOOM = 0.26
# 特写焦点 = 眼贴片中心（placement.json 精确值）
FOCUS = np.array([EYES_PL["manim_center"][0], EYES_PL["manim_center"][1], 0.0])

# 五官切割窗口：placement.json 的 cut_window_xy_bottom_top
# (x_left, x_right, y_bottom, y_top) —— cut_out_rectangles 会校验顺序
CUT_WINDOWS = [
    tuple(EYES_PL["cut_window_xy_bottom_top"]),
    tuple(MOUTH_PL["cut_window_xy_bottom_top"]),
]

# 假装构造的椭圆参数（眉毛下方双眼，工作画框实测）
EYE_L = (-0.4617, 1.9620, 0.284, 0.231, -0.10)
EYE_R = (0.3551, 1.9607, 0.249, 0.249, 0.10)

ACCENT = "#00A896"
GOLD = "#E8B84B"
MUTED = "#8E8E93"
FX_CENTER = np.array([0.0, -0.55, 0.0])    # 结尾动效中心：胸前蓝焰


class YeFeng(hd.HandDrawScene):
    def _tag(self, msg, *, color=None, weight="NORMAL", scale=1.0, center=None,
             font=None):
        t = hd.tag_text(msg, font_size=TAG_FS,
                        color=MUTED if color is None else color,
                        weight=weight, scale=scale,
                        center=np.zeros(3) if center is None else center,
                        y=TAG_Y,
                        **({} if font is None else {"font": font}))
        t.set_z_index(40)
        return t

    @staticmethod
    def _layer(name, *, z=20):
        img = ImageMobject(os.path.join(A, name))
        img.scale_to_fit_height(SIZE)
        img.move_to([CENTER[0], CENTER[1], 0.0])
        img.set_z_index(z)
        return img

    @staticmethod
    def _face_ink(placement, ink_layer):
        """铅笔稿五官贴片：位置/大小严格按 placement.json。"""
        img = ImageMobject(os.path.join(A, placement["patch"]))
        img.scale_to_fit_height(placement["manim_height"])
        cx, cy = placement["manim_center"]
        img.move_to([cx, cy, 0]).set_z_index(25)
        ink_layer.append(img)
        return img

    def construct(self):
        ui = hd.CanvasUI(title="Yefeng · 飓风战魂",
                         subtitle="叶枫手书 · 铅笔稿描摹 + 原图上色")
        self.add(ui)
        tag = self._tag("Act 1 / 绘图工具装配：旋转圆规定位面容基准圆")
        self.play(FadeIn(tag), run_time=1.0)
        self.wait(0.5)

        ink_layer = []

        # =============================================================
        # Act 1 — 面容基准圆
        # =============================================================
        compass = hd.Compass(FOCUS.copy(), 0.65)
        self.play(FadeIn(compass), run_time=0.7)
        anims, face_ref = compass.draw_circle(run_time=2.2, dashed=False,
                                              color="#CBD5E1")
        self.play(*anims, run_time=2.2)
        self.wait(0.3)
        self.play(FadeOut(compass), run_time=0.5)
        self.wait(0.5)

        # =============================================================
        # Act 2 — 逐笔描摹：发型与颜面
        # =============================================================
        self.play(Transform(tag, self._tag(
            "Act 2 / 铅笔稿描摹：连贯墨线逐笔生长，笔尖沿笔画实时跟随",
            color=hd.INK, weight="BOLD")), run_time=0.8)

        strokes = hd.from_image(os.path.join(A, "lineart_final.png"),
                                size=SIZE, center=CENTER,
                                merge_gap=36, merge_angle=0.15,
                                clean_short=12)

        # ---- 五官窗口切段（官方 API：切窗内、保窗外穿越笔画） ----
        strokes = strokes.cut_out_rectangles(CUT_WINDOWS)
        # 验证：窗口内残留笔画点必须为 0（切段静默失效的保险丝）
        eps = 1e-6
        residual = 0
        for p in strokes.paths:
            for wx0, wx1, wy0, wy1 in CUT_WINDOWS:
                residual += int(np.count_nonzero(
                    (p[:, 0] > wx0 + eps) & (p[:, 0] < wx1 - eps) &
                    (p[:, 1] > wy0 + eps) & (p[:, 1] < wy1 - eps)))
        assert residual == 0, f"五官窗口内残留 {residual} 个笔画点！"

        # 密集区自适应线宽（库方法：主线 2.4 / 密集 1.7）
        widths = strokes.adaptive_widths(regular=2.4, fine=1.7)
        pairs = list(zip(strokes.paths, widths))

        head = [q for q in pairs if q[0][:, 1].mean() >= 1.5]
        torso = [q for q in pairs if -0.55 <= q[0][:, 1].mean() < 1.5]
        lower = [q for q in pairs if q[0][:, 1].mean() < -0.55]

        stylus = hd.Stylus()
        stylus.move_to(np.concatenate([head[0][0][0], [0.0]]))
        self.play(FadeIn(stylus), run_time=0.5)
        self.play(Transform(tag, self._tag(
            "笔 1/3 · 蓝发刺猬头：怒目与尖刺刘海", color=hd.INK)), run_time=0.5)
        self._draw(stylus, head, ink_layer)

        # =============================================================
        # Act 3 — 面容特写：假装构造 + 铅笔五官贴片逐步淡入
        # =============================================================
        self.play(FadeOut(tag), FadeOut(ui), FadeOut(face_ref), FadeOut(stylus),
                  run_time=0.5)

        # 反聚光（对齐魔女做法）：只压远处的笔画，面部附近的墨线保持全实——
        # 五官贴片必须"长"在完整的脸部线条里才不会像贴上去的。
        dim_mobs, keep_mobs = [], []
        for m in ink_layer:
            if isinstance(m, ImageMobject):
                continue
            pts = m.points
            if not len(pts):
                continue
            dist = float(np.linalg.norm(pts[:, :2] - FOCUS[:2], axis=1).min())
            (keep_mobs if dist < 0.80 else dim_mobs).append(m)

        spot = [self.camera.frame.animate.scale(ZOOM).move_to(FOCUS)]
        spot += [m.animate.set_stroke(opacity=0.12) for m in dim_mobs]
        self.play(*spot, run_time=1.3)

        tag = self._tag("Act 3 / 眼睛数学构造：椭圆参数方程 x=a·cosθ , y=b·sinθ",
                        color=hd.INK, weight="BOLD", scale=ZOOM, center=FOCUS)
        self.play(FadeIn(tag), run_time=0.6)
        self.wait(0.4)

        for E, name, trace in [
            (EYE_L, "左眼 · 椭圆", 1.6),
            (EYE_R, "右眼 · 椭圆（同构）", 1.4),
        ]:
            self._show_eye_construct(E, name, trace)

        # 眼睛贴片：原铅笔稿复刻（旋纹瞳 + 自然刘海遮挡 + 眉与鼻梁）
        self.play(FadeIn(self._face_ink(EYES_PL, ink_layer)), run_time=1.6)
        # 刘海/线条重描：切片内的铅笔细线用与全图一致的墨线粗细重新描出，
        # 消除粗细不匹配的"复制粘贴感"（bangs_source 已挖掉双眼，不挡眼睛）
        strands = hd.from_image(os.path.join(A, "bangs_source.png"),
                                size=SIZE, center=CENTER,
                                merge_gap=18, merge_angle=0.25, clean_short=5)
        sw = strands.adaptive_widths(regular=2.4, fine=1.9)
        strand_anims = []
        for p, w in zip(strands.paths, sw):
            mob = hd.stroke_mobject(p, color=hd.INK, stroke_width=w)
            mob.set_z_index(26)
            strand_anims.append(Create(mob))
            ink_layer.append(mob)
        self.play(*strand_anims, run_time=1.8, rate_func=linear)
        self.wait(0.4)
        # 嘴巴贴片：呐喊大嘴原稿复刻
        self.play(FadeIn(self._face_ink(MOUTH_PL, ink_layer)), run_time=1.3)
        self.wait(0.6)

        self.play(FadeOut(tag), run_time=0.4)
        out = [self.camera.frame.animate.scale(1.0 / ZOOM).move_to([0, 0, 0])]
        out += [m.animate.set_stroke(opacity=1.0) for m in dim_mobs]
        self.play(*out, run_time=1.3)

        tag = self._tag("Act 4 / 描摹（续）：衣饰、佩饰与下装",
                        color=hd.INK, weight="BOLD")
        self.play(FadeIn(ui), FadeIn(tag), FadeIn(stylus), run_time=0.6)

        # =============================================================
        # Act 4 — 描摹：躯干与下半身
        # =============================================================
        self.play(Transform(tag, self._tag(
            "笔 2/3 · 战甲护腕：蓝色战衣与藏青护腕", color=hd.INK)), run_time=0.5)
        self._draw(stylus, torso, ink_layer)
        self.play(Transform(tag, self._tag(
            "笔 3/3 · 红裤飓风：下装与手中战魂", color=hd.INK)), run_time=0.5)
        self._draw(stylus, lower, ink_layer)

        self.play(FadeOut(stylus), run_time=0.6)
        self.wait(0.6)

        self.play(Transform(tag, self._tag(
            f"白描定稿 · 全 {len(strokes)} 笔，与铅笔稿逐线对齐",
            color=ACCENT, weight="BOLD")), run_time=0.7)
        scan = Line([-3.8, 3.4, 0], [3.8, 3.4, 0], stroke_color="#00B4D8",
                    stroke_width=3.0, stroke_opacity=0.8)
        self.play(scan.animate.move_to([0, -3.4, 0]), run_time=2.4, rate_func=smooth)
        self.play(FadeOut(scan), run_time=0.35)
        self.wait(1.0)

        # =============================================================
        # Act 5 — 原图分层浸润上色（淡彩打底 → 分区逐步加深 → 定妆）
        # =============================================================
        self.play(Transform(tag, self._tag(
            "Act 5 / 原图上色：淡彩晕染打底，蓝焰、暗夜、肌肤、蓝发依次浸润",
            color=hd.INK, weight="BOLD")), run_time=0.8)

        stages = [
            ("full_wash.png",  "上色 1/10 · 淡彩晕染打底"),
            ("lay_flame.png",  "上色 2/10 · 蓝焰燎原"),
            ("lay_night.png",  "上色 3/10 · 暗夜围城"),
            ("lay_bgrest.png", "上色 4/10 · 夜色余晕"),
            ("lay_skin.png",   "上色 5/10 · 肌肤透暖"),
            ("lay_hair.png",   "上色 6/10 · 蓝发塑形"),
            ("lay_white.png",  "上色 7/10 · 白边提亮"),
            ("lay_navy.png",   "上色 8/10 · 藏青护腕"),
            ("lay_red.png",    "上色 9/10 · 红裤点火"),
            ("lay_gold.png",   "上色 10/10 · 金饰闪电"),
            ("full.png",       "最后一并点睛 · 叶枫跃然纸上"),
        ]
        holders, partials = [], []
        for name, label in stages:
            last = name == stages[-1][0]
            grp = self._layer(name)
            stage = [Transform(tag, self._tag(
                label, color=ACCENT if last else MUTED,
                weight="BOLD" if last else "NORMAL")),
                FadeIn(grp, shift=UP * 0.05)]
            self.play(*stage, run_time=LAYER_FADE)
            holders.append(grp)
            if not last:
                partials.append(grp)
            self.wait(LAYER_PAUSE)
        full = holders[-1]
        wash = holders[0]

        # 分色层与墨线等完整图铺好后才收（Group：ink_layer 含贴片图片）
        self.play(FadeOut(Group(*ink_layer)), FadeOut(Group(*partials)),
                  run_time=1.2)
        self.remove(*ink_layer, *partials)
        self.wait(1.0)

        # =============================================================
        # Act 6 — 角色专属结尾动效
        # =============================================================
        self.play(Transform(tag, self._tag(
            "Act 6 / 烈焰觉醒 · 飓风降临", color=ACCENT, weight="BOLD",
            scale=0.93, center=[0.0, 0.4, 0.0])), run_time=0.7)

        glow = Circle(radius=0.35, stroke_color="#4FC3F7", stroke_width=5.0)
        glow.move_to(FX_CENTER).set_z_index(50)
        self.play(Create(glow), run_time=0.8, rate_func=smooth)
        self.play(glow.animate.scale(2.5).set_opacity(0), run_time=0.7)

        rng = np.random.default_rng(42)
        sparks = VGroup(*[
            Dot(radius=np.random.uniform(0.015, 0.04),
                color="#4FC3F7" if k % 2 else "#B3E5FC")
            .move_to([rng.uniform(-3.5, 3.5), rng.uniform(-3.2, 3.2), 0])
            .set_z_index(50)
            for k in range(22)
        ])
        self.play(FadeIn(sparks, scale=0.3), run_time=0.4)
        self.play(self.camera.frame.animate.scale(0.93).move_to([0.0, 0.4, 0]),
                  sparks.animate.shift(UP * 0.65).set_opacity(0),
                  run_time=2.0, rate_func=smooth)
        self.remove(sparks)
        self.wait(0.5)

        self.play(Transform(tag, self._tag(
            "Masterpiece · 飓风战魂 叶枫", color=ACCENT,
            weight="BOLD", font=hd.MONO_FONT, scale=0.93,
            center=[0.0, 0.4, 0.0])), run_time=1.1)
        self.wait(4.0)

    # ---------------------------------------------------------------- helpers
    def _draw(self, stylus, pairs, ink_layer):
        for p, w in pairs:
            anims, rt, mob = stylus.draw(p, stroke_width=w,
                                         pen_speed=PEN_SPEED, min_time=MIN_TIME)
            ink_layer.append(mob)
            self.play(*anims, run_time=rt)

    def _show_eye_construct(self, E, name, trace):
        """假装用参数方程构造椭圆（演出），不落墨——定稿由贴片呈现。"""
        ex, ey, Ea, Eb, tilt = E
        info = hd.trace_ellipse((ex, ey), Ea, Eb, tilt, run_time=trace,
                                show_label=name, label_scale=ZOOM)
        self.play(*info["anims"], run_time=trace)
        fade = [FadeOut(info["scaffold"]), FadeOut(info["path"])]
        if info["arm"] is not None:
            fade.append(FadeOut(info["arm"]))
        self.play(*fade, run_time=0.4)
