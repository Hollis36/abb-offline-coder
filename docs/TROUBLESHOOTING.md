# 故障排查 / 部署问题

> 本文收录在真实部署（含云服务器 / 虚拟机 / 容器 / 工业 PC）中遇到的典型问题与解决办法。
> 按「症状 → 原因 → 解决」组织，命令可直接复制。

---

## 1. Ollama 推理段错误（云 / 虚拟机 CPU 谎报 AMX）

**症状**：模型可以下载、`abb-agent doctor` 显示 Ollama 在线，但一旦真正推理（`abb-agent gen` 或直接 `curl /api/generate`）就报：

```
OllamaConnectionError: 生成请求失败: Server error '500 Internal Server Error'
```

查看 Ollama 服务日志可见：

```
llama-server process has terminated: signal: segmentation fault
```

且日志里 `system_info:` 一行包含 `AMX_INT8 = 1`。

**原因**：很多云主机 / 虚拟机的 CPUID **上报**支持 Intel AMX（`AMX_INT8`），但宿主 / 容器并没有为其启用 AMX tile 寄存器状态（XCR0 未配置）。Ollama 的 GGML 会按 CPUID 自动挑选 AMX 优化后端 `libggml-cpu-sapphirerapids.so`，可一执行 AMX 指令就触发段错误。

> 这是 **Ollama 构建 × 虚拟化 CPU** 的环境问题，**与本项目代码无关**。物理机或 AMX 正常启用的环境通常不会遇到。

**解决**：把 AMX 后端移走，让 GGML 回退到非 AMX 的 AVX512 / AVX2 后端：

```bash
# 1) 停掉 ollama 服务（按进程名精确匹配，避免误杀当前 shell）
pkill -x ollama; sleep 2

# 2) 把 AMX 后端移到一边（可逆，随时移回）
cd /usr/local/lib/ollama          # Linux 默认安装路径
mkdir -p _disabled_backends
mv libggml-cpu-sapphirerapids.so _disabled_backends/

# 3) 重启服务并验证
nohup ollama serve > /tmp/ollama-serve.log 2>&1 &
sleep 3
curl -s http://127.0.0.1:11434/api/generate \
  -d '{"model":"qwen2.5-coder:7b-instruct-q4_K_M","prompt":"reply: ok","stream":false,"options":{"num_predict":8}}'
```

返回 JSON 里出现 `"response": "..."`（HTTP 200）即修复成功。

**若仍崩溃**：说明该 CPU 上 AVX512 后端也不稳，继续把 AVX512 变体也移走，让它回退到 AVX2：

```bash
cd /usr/local/lib/ollama
mv libggml-cpu-{cascadelake,icelake,skylakex,cooperlake,zen4}.so _disabled_backends/ 2>/dev/null
# 之后会落到 libggml-cpu-haswell.so / -alderlake.so（AVX2，最稳）
```

恢复原状只需把文件从 `_disabled_backends/` 移回即可。

---

## 2. 纯 CPU 推理慢 / 请求超时

**症状**：`abb-agent gen` 跑很久后报 `生成请求失败: timed out`。

**原因**：无 GPU 时全靠 CPU 推理。瓶颈往往是**提示词处理**——完整 few-shot 提示约 4500 tokens，4 核 CPU 上 ~25 tok/s 就要 ~3 分钟，早超过默认 `timeout_seconds=120`。

**解决**（按需组合）：

```bash
# 调高单次请求超时（注意：单下划线前缀，见第 5 节）
export ABB_AGENT_LLM_TIMEOUT_SECONDS=900

# 减小提示词：禁用 few-shot（更快，质量略降）
abb-agent gen --no-few-shot "你的需求"

# 换更小的模型（3B，加载与推理都更快）
export ABB_AGENT_LLM_MODEL_NAME="qwen2.5-coder:3b-instruct-q4_K_M"
```

**性能小贴士**：给 Ollama 设 `OLLAMA_KEEP_ALIVE=-1`，模型加载后常驻内存，避免每次冷加载的几十秒开销：

```bash
OLLAMA_KEEP_ALIVE=-1 ollama serve
```

---

## 3. 安装 Ollama 报缺少 zstd

**症状**：`curl -fsSL https://ollama.com/install.sh | sh` 报：

```
ERROR: This version requires zstd for extraction.
```

**原因**：精简版 Linux（容器 / 最小化镜像）默认没装 `zstd` 解压工具。

**解决**：

```bash
sudo apt-get install -y zstd      # Debian / Ubuntu
sudo dnf install -y zstd          # RHEL / CentOS / Fedora
sudo pacman -S zstd               # Arch
# 然后重新跑 install.sh
```

---

## 4. 向量库为空（doctor 显示 △）

**症状**：`abb-agent doctor` 的「向量库」一行是 `△ 空`。

**原因**：仓库**不附带** ABB 手册（`data/raw/` 已 gitignore，避免版权问题）。库为空时仍可生成，只是少了 RAG 检索增强，靠内置 few-shot。

**解决**：把资料放入对应目录后建库：

```bash
#   data/raw/pdf/   - RAPID Reference Manual / Application Manual 等
#   data/raw/code/  - 历史 .mod / .sys 示例
#   data/raw/html/  - 离线保存的 HTML 文档
abb-agent kb build
abb-agent kb status            # 确认切片数 > 0
abb-agent kb inspect "Z 字喷涂"  # 测试检索质量
```

---

## 5. 环境变量覆盖不生效

**症状**：`export ABB_AGENT_LLM__MODEL_NAME=...` 后模型没换。

**原因**：`LLM` / `EMBED` 子配置各自带 `env_prefix`，只认**单下划线**前缀。**双下划线**会被 pydantic-settings 静默忽略。

**解决**：用单下划线：

```bash
export ABB_AGENT_LLM_MODEL_NAME="qwen2.5-coder:3b-instruct-q4_K_M"   # ✅
export ABB_AGENT_LLM_TEMPERATURE=0.4                                  # ✅
export ABB_AGENT_EMBED_DEVICE="cuda"                                 # ✅
# 验证：
python -c "from abb_agent.config import get_config as g; print(g().llm.model_name)"
```

---

## 6. 连接 Ollama 被拒（Connection refused）

**症状**：`无法连接 Ollama: [Errno 111] Connection refused`。

**原因**：Ollama 服务没起，或被回收（在临时容器 / 会话里后台进程可能不持久）。

**解决**：

```bash
ollama serve                                   # 前台常驻（推荐新开一个终端）
# 或后台：
nohup ollama serve > /tmp/ollama-serve.log 2>&1 &
curl -s http://127.0.0.1:11434/api/tags        # 确认在线
```
