#!/usr/bin/env python3
"""离线生成质量评测 —— 用 validate() + 关键指令检查给生成结果打分。

用法：
  python scripts/eval.py                        # 跑全部用例
  python scripts/eval.py --cases irc5p_zigzag   # 只跑某些用例（逗号分隔）
  python scripts/eval.py --no-few-shot          # 关 few-shot 做对比
  python scripts/eval.py --json-out out.json    # 导出明细

需要 Ollama 在运行且模型已拉取（见 abb-agent doctor）。
CPU 推理较慢，建议先用 --cases 跑子集。
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from abb_agent.agent import Agent  # noqa: E402
from abb_agent.eval.harness import load_cases, score_generation, summarize  # noqa: E402


def _mark(ok: bool) -> str:
    return "[green]✓[/green]" if ok else "[red]✗[/red]"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成质量评测")
    parser.add_argument("--cases", help="逗号分隔的用例 id 子集")
    parser.add_argument("--no-few-shot", action="store_true", help="关闭 few-shot 对比")
    parser.add_argument("--json-out", help="把明细写到 JSON 文件")
    args = parser.parse_args()

    cases = load_cases()
    if args.cases:
        want = {c.strip() for c in args.cases.split(",") if c.strip()}
        cases = [c for c in cases if c.id in want]
    if not cases:
        print("没有匹配的用例")
        return 1

    console = Console()
    label = " (no few-shot)" if args.no_few_shot else " (few-shot on)"
    console.print(f"[bold]评测 {len(cases)} 个用例{label}[/bold]")

    scores = []
    with Agent() as agent:
        for case in cases:
            console.print(f"[dim]running[/dim] {case.id} ({case.controller}) …")
            result = agent.generate_code(
                case.query,
                controller=case.controller,
                include_few_shot=not args.no_few_shot,
            )
            scores.append(
                score_generation(
                    case,
                    result.code,
                    result.validation,
                    category=result.rewritten_query.category.value,
                    duration_ms=result.duration_ms,
                    model=result.model_used,
                )
            )

    table = Table(title="评测结果" + label)
    for col in ("用例", "控制器", "校验", "含关键指令", "无禁用项", "类别", "通过", "耗时"):
        table.add_column(col)
    for case, s in zip(cases, scores, strict=True):
        inc = _mark(s.includes_ok) + (f" 缺{list(s.missing)}" if s.missing else "")
        exc = _mark(s.excludes_ok) + (f" 漏{list(s.leaked)}" if s.leaked else "")
        table.add_row(
            s.case_id, case.controller, _mark(s.valid), inc, exc,
            _mark(s.category_ok), _mark(s.passed), f"{s.duration_ms}ms",
        )
    console.print(table)

    summary = summarize(scores)
    console.print(
        f"通过 [bold]{summary.passed}/{summary.total}[/bold] "
        f"(pass_rate={summary.pass_rate:.0%}, valid_rate={summary.valid_rate:.0%})"
    )

    if args.json_out:
        import json

        Path(args.json_out).write_text(
            json.dumps([asdict(s) for s in scores], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        console.print(f"明细已写入 {args.json_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
