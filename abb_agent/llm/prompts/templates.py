"""Prompt 模板加载与渲染。

system.md / painting_few_shot.md 用 importlib.resources 打包进 wheel，
保证发布后仍能加载。
"""
from __future__ import annotations

from functools import lru_cache
from importlib import resources

from abb_agent.rag.context_builder import BuiltContext
from abb_agent.rag.query_rewriter import RewrittenQuery


@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    # encoding="utf-8" 显式声明，避免 Windows 默认 cp1252/cp936 解码中文 prompt 报错
    return resources.files("abb_agent.llm.prompts").joinpath("system.md").read_text(
        encoding="utf-8"
    )


@lru_cache(maxsize=1)
def _load_few_shot() -> str:
    return resources.files("abb_agent.llm.prompts").joinpath("painting_few_shot.md").read_text(
        encoding="utf-8"
    )


def build_full_prompt(
    user_query: RewrittenQuery,
    context: BuiltContext,
    *,
    include_few_shot: bool = True,
) -> tuple[str, str]:
    """返回 (system_prompt, user_prompt)。"""
    system_prompt = _load_system_prompt()
    if include_few_shot:
        system_prompt = system_prompt + "\n\n## 喷涂典型示例 (Few-Shot)\n\n" + _load_few_shot()

    user_prompt_parts: list[str] = []
    user_prompt_parts.append("## 用户需求")
    user_prompt_parts.append(user_query.original)
    user_prompt_parts.append("")
    user_prompt_parts.append(f"## 识别的任务类别\n{user_query.category.value}")

    if context.text:
        user_prompt_parts.append("\n## 检索到的相关资料")
        user_prompt_parts.append(context.text)

    user_prompt_parts.append("\n## 你的任务")
    user_prompt_parts.append(
        "请生成完整 RAPID 模块代码。先用 ```rapid ... ``` 输出代码块，"
        "再用 2-3 句中文说明设计思路与关键参数。"
    )

    return system_prompt, "\n".join(user_prompt_parts)


def system_prompt() -> str:
    """对外暴露 system prompt（用于多轮对话）。"""
    return _load_system_prompt()


def few_shot_prompt() -> str:
    return _load_few_shot()
