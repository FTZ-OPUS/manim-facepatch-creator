---
name: manim-facepatch-creator
description: 让手书动画里的五官贴片"完全看不出贴的痕迹"——稀疏深色笔迹贴片、超椭圆径向羽化、选择性聚光、刘海重描、浸润式上色，以及本机渲染的全部坑位解药。基于《飓风战魂》叶枫 v4（用户验收"完全看不出来痕迹"）沉淀。
---

# Manim 五官贴片隐形技能包

手书动画（铅笔稿描摹 + 原图上色）中，五官用铅笔稿贴片复刻。贴片做得不好
会一眼看出"复制粘贴"。本包沉淀了从"一眼假"到"完全看不出来"的完整方法，
主案例：《飓风战魂》叶枫（v4，用户原话"完全看不出来了痕迹"）。

## 前置

- 动画库 `manim-handdraw` **必须 ≥0.1.1**（`cut_out_rectangles`/`adaptive_widths`/
  缓存校验都在这版）。venv 里装着 0.1.0 editable 时 `pip install manim-handdraw==0.1.1`。
  先跑 `scripts/check_environment.py` 确认。
- 配套大包：`/Users/fengtianzhu/Desktop/manim-handdraw-creator/`（对齐、prepare_pair、
  质量标准）。本包只管"贴片隐形 + 重描 + 上色过渡 + 渲染坑"这一段。
- 输入约定：已对齐的铅笔稿（贴片与线稿的唯一来源）+ 对齐彩图（上色来源）。

## 核心方法（五条，缺一就"假"）

1. **贴片只留稀疏深色笔迹。** 先直方图铅笔灰度：排线晕染（灰 120-200）alpha 全归零，
   `light≈155 + gamma1.3`，不是默认 205。验收参照：魔女左眼贴片仅 ~627 个非透明像素。
2. **窗口贴紧五官**，每多一寸就多切断一根描摹笔画、多带一块石墨。
3. **选择性聚光，绝不全图压暗。** 面部 0.8 manim 单位内笔画保持全实，只压远处到
   stroke opacity 0.12。全图压暗 = 贴片孤悬纸上，边界必显眼。
4. **切片内细线重描。** 贴片里的铅笔细线比全图墨线细 → 粗细不匹配即穿帮。
   把眼窗内深色笔画提取成独立笔画（挖掉双眼椭圆，挡眼不描），
   用与全图一致的 adaptive_widths 重新描出，盖住铅笔细线。
5. **上色要"浸润"不要"贴纸"。** 先铺 full 全图 32% 淡彩打底 → 分区色层依次加深
   → full 定妆。分区层 = 人物多边形蒙版 + HSV 条件、排他化认领、背景全兜底。

## 使用步骤

1. 环境：`python3 scripts/check_environment.py`
2. 贴片：`python3 scripts/make_sparse_patch.py --mode patch --pencil pencil_raw.png
   --output assets/eyes_ink.png --box X0 Y0 X1 Y1 --scene-height 7.6 --scene-center 0 -0.05`
   （写 placement.json，含精确切割窗口 → 场景用 `StrokeSet.cut_out_rectangles()`
   切段并断言窗口内残留=0）
3. 重描源：同脚本 `--mode retrace --erase-ellipse 左眼CX CY RX RY --erase-ellipse 右眼…`
   产出全画布透明笔画图，场景里 `hd.from_image` 提取后用 Create 重描。
4. 渲染：**必须用 `scripts/render_safe.py` 包装**（沙箱批量删除保护解药），且每次渲染前
   把 `media/videos/<场景>` 目录改名换新——manim 会复用旧 partial 缓存，同名图片素材
   改了内容也不生效。
5. 自检：`scripts/review_frames.py <video>` 均匀抽帧，重点看特写、上色、结尾三段。

## 坑位速查（全部实测踩过）

详见 [references/pitfalls.md](references/pitfalls.md)。渲染类：沙箱批量删除保护、
partial 缓存串味、8fps 低画质时长偏长属正常、结尾镜头移动后字幕出画。
素材类：色层必须带原图 RGB、bgrest 全图兜底、石墨杂痕按区域擦不按笔画长度。
完整案例见 [examples/yefeng/README.md](examples/yefeng/README.md)。
