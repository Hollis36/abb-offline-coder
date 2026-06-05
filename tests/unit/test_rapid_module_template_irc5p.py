"""IRC5P 模式下 module_template 注入行为。"""
from __future__ import annotations

from abb_agent.rapid.module_template import empty_painting_skeleton, wrap_in_module


def test_wrap_in_module_irc5p_injects_brushdata() -> None:
    code = "PROC main()\n    PaintL p1, vPaint, bdMain, z10, tSprayGun;\nENDPROC"
    wrapped = wrap_in_module(code, controller="IRC5P", brush_mode="brushdata_arg")
    assert "PERS brushdata bdMain" in wrapped, wrapped


def test_wrap_in_module_irc5p_omits_num_brush_block() -> None:
    code = "PROC main()\n    PaintL p1, vPaint, bdMain, z10, tSprayGun;\nENDPROC"
    wrapped = wrap_in_module(code, controller="IRC5P")
    # 不应再用 num 占位
    assert "PERS num nFlowRate" not in wrapped


def test_wrap_in_module_irc5_default_unchanged() -> None:
    """不显式指定 controller 时保持原有行为（不注入 brushdata 块）。"""
    code = "PROC main()\n    MoveL p1, v100, fine, tool0;\nENDPROC"
    wrapped = wrap_in_module(code)
    assert "PERS brushdata" not in wrapped


def test_wrap_in_module_irc5p_skips_existing_brushdata() -> None:
    """已有 brushdata 声明的代码不重复注入。"""
    code = (
        "PERS brushdata bdCustom := [70,250,40,30,30,0,FALSE,\"bdCustom\",0];\n"
        "PROC main()\n"
        "    PaintL p1, vPaint, bdCustom, z10, tSprayGun;\n"
        "ENDPROC"
    )
    wrapped = wrap_in_module(code, controller="IRC5P")
    assert wrapped.count("PERS brushdata") == 1


def test_wrap_in_module_irc5p_still_injects_tooldata() -> None:
    """IRC5P 模式下其它默认变量声明仍然注入。"""
    code = "PROC main()\n    PaintL p1, vPaint, bdMain, z10, tSprayGun;\nENDPROC"
    wrapped = wrap_in_module(code, controller="IRC5P")
    assert "PERS tooldata tSprayGun" in wrapped
    assert "PERS wobjdata wobjPart" in wrapped


def test_empty_painting_skeleton_irc5p_includes_brushdata() -> None:
    """brushdata_arg 写法下空骨架应包含 brushdata 声明。"""
    skel = empty_painting_skeleton(controller="IRC5P", brush_mode="brushdata_arg")
    rendered = skel.render()
    assert "PERS brushdata" in rendered


def test_wrap_in_module_irc5p_setbrush_default_no_brushdata() -> None:
    """默认 setbrush：不注入 brushdata（刷子由 SetBrush 选择）。"""
    code = "PROC main()\n    SetBrush 1;\n    PaintL p1, v600, z10, tSprayGun;\nENDPROC"
    wrapped = wrap_in_module(code, controller="IRC5P")
    assert "PERS brushdata" not in wrapped
    assert "PERS tooldata tSprayGun" in wrapped  # 其它默认声明仍注入


def test_empty_painting_skeleton_irc5p_setbrush_default_mentions_setbrush() -> None:
    skel = empty_painting_skeleton(controller="IRC5P")  # 默认 setbrush
    rendered = skel.render()
    assert "PERS brushdata" not in rendered
    assert "SetBrush" in rendered


def test_empty_painting_skeleton_irc5_default_unchanged() -> None:
    skel = empty_painting_skeleton()
    rendered = skel.render()
    assert "PERS brushdata" not in rendered
    assert "PERS num nFlowRate" in rendered  # 老行为
