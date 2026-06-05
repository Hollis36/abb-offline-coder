"""IRC5P 专项 RAPID 校验规则。

新增三类问题码：
  - PNT001: PaintL/PaintC 缺少 brushdata 形参
  - TCP001: tooldata TCP 仍为默认占位值（必须现场标定）
  - IO001 : 引用的 IO 信号不在 EIO.cfg 白名单中
"""
from __future__ import annotations

from abb_agent.rapid.validator import Severity, validate


# ---------------- PNT001: PaintL 必须带 brushdata ----------------

def test_paintl_with_brushdata_passes() -> None:
    code = """MODULE M
    PERS brushdata bdMain := [80,300,50,50,50,0,FALSE,"bdMain",0];
    PROC main()
        PaintL p1, vPaint, bdMain, z10, tSprayGun\\WObj:=wobjPart;
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P")
    assert not any(i.code == "PNT001" for i in report.errors), report.format_summary()


def test_paintl_missing_brushdata_triggers_pnt001() -> None:
    # 5 个参数但其中没有 brushdata 标识
    code = """MODULE M
    PROC main()
        PaintL p1, vPaint, z10, tSprayGun\\WObj:=wobjPart;
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P", brush_mode="brushdata_arg")
    assert any(i.code == "PNT001" and i.severity == Severity.ERROR for i in report.issues), \
        report.format_summary()


def test_paintc_missing_brushdata_triggers_pnt001() -> None:
    code = """MODULE M
    PROC main()
        PaintC pMid, pEnd, vPaint, z10, tSprayGun\\WObj:=wobjPart;
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P", brush_mode="brushdata_arg")
    assert any(i.code == "PNT001" for i in report.errors), report.format_summary()


def test_paintl_not_checked_under_irc5_mode() -> None:
    """IRC5 模式下不应触发 PNT001（哪怕代码里写了 PaintL 也只是字符串）。"""
    code = """MODULE M
    PROC main()
        PaintL p1, vPaint, z10, tSprayGun\\WObj:=wobjPart;
    ENDPROC
ENDMODULE
"""
    report = validate(code)  # 默认 IRC5
    assert not any(i.code == "PNT001" for i in report.issues)


# ---------------- TCP001: tooldata 默认值告警 ----------------

def test_default_tcp_triggers_tcp001() -> None:
    """tooldata 中 TCP 偏移 [0,0,200] 是默认占位值，现场必须重新标定。"""
    code = """MODULE M
    PERS tooldata tSprayGun := [TRUE,[[0,0,200],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PROC main()
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P", strict_tcp=True)
    assert any(i.code == "TCP001" for i in report.issues), report.format_summary()


def test_custom_tcp_no_warning() -> None:
    """非默认 TCP 不告警。"""
    code = """MODULE M
    PERS tooldata tSprayGun := [TRUE,[[12.5,3.4,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PROC main()
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P", strict_tcp=True)
    assert not any(i.code == "TCP001" for i in report.issues)


def test_default_tcp_silent_when_strict_off() -> None:
    """strict_tcp 关闭时不告警（开发期默认）。"""
    code = """MODULE M
    PERS tooldata tSprayGun := [TRUE,[[0,0,200],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PROC main()
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P")
    assert not any(i.code == "TCP001" for i in report.issues)


# ---------------- IO001: IO 信号白名单 ----------------

def test_io_signal_in_whitelist_passes() -> None:
    code = """MODULE M
    PROC main()
        SetDO doSprayOn, 1;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn", "doFanOn"))
    assert not any(i.code == "IO001" for i in report.issues)


def test_io_signal_not_in_whitelist_triggers_io001() -> None:
    code = """MODULE M
    PROC main()
        SetDO doUnknown, 1;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn",))
    assert any(i.code == "IO001" and i.severity == Severity.ERROR for i in report.issues), \
        report.format_summary()


def test_io_whitelist_none_skips_check() -> None:
    """白名单未提供时不做检查（兼容老调用）。"""
    code = """MODULE M
    PROC main()
        SetDO doAnything, 1;
    ENDPROC
ENDMODULE
"""
    report = validate(code)
    assert not any(i.code == "IO001" for i in report.issues)


def test_pulsedo_also_checked() -> None:
    code = """MODULE M
    PROC main()
        PulseDO doMystery;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn",))
    assert any(i.code == "IO001" for i in report.issues)


def test_waitdi_also_checked() -> None:
    code = """MODULE M
    PROC main()
        WaitDI diMystery, 1;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("diBrushOK",))
    assert any(i.code == "IO001" for i in report.issues)


# -------- IO001 现场命名 / 开关参数 / 大小写（IO 校验加强） --------

def test_pulsedo_switch_form_signal_checked() -> None:
    """PulseDO\\PLength:=3,sig 这种带开关的写法，信号名仍要被提取并校验。"""
    code = """MODULE M
    PROC main()
        PulseDO\\PLength:=3,B_dopaintfinish;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn",))
    assert any(i.code == "IO001" and "B_dopaintfinish" in i.message for i in report.issues), \
        report.format_summary()


def test_pulsedo_switch_form_signal_in_whitelist_ok() -> None:
    code = """MODULE M
    PROC main()
        PulseDO\\PLength:=3,B_dopaintfinish;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("B_dopaintfinish",))
    assert not any(i.code == "IO001" for i in report.issues), report.format_summary()


def test_setdo_field_named_signal_checked_regardless_of_prefix() -> None:
    """现场非 do/di 前缀的信号名（如 Hand_A_StartSpray）在 SetDO 里也要校验。"""
    code = """MODULE M
    PROC main()
        SetDO Hand_A_StartSpray, 1;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn",))
    assert any(i.code == "IO001" and "Hand_A_StartSpray" in i.message for i in report.issues), \
        report.format_summary()


def test_setdo_sdelay_switch_signal_extracted() -> None:
    """SetDO\\SDelay:=t, sig, val —— 应跳过开关取到真正的信号名。"""
    code = """MODULE M
    PROC main()
        SetDO\\SDelay:=0.5, doSprayOn, 1;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn",))
    assert not any(i.code == "IO001" for i in report.issues), report.format_summary()


def test_reset_non_io_identifier_not_flagged() -> None:
    """Reset 多义：非 IO 形态的标识符（如 stopwatch1）不应误报 IO001。"""
    code = """MODULE M
    PROC main()
        Reset stopwatch1;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn",))
    assert not any(i.code == "IO001" for i in report.issues), report.format_summary()


def test_reset_do_prefixed_unknown_flagged() -> None:
    code = """MODULE M
    PROC main()
        Reset doSprayOff;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn",))
    assert any(i.code == "IO001" for i in report.issues), report.format_summary()


def test_io_whitelist_match_case_insensitive() -> None:
    """RAPID 标识符大小写不敏感，白名单匹配亦然。"""
    code = """MODULE M
    PROC main()
        SetDO DOSPRAYON, 1;
    ENDPROC
ENDMODULE
"""
    report = validate(code, io_whitelist=("doSprayOn",))
    assert not any(i.code == "IO001" for i in report.issues), report.format_summary()


def test_io_signal_prefixes_configurable_for_reset() -> None:
    """配置自定义前缀后，Reset 也能识别现场命名的 IO（如 a_clamp）。"""
    code = """MODULE M
    PROC main()
        Reset A_clamp;
    ENDPROC
ENDMODULE
"""
    # 默认前缀不含 a_ → 视为非 IO，跳过
    assert not any(
        i.code == "IO001"
        for i in validate(code, io_whitelist=("doSprayOn",)).issues
    )
    # 配置 a_ 前缀后 → 识别为 IO，且不在白名单 → 报错
    report = validate(
        code, io_whitelist=("doSprayOn",), io_signal_prefixes=("do", "di", "a_")
    )
    assert any(i.code == "IO001" for i in report.issues), report.format_summary()


# ---------------- 集成场景：完整 IRC5P 程序 ----------------

def test_complete_irc5p_program_valid() -> None:
    code = """MODULE PaintLine
    PERS tooldata tSprayGun := [TRUE,[[15.2,0.3,287.5],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[100,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    PERS brushdata bdMain := [80,300,50,50,50,0,FALSE,"bdMain",0];
    CONST speeddata vPaint := [200,500,5000,1000];
    CONST robtarget P1 := [[500,0,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget P2 := [[700,0,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    PROC main()
        ConfL\\Off;
        SingArea\\Wrist;
        MoveL P1, v500, fine, tSprayGun\\WObj:=wobjPart;
        PaintL P2, vPaint, bdMain, z10, tSprayGun\\WObj:=wobjPart;
    ENDPROC
ENDMODULE
"""
    report = validate(
        code,
        controller="IRC5P",
        io_whitelist=("doSprayOn", "doFanOn"),
        strict_tcp=True,
        brush_mode="brushdata_arg",
    )
    assert report.is_valid, report.format_summary()


# ---------------- setbrush 写法（默认）：PaintL 4 参数 + SetBrush ----------------

def test_setbrush_4arg_paintl_valid_by_default() -> None:
    """默认 setbrush 模式下，4 参数 PaintL（无 brushdata）合法。"""
    code = """MODULE M
    PROC main()
        SetBrush 1;
        PaintL p1, v600, z10, tSprayGun\\WObj:=wobjPart;
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P")  # 默认 setbrush
    assert not any(i.code == "PNT001" for i in report.issues), report.format_summary()


def test_setbrush_5arg_paintc_valid_by_default() -> None:
    code = """MODULE M
    PROC main()
        SetBrush 1;
        PaintC pMid, pEnd, v600, z10, tSprayGun\\WObj:=wobjPart;
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P")
    assert not any(i.code == "PNT001" for i in report.issues), report.format_summary()


def test_setbrush_paintl_too_few_args_still_flagged() -> None:
    """即便 setbrush 模式，PaintL 少于 4 个参数仍属畸形。"""
    code = """MODULE M
    PROC main()
        PaintL p1, v600, z10;
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P")
    assert any(i.code == "PNT001" for i in report.errors), report.format_summary()


def test_real_m3_setbrush_program_validates() -> None:
    """真实产线 IPS Paint 程序（SetBrush + 4 参数 PaintL）应通过默认校验。"""
    code = """MODULE M3
    LOCAL CONST robtarget p10:=[[967.17,-1332.68,1108.14],[0.025,-0.727,-0.686,0.003],[0,-1,1,-1],[9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];
    LOCAL CONST robtarget p20:=[[-894.93,-1354.32,1093.02],[0.025,-0.727,-0.686,0.003],[-1,-1,0,-1],[9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]];

    PROC mainM3()
        AccSet 50,80;
        ClkReset Runclock;
        ClkStart Runclock;
        WaitUntil Hand_A_StartSpray=1 OR A_StartSpray=1;
        MoveAbsJ jHomePos\\NoEOffs,v600,z50,tool0;
        PaintL p10,v600,fine,tUserTool0;
        SetBrush 2;
        PaintL p20,v600,z30,tUserTool0;
        SetBrush 1;
        MoveAbsJ jHomePos\\NoEOffs,v600,z50,tool0;
        PulseDO\\PLength:=3,B_dopaintfinish;
        ClkStop Runclock;
        Runtime:=ClkRead(Runclock);
        TPWrite "Runtime="\\Num:=Runtime;
    ENDPROC
ENDMODULE
"""
    report = validate(code, controller="IRC5P", strict_tcp=True)  # 默认 setbrush
    assert report.is_valid, report.format_summary()
