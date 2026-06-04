# 项目研究报告（人工智能创新赛）

本目录是 **abb-offline-coder** 参加「人工智能创新赛」的项目研究报告。

- **队伍名称**：人工智能创新001
- **比赛赛项**：人工智能创新赛

本目录含五份参赛材料：

| 文件 | 内容 | 规格 |
|------|------|------|
| [`main.tex`](main.tex) / [`main.pdf`](main.pdf) | **项目研究报告**（背景 · 架构 · 关键技术 · 创新点 · 实测 · 实拍配图 · 终端实录） | A4 · 20 页 |
| [`evidence.tex`](evidence.tex) / [`evidence.pdf`](evidence.pdf) | **项目佐证材料**（Git 历史 · 单元测试实跑 · 覆盖率 · 核心能力实证 · 真实产物 · 公开发布物料） | A4 · 8 页 |
| [`poster.tex`](poster.tex) / [`poster.pdf`](poster.pdf) | **项目一图流海报**（答辩展板 / 路演，一眼看全） | A4 横版 · 1 页 |
| [`slides.tex`](slides.tex) / [`slides.pdf`](slides.pdf) | **答辩幻灯**（Beamer 16:9，10 页内） | 16:9 · 10 页 |
| [`combined.tex`](combined.tex) / [`combined.pdf`](combined.pdf) | **合订本**（研究报告 + 佐证材料附录，单文件提交用） | A4 · 29 页 |

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
# 合订本：须先生成 main.pdf 与 evidence.pdf，再编译两次（封面分隔页用 overlay 需二次定位）
xelatex combined.tex && xelatex combined.tex
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
