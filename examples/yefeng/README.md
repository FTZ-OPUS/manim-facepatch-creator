# 案例：《飓风战魂》叶枫（v4，用户验收"完全看不出痕迹"）

主项目《飓风战魂》叶枫手书（本地项目）：铅笔稿 pencil_raw.png 1470×1070、
彩图 color_ref.png、成片 叶枫_手绘版_1080p60_v4.mp4；场景源码已复制到本目录
（yefeng_scene_v4.py），素材由本文参数 + make_sparse_patch.py 一键复现。

## 关键参数（可直接抄）

### 线稿（连贯 188 笔，背景杂痕零残留）
- 阈值 150 + `merge_gap=36, merge_angle=0.15, clean_short=12`
- 27 组参数实验 + 静态预览择优（t150/g36 最干净，t165 带石墨噪点）
- 人物多边形膨胀 60px 之外 alpha 全清（按区域擦，不按笔画长度）

### 五官贴片（稀疏深色笔迹）
```
python3 scripts/make_sparse_patch.py --mode patch \
  --pencil pencil_raw.png --output assets_v4/eyes_ink.png \
  --box 630 178 830 300 --scene-height 7.6 --scene-center 0 -0.05 \
  --dark 100 --light 155 --gamma 1.3 --r0 0.75
# 嘴巴：--box 698 296 766 350（其余同）
```
- 眼贴片非透明像素 10372 → 5714（灰调全砍），对齐魔女"稀疏"观感
- 窗口上缘 170→178：贴着眉毛，少切断额发

### 重描（消粗细不匹配，v4 的关键一步）
```
python3 scripts/make_sparse_patch.py --mode retrace \
  --pencil pencil_raw.png --output assets_v4/bangs_source.png \
  --box 630 178 830 300 \
  --erase-ellipse 670 252 46 40 --erase-ellipse 785 255 44 42
```
场景里（眼贴片淡入后、嘴贴片之前）：
```python
strands = hd.from_image(os.path.join(A, "bangs_source.png"), size=SIZE,
                        center=CENTER, merge_gap=18, merge_angle=0.25, clean_short=5)
sw = strands.adaptive_widths(regular=2.4, fine=1.9)
anims = []
for p, w in zip(strands.paths, sw):
    mob = hd.stroke_mobject(p, color=hd.INK, stroke_width=w).set_z_index(26)
    anims.append(Create(mob)); ink_layer.append(mob)
self.play(*anims, run_time=1.8, rate_func=linear)
```

### 选择性聚光（Act 3 特写）
```python
dim_mobs = [m for m in ink_layer if not isinstance(m, ImageMobject)
            and np.linalg.norm(m.points[:, :2] - FOCUS[:2], axis=1).min() >= 0.80]
spot = [camera.zoom] + [m.animate.set_stroke(opacity=0.12) for m in dim_mobs]
# 拉远时逐笔 set_stroke(opacity=1.0) 恢复；不要全图压到 0.04！
```

### 浸润式上色（11 阶段）
1. `full_wash.png` = full 全图 alpha 82 (32%) 预乘烘焙，打底
2. lay_flame → lay_night → lay_bgrest（背景三层，bgrest 全图兜底）
3. lay_skin → lay_hair → lay_white → lay_navy → lay_red → lay_gold（人物六层）
4. full.png 定妆 → 墨线与 partials 一并收
- 色层生成：人物多边形蒙版 + HSV 条件、排他化认领（skin/gold/red 先行）

## 迭代史（每版差在哪）

| 版本 | 用户反馈 | 修了什么 |
| --- | --- | --- |
| v1 | 线条乱/背景色错/眼睛半贴半残 | （上一任）未过 |
| v2 | 及格；贴片有方形边框；上色突兀 | 线稿重做 188 笔、色层蒙版重做、官方切段 |
| v3初 | 贴片还是看得出贴的 | 阈值砍灰调(10372→5714) + 窗口收紧 + **选择性聚光**（真病根） |
| v3终 | 贴片刘海粗细与墨线不匹配 | **重描**：眼窗笔画提取+双眼挖空+同宽墨线 Create |
| v4 | 完全看不出痕迹 ✅ | — |

## 本案例的渲染命令

```bash
cd "/Users/fengtianzhu/Desktop/《飓风战魂》叶枫手书"
mv media/videos/yefeng_scene_v4 media/videos/_stale 2>/dev/null   # 换新防缓存串味
python3 render_safe.py -ql 8 yefeng_scene_v4.py                   # 自检（~40s）
python3 render_safe.py -qh yefeng_scene_v4.py                     # 成片 1080p60（~5-7min）
```
