# 答辩幻灯配图 · 专业提示词集（abb-offline-coder）

> 目标：为文字偏多的幻灯页（解决方案 / 行业痛点 / 双控制器 / 创新点 / 关键技术）补充
> **统一风格的矢量概念图与图标**。所有图遵循同一套品牌风格，保证"成套感"。
>
> ⚠️ 真实性原则：本套幻灯已含**工厂真实照片**（机器人 / 成品 / 膜厚检测）。下列均为
> **概念示意图（非写实）**，请与真实照片分区使用——真实照片所在页不要混入 AI 生成图，
> 避免"真假难辨"削弱可信度。

---

## 0. 通用风格基底（每条提示词都追加这一段）

**STYLE（正向，统一风格）**
```
flat vector infographic illustration, minimalist and clean, light isometric feel,
brand palette = warm orange #D94A1F as the ONLY accent + charcoal #1C1C1C line work
on a soft warm-gray #F6F2F0 or transparent background; uniform 2–3px rounded strokes,
rounded corners, generous negative space, balanced centered composition,
modern engineering/keynote aesthetic, crisp, high-resolution.
```

**NEGATIVE（负面，务必带上）**
```
no text, no letters, no numbers, no words, no captions, no labels, no logo, no watermark,
no signature; NOT photorealistic, no 3D render, no glossy gradients, no drop shadows,
no neon, no clutter, no busy background, no realistic human faces, no stock-photo look.
```

> 文字一律不入图——中文图注我在 LaTeX 里加，保证字体统一、随时可改。

---

## 1. 核心价值流（用于「解决方案与定位」页 · 主图）　比例 3:2 / 宽图

```
A clean left-to-right value pipeline. Far left: a rounded speech bubble suggesting a
short spoken sentence (use 2–3 small horizontal bars instead of real text). A bold arrow
leads into a central rounded-rectangle "engine" card containing three stacked mini line-
icons: a magnifier over a stack of documents (knowledge retrieval), a microchip-brain
hybrid (local language model), and a shield with a check mark (validation). A small
circular badge with a crossed-out Wi-Fi symbol sits on the engine corner to signal
"offline". From the engine, an arrow points to a file marked with angle brackets
(generated code), then a final arrow to a simplified six-axis industrial robot arm
holding a spray nozzle emitting a soft fan of dots. Accent color highlights the arrows,
the offline badge and the spray. + [STYLE] + [NEGATIVE]
```

## 2. 离线 vs 云端 对比（用于「解决方案」或「行业痛点」页）　比例 3:2

```
A balanced split-screen contrast with a thin vertical divider. LEFT half (muted charcoal,
marked with a small prohibited circle): a cloud icon with a broken/cut connection line and
a tiny data packet escaping outward past a dashed factory boundary — cloud AI that leaks
data and cannot reach the floor. RIGHT half (orange accent): a compact spray-booth/factory
outline wrapped in a protective shield, a small server/chip inside, all data arrows looping
back within the shield, plus an offline crossed-Wi-Fi badge — the on-prem, data-never-leaves
approach. + [STYLE] + [NEGATIVE]
```

## 3. 行业痛点 · 四图标（用于「行业痛点」页 · 配 4 条要点）　各 1:1 透明，一排四枚

```
One row of FOUR matching flat line icons, identical stroke weight, size and corner radius,
charcoal lines with one orange accent each, transparent background:
(a) a stack of books topped with a gear — steep专业 threshold;
(b) a robot arm tip meeting a warning triangle with a small collision spark — costly trial / crash;
(c) a single person silhouette beside a clock with a long sweep — slow, human-dependent;
(d) a spray booth/enclosure with a crossed-out Wi-Fi glyph — offline, isolated workshop.
Evenly spaced, consistent visual language. + [STYLE] + [NEGATIVE]
```

## 4. RAG 知识注入（用于「关键技术」左半）　比例 3:2 / 1:1

```
A knowledge-injection concept. Left: a small shelf of manuals/PDF documents. Arrow into a
funnel/sieve marked with a magnifier (hybrid retrieval) that distills the documents into a
few highlighted snippet cards. Those snippets flow as an arrow INTO a prompt/speech bubble
that feeds a microchip-brain (the local model), which outputs a clean code file. Accent
color marks the distilled snippets being injected. Conveys "official manuals are retrieved
and injected so a small model does not hallucinate." + [STYLE] + [NEGATIVE]
```

## 5. 生成—校验 · 左移拦截（用于「关键技术」右半）　比例 3:2

```
A "shift-left safety gate" concept. A horizontal track flows from a code file on the left
toward an industrial robot on the right. Midway sits a sturdy gate/funnel shaped like a
shield; a few defective code blocks (small orange warning dots) are caught and bounced back
at the gate, while clean blocks pass through to the robot. A small clock/arrow motif shows
the error is caught EARLY (at generation) rather than late (on the machine). Shield and
caught defects use the accent color. + [STYLE] + [NEGATIVE]
```

## 6. 双控制器分支（用于「双控制器自适应」页）　比例 3:2

```
A "one input, two process styles" branching diagram. A single rounded node on the left with
a gear/controller glyph splits via two diverging arrows into two horizontal lanes. TOP lane:
a straight line-move path icon then a manual toggle switch (MoveL + manual IO on a generic
controller). BOTTOM lane: a spray/brush nozzle icon then a small data-table/recipe card
(native paint process with a brush-data table). Both lanes end at a matching small panel/part.
Accent color on the branch arrows and the two lane-defining icons. + [STYLE] + [NEGATIVE]
```

## 7. 创新点 · 七图标（用于「创新点总览」页）　各 1:1 透明

```
A set of SEVEN matching flat line icons, identical style, charcoal with one orange accent each,
transparent:
1 a globe/factory with crossed Wi-Fi (fully offline industrial code-gen);
2 a manual/book feeding a small brain (manual-grounded RAG, anti-hallucination);
3 a switch toggling between two controller boxes (dual-controller adaptive);
4 a shield with a check while a small bug is filtered out (generation–validation loop);
5 a folded package box with a deploy/play arrow (one-click loadable bundle);
6 a sealed box with a circular sync arrow (one-click offline migration);
7 a hard-hat plus a review check (built-in safety guardrails). + [STYLE] + [NEGATIVE]
```

## 8. 封面/章节 Hero（可选 · 用于封面或提纲背景）　比例 16:9 宽、极淡

```
A wide airy hero banner: on the left a stylized speech bubble (abstract bars, no real text)
morphs along a dotted path into clean lines of bracketed code, which connect to a minimalist
six-axis spray-painting robot on the right; a faint offline/shield motif in the background.
Very light, lots of negative space, single orange accent, charcoal linework on warm-gray,
designed to sit BEHIND a title without competing with it. + [STYLE] + [NEGATIVE]
```

---

## 9. 给 codex（生成矢量代码，最推荐——可精确套色、零文字噪声）

把上面任意一条描述作为需求，追加这段指令：

```
Produce a standalone, self-contained TikZ picture (PGF/TikZ, about 8cm wide, no external
assets, compiles with XeLaTeX). Use ONLY these colors:
  \definecolor{acc}{HTML}{D94A1F}  % 主题橙
  \definecolor{ink}{HTML}{1C1C1C}  % 线条
  \definecolor{bg}{HTML}{F6F2F0}   % 浅底（或透明）
Build every icon from basic shapes/paths (rectangles, circles, lines, arrows). Keep it
vector and scalable. NO raster images, NO text labels (Chinese captions are added later in
LaTeX). Return only the tikzpicture code.
```

> 矢量（TikZ/SVG）相比 AI 位图的优势：①与品牌橙灰**像素级一致**；②**无文字乱码**；
> ③可无限缩放、PDF 内清晰；④与现有 TikZ 架构图/流水线图**风格统一**。

---

## 10. 使用规范（拿到图后怎么落地）

- **导出格式**：矢量优先（SVG / PDF）；若位图则**透明 PNG ≥ 2000px**。
- **比例**：宽图 3:2、半栏图 1:1 或贴合列宽；图标 1:1 透明、成排。
- **文字**：图内**不要文字**，中文图注统一在 LaTeX 里加（字体一致、可改）。
- **一致性**：所有图共用 §0 的 STYLE + NEGATIVE，确保整套风格统一。
- **落地**：把图丢进 `docs/slide-art/`，我来缩放、配橙灰细边框、加中文图注、排进对应页，并同步放映版/备注版与全套包。
- **真实性**：概念图与**真实照片分区**——「真实应用现场」页保持纯实拍，不混 AI 图。
