# 项目研究报告（人工智能创新赛）

本目录是 **abb-offline-coder** 参加「人工智能创新赛」的项目研究报告。

- **队伍名称**：人工智能创新001
- **比赛赛项**：人工智能创新赛
- 源文件：[`main.tex`](main.tex)（LaTeX，`ctexart` 中文排版）
- 成品：[`main.pdf`](main.pdf)（17 页）

## 编译方式

报告使用中文，需用 **XeLaTeX** 编译（依赖 `ctex` 宏包 + Noto CJK 字体）。
为生成目录与交叉引用，请运行两次：

```bash
xelatex main.tex
xelatex main.tex
```

或使用 `latexmk`：

```bash
latexmk -xelatex main.tex
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
