# manim-facepatch-creator — 让手书动画的五官贴片"完全看不出贴的痕迹"

[![Python](https://img.shields.io/badge/python-3.12+-blue)]()
[![manim](https://img.shields.io/badge/manim-- CE-0.21+-red)]()
[![manim-handdraw](https://img.shields.io/badge/manim--handdraw-%E2%89%A50.1.1-green)]()

**一句话**：铅笔稿描摹 + 原图上色的手书动画里，五官（眼睛/嘴）用铅笔稿贴片复刻，
这个技能包把贴片从"一眼看出是复制粘贴"打磨到"完全看不出痕迹"——
并附带上色浸润化、沙箱渲染解药等整套实战沉淀。

<p align="center">
  <img src="examples/yefeng/closeup_patch_retrace.gif" width="420" alt="特写：贴片浮现 + 刘海重描"/>
  <img src="examples/yefeng/coloring_soak.gif" width="420" alt="浸润式上色"/>
</p>

*左：特写——眼睛贴片浮现后，窗内刘海用与全图一致的墨线重描（挡眼不描）；
右：上色——淡彩打底 → 分区逐步加深 → 定妆，全程水彩浸润感。*

---

## 它解决什么问题

手书动画的五官是"手绘感的命门"：数学椭圆画眼睛必假，直接贴铅笔稿又会穿帮——

- 贴片带着铅笔的**灰调排线**，往干净纸面上一糊，方形边界立现；
- 贴片里的**铅笔细线**与全图 2.4 宽的墨线粗细不匹配，接口一眼假；
- 特写时若全图压暗，贴片孤悬纸上，怎么羽化都像贴纸；
- 上色一层一层"蹦"出来，像贴色块，没有手绘上色的浸润感。

本包是《飓风战魂》叶枫项目从 v1 到 v4 四轮用户反馈迭代下来的最终方法，
v4 用户验收原话：**"完全看不出来了痕迹，太厉害了"**。

## 生态位：三个包各司其职

```
manim-handdraw（Python 库）          笔画引擎：from_image / Stylus / Compass
        ↓                              /cut_out_rectangles /adaptive_widths
manim-handdraw-creator（核心技能包）  六幕手书全流程：对齐 → 描摹 → 构造 →
        ↓                              贴片 → 上色 → 结尾动效
manim-facepatch-creator（本包）       精修专精：贴片隐形五要素 + 重描 +
                                       浸润式上色 + 渲染坑位解药
```

库装好、全流程跑通之后，如果验收时"五官还是看得出贴的"——就是本包登场的时候。

## 五条核心方法（每条都是踩坑换来的）

1. **贴片只留稀疏深色笔迹。** 先直方图铅笔灰度，排线晕染（灰 120-200）alpha 全归零：
   `light≈155 + gamma1.3`，而不是直觉的 205。验收参照：达标贴片的非透明像素只有
   数千级（星辉魔女左眼贴片仅 ~627 像素）。
2. **窗口贴紧五官。** 每多一寸，就多切断一根描摹笔画、多带一块石墨。
3. **选择性聚光，绝不全图压暗。** 面部 0.8 manim 单位内笔画保持全实，只把远处压到
   stroke opacity 0.12。全图压暗 = 贴片孤悬纸上，边界必然显眼。
4. **切片内细线重描。** 眼窗内的深色笔画提取成独立笔画源（`--erase-ellipse`
   挖掉双眼——挡眼不描），场景里用与全图一致的 `adaptive_widths` 墨线
   `Create` 出来，盖住贴片里的铅笔细线。
5. **上色要浸润不要贴纸。** 先铺 full 全图 32% 淡彩打底，分区色层依次加深，
   最后 full 定妆；分区层 = 人物多边形蒙版 + HSV 条件、排他化认领、余色全图兜底。

## 快速上手

```bash
# 0) 依赖（manim-handdraw 必须 ≥0.1.1）
pip install "manim-handdraw[extract]>=0.1.1"
python3 scripts/check_environment.py

# 1) 贴片（透明 RGBA + placement.json，含精确切割窗口）
python3 scripts/make_sparse_patch.py --mode patch \
  --pencil pencil_raw.png --output assets/eyes_ink.png \
  --box 630 178 830 300 --scene-height 7.6 --scene-center 0 -0.05

# 2) 重描源（全画布透明笔画图，双眼挖空）
python3 scripts/make_sparse_patch.py --mode retrace \
  --pencil pencil_raw.png --output assets/bangs_source.png \
  --box 630 178 830 300 \
  --erase-ellipse 670 252 46 40 --erase-ellipse 785 255 44 42

# 3) 渲染（必须用包装脚本：沙箱批量删除保护解药）
python3 scripts/render_safe.py -qh my_scene.py MyScene
```

场景侧三个关键片段（完整可运行示例见 [`examples/yefeng/`](examples/yefeng/)）：

```python
# a) 切段 + 保险丝断言（反向 y 窗口会静默失效，必须验证）
strokes = strokes.cut_out_rectangles([EYES_WIN, MOUTH_WIN])
assert 残留笔画点数 == 0

# b) 选择性聚光
dim = [m for m in ink_layer if dist(m, FOCUS) >= 0.80]
self.play(camera_zoom, *[m.animate.set_stroke(opacity=0.12) for m in dim])

# c) 重描（眼贴片淡入后）
strands = hd.from_image("assets/bangs_source.png", size=SIZE, center=CENTER,
                        merge_gap=18, merge_angle=0.25, clean_short=5)
widths = strands.adaptive_widths(regular=2.4, fine=1.9)
self.play(*[Create(hd.stroke_mobject(p, stroke_width=w).set_z_index(26))
            for p, w in zip(strands.paths, widths)], run_time=1.8)
```

## 目录结构

```
manim-facepatch-creator/
├── README.md / README_EN.md      ← 本文件
├── SKILL.md                       ← AI 助手可读的技能卡（五条核心 + 步骤）
├── scripts/
│   ├── check_environment.py       ← 环境自检
│   ├── make_sparse_patch.py       ← 贴片(patch) / 重描源(retrace) 双模式
│   ├── render_safe.py             ← 渲染包装：批量删除保护解药（必用）
│   └── review_frames.py           ← 成片抽帧自检
├── references/pitfalls.md         ← 14 条实测坑位速查（渲染 5 + 素材 9）
└── examples/yefeng/               ← 完整案例：可抄参数 + 场景源码 + 演示 GIF
```

## 案例：从"一眼假"到"看不出痕迹"的四轮迭代

| 版本 | 用户反馈 | 修了什么 |
| --- | --- | --- |
| v1 | 线条乱 / 背景色错 / 眼睛半贴半残 | （起点） |
| v2 | 及格；贴片有方形边框；上色突兀 | 线稿重做、色层蒙版重做、官方切段 |
| v3 | 贴片还是看得出贴的 | 阈值砍灰调 + 窗口收紧 + **选择性聚光**（真病根） |
| v4 | **完全看不出痕迹** ✅ | **重描**：眼窗笔画提取 + 双眼挖空 + 同宽墨线 |

完整踩坑记录见 [`references/pitfalls.md`](references/pitfalls.md)——
含沙箱渲染被批量删除保护 1 秒打死、partial 缓存串味导致素材改了不生效、
字幕出画、色层变黑剪影等每一个都值一晚上的坑。

## 相关项目

- [manim-handdraw](https://github.com/FTZ-OPUS/manim-handdraw) —— 笔画引擎库
  （bitmap 线稿 → 渐进手书动画）
- [manim-handdraw-creator](https://github.com/FTZ-OPUS/manim-handdraw-creator) —— 手书全流程核心技能包（对齐/描摹/构造/上色/收尾）
- 参考审美基准：紫发女骑士、火焰女王、星辉魔女、秩序神女系列成片
