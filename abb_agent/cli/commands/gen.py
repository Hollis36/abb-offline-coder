"""gen 子命令：单次生成 RAPID 代码。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from abb_agent.agent import Agent
from abb_agent.config import get_config

app = typer.Typer(help="单次生成 RAPID 代码")
console = Console()


def _default_output_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return get_config().paths.output_dir / f"PaintProgram_{ts}.mod"


@app.callback(invoke_without_command=True)
def gen_default(
    query: str = typer.Argument(..., help="中文需求描述"),
    output: Path = typer.Option(
        None, "--output", "-o", help="输出 .mod 文件路径（默认 output/PaintProgram_*.mod）"
    ),
    no_few_shot: bool = typer.Option(False, "--no-few-shot", help="禁用 few-shot 示例（更快但效果差）"),
    show_context: bool = typer.Option(False, "--show-context", help="显示检索到的上下文"),
) -> None:
    """单次生成代码。"""
    out_path = output or _default_output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with Agent() as agent:
        console.print(Panel.fit(f"[bold cyan]需求:[/bold cyan] {query}"))
        with console.status("正在检索 + 生成代码..."):
            result = agent.generate_code(
                query,
                save_to=out_path,
                include_few_shot=not no_few_shot,
            )

    console.rule("[bold]生成结果[/bold]")
    console.print(Syntax(result.code, "rapid", theme="monokai", line_numbers=True, word_wrap=True))

    if result.explanation:
        console.rule("[bold]说明[/bold]")
        console.print(result.explanation)

    if show_context:
        console.rule("[bold]检索上下文[/bold]")
        console.print(result.context.text[:1500] + ("..." if len(result.context.text) > 1500 else ""))

    console.rule("[bold]校验报告[/bold]")
    console.print(result.validation.format_summary())

    console.rule("[bold]统计[/bold]")
    console.print(f"模型: {result.model_used}")
    console.print(f"耗时: {result.duration_ms} ms")
    console.print(f"任务类别: {result.rewritten_query.category.value}")
    console.print(f"已保存到: [green]{out_path}[/green]")
