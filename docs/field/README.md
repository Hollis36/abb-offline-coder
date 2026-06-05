# 现场照片素材（docs/field/）

放\*\*真实喷涂机器人现场照片\*\*的目录，用于嵌入答辩幻灯 / 研究报告 / 海报的「真实应用现场」部分。

> ⚠️ 注意：这些是**位图照片**，必须以**文件**形式放进本目录，AI 才能 `\includegraphics` 进 LaTeX。
> 对话里粘贴的图片**不会**自动落盘，需要你显式提交到仓库。

## 一、怎么把照片放进来（任选其一）

**方式 A · 本地 git（最快）**
```bash
# 在你本机的仓库目录里
mkdir -p docs/field
cp /你的照片/*.jpg docs/field/          # 重命名为 field-01.jpg, field-02.jpg ...
git add docs/field/*.jpg
git commit -m "assets(field): add on-site spray-cell photos"
git push origin claude/dazzling-noether-AHbRH
```

**方式 B · GitHub 网页上传（无需命令行，手机/电脑浏览器都行）**
1. 打开仓库 → 切到分支 `claude/dazzling-noether-AHbRH`
2. 进入 `docs/field/` 目录 → 右上角 **Add file → Upload files**
3. 把照片拖进去（命名 `field-01.jpg` … 任意顺序均可）→ **Commit**

提交后告诉我「照片已推送」，我会 `git pull` 拉取、挑选、裁剪并嵌入。

## 二、命名建议

- 直接按顺序命名即可：`field-01.jpg`、`field-02.jpg` …（顺序无所谓，**我来挑选/裁剪**）
- JPG / PNG 均可；手机原图即可（我会统一缩放，无需你处理）

## 三、我的初步选用计划（看过你发的 10 张后）

拟选 **4 张**，组成一页新幻灯「真实应用现场：喷涂机器人落地场景」，并可分发到报告应用案例节、海报：

| 角色 | 选用内容 | 拟配中文图注 |
|------|----------|--------------|
| 现场全景 | 玻璃喷房 + 防护套机器人 + 黄色喷枪 + 绿色格栅工装台 | 真实喷涂机器人工作站（物理隔离、无网玻璃喷房） |
| 机器人作业 | 机器人持枪对准工件、喷枪朝下特写 | 机器人执行本工具生成的 RAPID 程序喷涂工件 |
| 喷涂成品 | 浅绿色光泽漆面平板工件 | 本工具生成程序喷涂的成品（漆面均匀、光泽一致） |
| 质量检测 | 手持涂层测厚仪测量，读数 61.3 μm（另有 45.9 μm） | 成品膜厚检测：多点 45.9–61.3 μm |

> 若你想要不同的取舍（比如想突出某张），推送后告诉我即可，我按你的偏好调整。

## 四、真实性措辞（已确认）

队伍已确认：这些照片**确为本工具生成的 RAPID 程序在该工作站实际运行 / 喷涂成品质检**所摄。
因此图注按\*\*「本工具生成程序的现场运行实景」\*\*口径表述（见上表），并在幻灯落一句：
「图为本工具生成的 RAPID 喷涂程序在真实（物理隔离、无网）喷涂车间的现场运行与成品质检。」

## 五、我拿到文件后会做的处理

1. `imagemagick` 统一裁剪/缩放、必要时去除背景杂物或路人；
2. 配中文图注，做成「真实应用现场」幻灯（拟为放映版与备注版各加一页）；
3. 视需要再放 1 张到研究报告应用案例节、1 张到海报；
4. 重新生成合订本 / 全套提交包（内嵌更新后的幻灯与报告）；
5. 桌面打包同步刷新。

## 六、待集成的幻灯片代码（拿到照片后启用）

新幻灯将加在「应用案例」之后，示意如下（最终以实际照片为准）：

```latex
% 需在 slides.tex 序言加： \graphicspath{{../docs/screenshots/}{../docs/field/}}
\begin{frame}{真实应用现场：本工具生成程序的现场运行}
\begin{columns}[c]
  \begin{column}{0.25\textwidth}\centering
    \includegraphics[height=4.3cm]{field-cell.jpg}\\{\scriptsize 物理隔离、无网玻璃喷房}\end{column}
  \begin{column}{0.25\textwidth}\centering
    \includegraphics[height=4.3cm]{field-robot.jpg}\\{\scriptsize 机器人执行本工具生成的程序喷涂}\end{column}
  \begin{column}{0.25\textwidth}\centering
    \includegraphics[height=4.3cm]{field-part.jpg}\\{\scriptsize 喷涂成品（漆面均匀）}\end{column}
  \begin{column}{0.25\textwidth}\centering
    \includegraphics[height=4.3cm]{field-qc.jpg}\\{\scriptsize 成品膜厚检测 45.9–61.3\,$\mu$m}\end{column}
\end{columns}
\vspace{4pt}
{\footnotesize 图为本工具生成的 RAPID 喷涂程序在真实（物理隔离、无网）喷涂车间的现场运行与成品质检——印证「完全离线」定位真实落地。}
\end{frame}
```
