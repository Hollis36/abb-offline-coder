"""评测脚手架的纯逻辑测试（不跑 LLM）。"""
from __future__ import annotations

from abb_agent.eval.harness import (
    EvalCase,
    load_cases,
    score_generation,
    summarize,
)
from abb_agent.rapid.validator import validate

# 一段合法的 IRC5P 代码（PaintL + brushdata + 真实 TCP）
_VALID_IRC5P = """MODULE P
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS brushdata bdMain := [80,300,50,50,50,0,FALSE,"bdMain",0];
    CONST robtarget pEnd := [[500,0,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    PROC main()
        PaintL pEnd, vPaint, bdMain, z10, tSprayGun\\WObj:=wobjPart;
    ENDPROC
ENDMODULE"""

# 缺 ENDMODULE → 校验不过
_INVALID = "MODULE P\n    PROC main()\n        PaintL pEnd, vPaint, bdMain, z10, t;\n    ENDPROC"


def _case(**kw) -> EvalCase:
    base = {"id": "t", "query": "q", "controller": "IRC5P"}
    base.update(kw)
    return EvalCase(**base)


def test_load_cases_nonempty_and_well_formed() -> None:
    cases = load_cases()
    assert len(cases) >= 4
    ids = {c.id for c in cases}
    assert "irc5p_zigzag" in ids and "irc5_zigzag" in ids
    for c in cases:
        assert c.query and c.controller in ("IRC5", "IRC5P")


def test_score_passes_for_good_generation() -> None:
    case = _case(
        must_include=("PaintL", "brushdata"),
        must_not_include=("SetDO doSprayOn",),
        expect_category="zigzag_scan",
    )
    report = validate(_VALID_IRC5P, controller="IRC5P", strict_tcp=True)
    score = score_generation(case, _VALID_IRC5P, report, category="zigzag_scan")
    assert score.valid and score.includes_ok and score.excludes_ok and score.category_ok
    assert score.passed


def test_score_flags_missing_instruction() -> None:
    case = _case(must_include=("PaintC",))  # 代码里没有 PaintC
    report = validate(_VALID_IRC5P, controller="IRC5P")
    score = score_generation(case, _VALID_IRC5P, report)
    assert not score.includes_ok
    assert "PaintC" in score.missing
    assert not score.passed


def test_score_flags_leaked_token() -> None:
    code = _VALID_IRC5P + "\n        SetDO doSprayOn, 1;"
    case = _case(must_not_include=("SetDO doSprayOn",))
    report = validate(code, controller="IRC5P")
    score = score_generation(case, code, report)
    assert not score.excludes_ok
    assert "SetDO doSprayOn" in score.leaked
    assert not score.passed


def test_score_flags_invalid_code() -> None:
    case = _case()
    report = validate(_INVALID, controller="IRC5P")
    score = score_generation(case, _INVALID, report)
    assert not score.valid
    assert not score.passed


def test_score_category_mismatch() -> None:
    case = _case(expect_category="arc_scan")
    report = validate(_VALID_IRC5P, controller="IRC5P")
    score = score_generation(case, _VALID_IRC5P, report, category="zigzag_scan")
    assert not score.category_ok
    assert not score.passed


def test_summarize_counts() -> None:
    case_ok = _case(must_include=("PaintL",))
    case_bad = _case(must_include=("PaintC",))
    rep = validate(_VALID_IRC5P, controller="IRC5P")
    s_ok = score_generation(case_ok, _VALID_IRC5P, rep)
    s_bad = score_generation(case_bad, _VALID_IRC5P, rep)
    summary = summarize([s_ok, s_bad])
    assert summary.total == 2
    assert summary.passed == 1
    assert summary.valid == 2
    assert summary.pass_rate == 0.5
