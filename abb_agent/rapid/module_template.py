"""RAPID 模块模板生成器。

LLM 生成的代码经常缺少：
- MODULE/ENDMODULE 包裹
- 标准变量声明（tooldata、wobjdata、speeddata 等）
- 主入口过程 main()

本模块提供"骨架填充"能力：如果 LLM 输出缺失这些结构，自动补全。
所有函数都是纯函数（接受文本/数据，返回新文本），不修改输入。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

DEFAULT_TOOL_DATA = (
    "PERS tooldata tSprayGun := [TRUE, "
    "[[0,0,200],[1,0,0,0]], "  # TCP 平移 200mm（喷枪长度），姿态默认
    "[2.5,[0,0,80],[1,0,0,0],0,0,0]];"  # 质量 2.5kg
)
DEFAULT_WOBJ_DATA = (
    "PERS wobjdata wobjPart := [FALSE, TRUE, \"\", "
    "[[0,0,0],[1,0,0,0]], "
    "[[0,0,0],[1,0,0,0]]];"
)
DEFAULT_SPEED_PAINT = "CONST speeddata vPaint := [200, 500, 5000, 1000];"
DEFAULT_BRUSH_DATA = (
    "PERS num nFlowRate := 80;          ! 流量百分比 0-100\n"
    "    PERS num nFanWidth := 300;       ! 扇幅宽度 mm\n"
    "    PERS num nAtomPressure := 50;    ! 雾化压力 kPa"
)
DEFAULT_IO_SIGNALS = (
    "! 喷枪 IO 信号（需在 RobotStudio I/O 配置中映射）\n"
    "    ! VAR signaldo doSprayOn;\n"
    "    ! VAR signaldo doFanOn;\n"
    "    ! VAR signaldo doAtomOn;"
)


@dataclass(frozen=True)
class ModuleSkeleton:
    """RAPID 模块骨架配置。"""

    name: str = "MainModule"
    procedures: tuple[str, ...] = ()
    variables: tuple[str, ...] = ()
    routines: tuple[str, ...] = ()
    description: str = ""

    def render(self) -> str:
        """渲染为完整 .mod 字符串。"""
        header = f"MODULE {self.name}"
        if self.description:
            header += f"\n    ! {self.description}"

        var_section = "\n    ".join(self.variables) if self.variables else ""
        proc_section = "\n\n    ".join(self.procedures) if self.procedures else ""
        routines_section = "\n\n    ".join(self.routines) if self.routines else ""

        parts = [header]
        if var_section:
            parts.append("\n    " + var_section)
        if proc_section:
            parts.append("\n    " + proc_section)
        if routines_section:
            parts.append("\n    " + routines_section)
        parts.append("\nENDMODULE\n")
        return "\n".join(parts)


def _has_module_wrapper(code: str) -> bool:
    return bool(re.search(r"^\s*MODULE\b", code, re.MULTILINE))


def _has_main_proc(code: str) -> bool:
    return bool(re.search(r"\bPROC\s+main\s*\(", code, re.IGNORECASE))


def _extract_module_name(code: str) -> str | None:
    m = re.search(r"^\s*MODULE\s+([A-Za-z][A-Za-z0-9_]*)", code, re.MULTILINE)
    return m.group(1) if m else None


def wrap_in_module(
    code: str,
    *,
    module_name: str = "PaintProgram",
    description: str = "由 abb-agent 自动生成的喷涂程序",
    inject_defaults: bool = True,
) -> str:
    """若 LLM 输出缺少 MODULE，自动包裹。

    Args:
        code: 原始 LLM 输出
        module_name: 包裹模块名
        description: 模块顶部注释
        inject_defaults: 若主体没有声明 tool/wobj/speed，是否注入默认值
    """
    if _has_module_wrapper(code):
        return code

    has_tool = bool(re.search(r"\btooldata\b", code, re.IGNORECASE))
    has_wobj = bool(re.search(r"\bwobjdata\b", code, re.IGNORECASE))
    has_speed = bool(re.search(r"\bspeeddata\b", code, re.IGNORECASE))

    declarations: list[str] = []
    if inject_defaults:
        if not has_tool:
            declarations.append(DEFAULT_TOOL_DATA)
        if not has_wobj:
            declarations.append(DEFAULT_WOBJ_DATA)
        if not has_speed:
            declarations.append(DEFAULT_SPEED_PAINT)

    # 缩进 LLM 主体代码
    indented_body = "\n".join("    " + ln if ln else "" for ln in code.splitlines())

    decl_block = ("\n    " + "\n    ".join(declarations) + "\n") if declarations else ""
    return (
        f"MODULE {module_name}\n"
        f"    ! {description}\n"
        f"{decl_block}\n"
        f"{indented_body}\n"
        f"ENDMODULE\n"
    )


def ensure_main_proc(code: str, inner_calls: list[str] | None = None) -> str:
    """若没有 PROC main()，把所有未包裹在 PROC 内的指令收拢到 main 里。"""
    if _has_main_proc(code):
        return code
    if not inner_calls:
        return code

    main_proc = "PROC main()\n        " + "\n        ".join(inner_calls) + "\n    ENDPROC"
    # 插在 ENDMODULE 之前
    return re.sub(
        r"^\s*ENDMODULE",
        f"    {main_proc}\nENDMODULE",
        code,
        count=1,
        flags=re.MULTILINE,
    ) if _has_module_wrapper(code) else code + "\n" + main_proc + "\n"


def empty_painting_skeleton() -> ModuleSkeleton:
    """返回一个标准喷涂程序骨架。"""
    return ModuleSkeleton(
        name="PaintProgram",
        description="ABB 喷涂机器人 RAPID 程序模板",
        variables=(
            DEFAULT_TOOL_DATA,
            DEFAULT_WOBJ_DATA,
            DEFAULT_SPEED_PAINT,
            DEFAULT_BRUSH_DATA,
            DEFAULT_IO_SIGNALS,
        ),
        procedures=(
            "PROC main()\n"
            "        ! 主入口 - 调用具体喷涂路径\n"
            "        ConfL\\Off;\n"
            "        SingArea\\Wrist;\n"
            "        ! TODO: 调用扫描程序\n"
            "    ENDPROC",
        ),
    )
