"""保证 few-shot 黄金样例始终通过 validate()，且按控制器正确隔离。

few-shot 示例是小模型生成质量的直接锚点 —— 它们必须本身合法，
否则等于在教模型写错代码。这里把每个 ```rapid 代码块抽出来跑校验器。
"""
from __future__ import annotations

import re

import pytest

from abb_agent.config import get_config
from abb_agent.llm.prompts.templates import (
    build_full_prompt,
    clear_prompt_cache,
    few_shot_prompt,
)
from abb_agent.rag.context_builder import ContextBuilder
from abb_agent.rag.query_rewriter import rewrite
from abb_agent.rapid.validator import validate

_RAPID_BLOCK_RE = re.compile(r"```rapid\s*\n(.*?)```", re.DOTALL)
_PAINTL_INSTR_RE = re.compile(r"\bPaintL\b")  # 不匹配模块名 PaintLine


def _blocks(text: str) -> list[str]:
    return [b.strip() for b in _RAPID_BLOCK_RE.findall(text)]


@pytest.fixture(autouse=True)
def _fresh_cache() -> None:
    clear_prompt_cache()


def test_irc5_examples_are_valid() -> None:
    wl = get_config().rapid.io_whitelist
    blocks = _blocks(few_shot_prompt("IRC5"))
    assert len(blocks) >= 6
    for i, code in enumerate(blocks, 1):
        report = validate(code, controller="IRC5", io_whitelist=wl)
        assert report.is_valid, f"IRC5 few-shot block {i} invalid:\n{report.format_summary()}"


def test_irc5p_examples_are_valid_under_strict_settings() -> None:
    """IRC5P 样例要在 agent 实际使用的最严设置下通过（strict_tcp=True）。"""
    wl = get_config().rapid.io_whitelist
    blocks = _blocks(few_shot_prompt("IRC5P"))
    assert len(blocks) >= 4
    for i, code in enumerate(blocks, 1):
        report = validate(code, controller="IRC5P", io_whitelist=wl, strict_tcp=True)
        assert report.is_valid, f"IRC5P few-shot block {i} invalid:\n{report.format_summary()}"


def test_irc5p_examples_use_paint_instructions() -> None:
    text = few_shot_prompt("IRC5P")
    assert _PAINTL_INSTR_RE.search(text), "IRC5P few-shot 应包含 PaintL 指令"
    assert "PaintC" in text, "IRC5P few-shot 应包含 PaintC 示例"
    assert "SetBrush" in text, "IRC5P few-shot 应使用 SetBrush 选刷子"
    # 不能用 SetDO 切换喷涂主信号
    assert "SetDO doSprayOn" not in text, "IRC5P few-shot 不应用 SetDO doSprayOn 凑喷涂"


def test_irc5_examples_have_no_paint_instructions() -> None:
    text = few_shot_prompt("IRC5")
    assert not _PAINTL_INSTR_RE.search(text), "IRC5 few-shot 不应出现 PaintL 指令（PaintLine 模块名除外）"
    assert "SetDO doSprayOn" in text, "IRC5 few-shot 应使用 SetDO doSprayOn"


def test_build_full_prompt_selects_few_shot_by_controller() -> None:
    rw = rewrite("在平板上 Z 字喷涂")
    ctx = ContextBuilder().build([])
    mark = "## 喷涂典型示例 (Few-Shot)"

    sys_irc5, _ = build_full_prompt(rw, ctx, controller="IRC5")
    sys_irc5p, _ = build_full_prompt(rw, ctx, controller="IRC5P")

    fs_irc5 = sys_irc5.split(mark, 1)[1]
    fs_irc5p = sys_irc5p.split(mark, 1)[1]

    assert _PAINTL_INSTR_RE.search(fs_irc5p) and "brushdata" in fs_irc5p
    assert not _PAINTL_INSTR_RE.search(fs_irc5)
    assert "SetDO doSprayOn" in fs_irc5 and "SetDO doSprayOn" not in fs_irc5p


def test_no_few_shot_when_disabled() -> None:
    rw = rewrite("在平板上 Z 字喷涂")
    ctx = ContextBuilder().build([])
    sys_p, _ = build_full_prompt(rw, ctx, controller="IRC5P", include_few_shot=False)
    assert "## 喷涂典型示例 (Few-Shot)" not in sys_p
