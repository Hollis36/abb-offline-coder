"""离线生成质量评测脚手架。

把"few-shot 改没改善生成"变成可复现的数字:对一组用例跑生成,
再用项目自带的 validate() + 关键指令检查打分。

不依赖 LLM 的纯打分逻辑放这里(可单测);真正跑生成在 scripts/eval.py。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources

from abb_agent.config import ControllerKind
from abb_agent.rapid.validator import ValidationReport


@dataclass(frozen=True)
class EvalCase:
    """一个评测用例:需求 + 期望特征。"""

    id: str
    query: str
    controller: ControllerKind = "IRC5"
    must_include: tuple[str, ...] = ()
    must_not_include: tuple[str, ...] = ()
    expect_category: str | None = None


@dataclass(frozen=True)
class CaseScore:
    """一个用例的打分结果。"""

    case_id: str
    valid: bool
    includes_ok: bool
    excludes_ok: bool
    category_ok: bool
    missing: tuple[str, ...] = ()
    leaked: tuple[str, ...] = ()
    duration_ms: int = 0
    model: str = ""

    @property
    def passed(self) -> bool:
        return self.valid and self.includes_ok and self.excludes_ok and self.category_ok


def load_cases() -> list[EvalCase]:
    """从打包的 cases.json 读取评测用例。"""
    raw = resources.files("abb_agent.eval").joinpath("cases.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    return [
        EvalCase(
            id=c["id"],
            query=c["query"],
            controller=c.get("controller", "IRC5"),
            must_include=tuple(c.get("must_include", ())),
            must_not_include=tuple(c.get("must_not_include", ())),
            expect_category=c.get("expect_category"),
        )
        for c in data
    ]


def score_generation(
    case: EvalCase,
    code: str,
    report: ValidationReport,
    *,
    category: str | None = None,
    duration_ms: int = 0,
    model: str = "",
) -> CaseScore:
    """对一次生成结果打分。纯函数,不碰 LLM/网络。"""
    missing = tuple(s for s in case.must_include if s not in code)
    leaked = tuple(s for s in case.must_not_include if s in code)
    category_ok = case.expect_category is None or category == case.expect_category
    return CaseScore(
        case_id=case.id,
        valid=report.is_valid,
        includes_ok=not missing,
        excludes_ok=not leaked,
        category_ok=category_ok,
        missing=missing,
        leaked=leaked,
        duration_ms=duration_ms,
        model=model,
    )


@dataclass(frozen=True)
class EvalSummary:
    total: int
    passed: int
    valid: int

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    @property
    def valid_rate(self) -> float:
        return self.valid / self.total if self.total else 0.0


def summarize(scores: list[CaseScore]) -> EvalSummary:
    return EvalSummary(
        total=len(scores),
        passed=sum(1 for s in scores if s.passed),
        valid=sum(1 for s in scores if s.valid),
    )
