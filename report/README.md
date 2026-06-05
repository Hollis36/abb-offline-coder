# 项目研究报告（人工智能创新赛）

本目录是 **abb-offline-coder** 参加「人工智能创新赛」的项目研究报告。

- **队伍名称**：人工智能创新001
- **比赛赛项**：人工智能创新赛

本目录含九份参赛材料：

| 文件 | 内容 | 规格 |
|------|------|------|
| [`main.tex`](main.tex) / [`main.pdf`](main.pdf) | **项目研究报告**（背景 · 架构 · 关键技术 · 创新点 · 实测 · 实拍配图 · 终端实录） | A4 · 20 页 |
| [`evidence.tex`](evidence.tex) / [`evidence.pdf`](evidence.pdf) | **项目佐证材料**（Git 历史 · 单元测试实跑 · 覆盖率 · 核心能力实证 · 真实产物 · 公开发布物料） | A4 · 8 页 |
| [`poster.tex`](poster.tex) / [`poster.pdf`](poster.pdf) | **项目一图流海报**（答辩展板 / 路演，一眼看全） | A4 横版 · 1 页 |
| [`slides.tex`](slides.tex) / [`slides.pdf`](slides.pdf) | **答辩幻灯**（Beamer 16:9，10 页内） | 16:9 · 10 页 |
| [`slides_notes.tex`](slides_notes.tex) / [`slides_notes.pdf`](slides_notes.pdf) | **答辩幻灯·演讲者备注版**（每页 幻灯+备注 并排，供 pdfpc/双屏演讲者模式或排练） | 双宽 · 10 页 |
| [`script.tex`](script.tex) / [`script.pdf`](script.pdf) | **答辩讲稿**（逐页口语稿 + 舞台提示 + 预设问答 Q&A） | A4 · 3 页 |
| [`online_defense_guide.tex`](online_defense_guide.tex) / [`online_defense_guide.pdf`](online_defense_guide.pdf) | **在线答辩指南 & 检查清单**（屏幕共享策略 · 线上现场演示 · 线下→线上表达 · 赛前清单） | A4 · 2 页 |
| [`combined.tex`](combined.tex) / [`combined.pdf`](combined.pdf) | **合订本**（研究报告 + 佐证材料附录） | A4 · 29 页 |
| [`full_package.tex`](full_package.tex) / [`full_package.pdf`](full_package.pdf) | **全套提交包**（报告 + 佐证 + 海报 + 幻灯，单文件提交用） | A4/横版/16:9 · 42 页 |

> 佐证材料中的单元测试与覆盖率均为**可复现实测**（156 个用例全部通过，无需 GPU/Ollama）；
> 知识库/端到端等数据标注为「项目记录」，来源于 `PROJECT_STATUS.md` / `EXECUTION_LOG.md`。

## 编译方式

两份材料均为中文，需用 **XeLaTeX** 编译（依赖 `ctex` 宏包 + Noto CJK 字体）。
为生成目录与交叉引用，请各运行两次：

```bash
xelatex main.tex     && xelatex main.tex       # 研究报告（两次：目录/交叉引用）
xelatex evidence.tex && xelatex evidence.tex   # 佐证材料（需能读到 ../docs/screenshots/*.png）
xelatex poster.tex                             # 海报（一次即可）
xelatex slides.tex   && xelatex slides.tex     # 答辩幻灯（Beamer）
xelatex slides_notes.tex && xelatex slides_notes.tex  # 演讲者备注版（幻灯+备注并排）
xelatex script.tex   && xelatex script.tex     # 答辩讲稿
xelatex online_defense_guide.tex && xelatex online_defense_guide.tex  # 在线答辩指南
# 合订本/全套包：须先生成 main/evidence(/poster/slides).pdf，再编译两次（分隔页 overlay 需二次定位）
xelatex combined.tex     && xelatex combined.tex      # 合订本（报告+佐证）
xelatex full_package.tex && xelatex full_package.tex  # 全套提交包（报告+佐证+海报+幻灯）
```

或使用 `latexmk`：

```bash
latexmk -xelatex main.tex && latexmk -xelatex evidence.tex
latexmk -xelatex poster.tex && latexmk -xelatex slides.tex
latexmk -xelatex combined.tex
```

### 依赖

- TeX 发行版（TeX Live / MiKTeX），含 `ctex`、`tikz`、`listings`、`booktabs`、`pifont` 等宏包
- 中文字体：**Noto Serif/Sans/Sans Mono CJK SC**（Ubuntu 可装 `fonts-noto-cjk`）

> 若使用其它中文字体，可修改 `main.tex` 开头的 `\setCJKmainfont` 等三行。

## 报告结构

1. 项目背景与选题意义（行业痛点 · 离线机遇）
2. 相关工作与对比
3. 系统总体设计（四层架构 · 六级流水线 · 技术栈）
4. 关键技术与实现（查询改写 · 混合检索 · 本地 LLM · 生成—校验闭环 · 双控制器 · Pack&Go）
5. 创新点总结
6. 工程质量与实测
7. 应用案例（车门 Z 字喷涂 · IRC5 vs IRC5P）
8. 安全、合规与伦理
9. 局限性与未来工作
10. 结论
