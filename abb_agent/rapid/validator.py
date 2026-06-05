"""RAPID 轻量语法校验。

我们不做完整 RAPID parser（成本太高）。
只做 ABB RAPID 最常见的 8 类错误的正则校验：
  1. MODULE / ENDMODULE 配对
  2. PROC / ENDPROC 配对
  3. IF / ENDIF, WHILE / ENDWHILE, FOR / ENDFOR 配对
  4. 关键字大小写规范（RAPID 是大小写敏感的）
  5. 行末分号（语句必须以 ; 结尾，少数指令例外）
  6. 注释格式（! ... 或 % ... %）
  7. 字符串引号配对
  8. 数据类型常量出现位置（VAR/PERS/CONST 必须在 PROC 外或顶部）

外加 IRC5P 专项检查（当 controller="IRC5P" 时启用）：
  - PNT001: PaintL/PaintC 缺少 brushdata 形参
  - TCP001: tooldata 仍为默认占位 TCP（strict_tcp=True 时启用）
  - IO001 : 引用了不在 EIO.cfg 白名单中的 IO 信号

返回 ValidationReport，由调用方决定如何处理（修复 / 警告 / 拒绝）。
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

ControllerKind = Literal["IRC5", "IRC5P"]
# IRC5P 喷涂工艺写法，详见 config.BrushMode。
BrushMode = Literal["setbrush", "brushdata_arg"]


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationIssue:
    line: int
    severity: Severity
    code: str
    message: str

    def format(self) -> str:
        return f"[{self.severity.value.upper()}][{self.code}] L{self.line}: {self.message}"


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == Severity.WARNING)

    def format_summary(self) -> str:
        if not self.issues:
            return "✓ RAPID 语法校验通过"
        lines = [i.format() for i in self.issues]
        n_err = len(self.errors)
        n_warn = len(self.warnings)
        lines.append(f"-- 共 {n_err} 错误, {n_warn} 警告")
        return "\n".join(lines)


# 这些关键字必须大写
RAPID_KEYWORDS = frozenset(
    [
        "MODULE", "ENDMODULE", "PROC", "ENDPROC", "FUNC", "ENDFUNC", "TRAP", "ENDTRAP",
        "RECORD", "ENDRECORD", "IF", "THEN", "ELSE", "ELSEIF", "ENDIF",
        "FOR", "FROM", "TO", "STEP", "DO", "ENDFOR", "WHILE", "ENDWHILE",
        "TEST", "CASE", "DEFAULT", "ENDTEST", "RETURN", "GOTO", "RAISE",
        "VAR", "PERS", "CONST", "LOCAL", "TASK", "GLOBAL",
        "MoveJ", "MoveL", "MoveC", "MoveAbsJ", "MoveLDO", "MoveJDO", "MoveCDO",
        "MoveLSync", "MoveJSync", "MoveCSync",
        "PaintL", "PaintC", "SetBrush",
        "TriggL", "TriggC", "TriggJ", "TriggIO", "TriggData", "TriggEquip",
        "SetDO", "Reset", "SetAO", "WaitDI", "WaitDO", "WaitUntil", "PulseDO",
        "WaitTime", "Stop", "EXIT",
        "AccSet", "VelSet", "ConfL", "ConfJ", "SingArea",
        "TPWrite", "ClkReset", "ClkStart", "ClkStop", "ClkRead",
    ]
)

# 喷涂 helpers 当前注入的默认 TCP（[0,0,200]），现场必须重新标定。
# 兼容 [0,0,200] / [0.0, 0, 200.0] / 任意空格/小数 0.x 形式。
DEFAULT_TCP_PATTERN = re.compile(
    r"\[\s*0(?:\.0+)?\s*,\s*0(?:\.0+)?\s*,\s*200(?:\.0+)?\s*\]",
    re.IGNORECASE,
)

# 只有这些前缀的标识符才算 IO 信号；其它（如 clock 变量）一律忽略。
IO_SIGNAL_PREFIXES = ("do", "di", "ao", "ai", "go", "gi")


# 块结构配对表：开始关键字 -> 结束关键字（按顺序匹配嵌套）
BLOCK_PAIRS = {
    "MODULE": "ENDMODULE",
    "PROC": "ENDPROC",
    "FUNC": "ENDFUNC",
    "TRAP": "ENDTRAP",
    "RECORD": "ENDRECORD",
    "IF": "ENDIF",
    "FOR": "ENDFOR",
    "WHILE": "ENDWHILE",
    "TEST": "ENDTEST",
}
OPEN_KEYWORDS = frozenset(BLOCK_PAIRS.keys())
CLOSE_KEYWORDS = frozenset(BLOCK_PAIRS.values())

# 不需要 ; 结尾的关键字行
NO_SEMICOLON_LINES = frozenset(
    list(BLOCK_PAIRS.keys()) + list(BLOCK_PAIRS.values()) +
    ["THEN", "ELSE", "ELSEIF", "DO", "CASE", "DEFAULT", "TASK", "GLOBAL", "LOCAL"]
)


_LINE_COMMENT_RE = re.compile(r"!.*$")
_KEYWORD_TOKEN_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\b")


def _strip_comments(line: str) -> str:
    """去掉 ! 之后的行注释。RAPID 不支持块注释 % ... %（很少用，本期不处理）。"""
    return _LINE_COMMENT_RE.sub("", line).rstrip()


def _is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("!")


def _check_blocks(lines: list[str]) -> list[ValidationIssue]:
    """检查块结构配对，使用栈式匹配。"""
    stack: list[tuple[str, int]] = []
    issues: list[ValidationIssue] = []

    for ln_idx, raw in enumerate(lines, start=1):
        line = _strip_comments(raw).strip()
        if not line:
            continue

        first_word_match = re.match(r"^([A-Z]+)\b", line)
        if not first_word_match:
            continue
        word = first_word_match.group(1)

        if word in OPEN_KEYWORDS:
            stack.append((word, ln_idx))
        elif word in CLOSE_KEYWORDS:
            expected_open = next(
                (op for op, cl in BLOCK_PAIRS.items() if cl == word), None
            )
            if not stack:
                issues.append(
                    ValidationIssue(
                        ln_idx, Severity.ERROR, "BLK001",
                        f"出现 {word} 但没有对应的 {expected_open}",
                    )
                )
            else:
                top_word, top_ln = stack[-1]
                if BLOCK_PAIRS.get(top_word) != word:
                    issues.append(
                        ValidationIssue(
                            ln_idx, Severity.ERROR, "BLK002",
                            f"块不匹配：L{top_ln} 是 {top_word}，但在此处遇到 {word}",
                        )
                    )
                else:
                    stack.pop()

    for top_word, top_ln in stack:
        issues.append(
            ValidationIssue(
                top_ln, Severity.ERROR, "BLK003",
                f"未闭合的 {top_word}，应有对应的 {BLOCK_PAIRS[top_word]}",
            )
        )
    return issues


def _check_keyword_case(lines: list[str]) -> list[ValidationIssue]:
    """检查关键字大小写。常见错误：modul/Movel 等。"""
    issues: list[ValidationIssue] = []
    case_map = {kw.lower(): kw for kw in RAPID_KEYWORDS}

    for ln_idx, raw in enumerate(lines, start=1):
        line = _strip_comments(raw)
        if not line.strip():
            continue
        for token in _KEYWORD_TOKEN_RE.findall(line):
            lower = token.lower()
            if lower in case_map and token != case_map[lower]:
                issues.append(
                    ValidationIssue(
                        ln_idx, Severity.WARNING, "CASE001",
                        f"关键字 '{token}' 大小写应为 '{case_map[lower]}'",
                    )
                )
    return issues


def _check_semicolons(lines: list[str]) -> list[ValidationIssue]:
    """检查行末分号。"""
    issues: list[ValidationIssue] = []
    for ln_idx, raw in enumerate(lines, start=1):
        line = _strip_comments(raw).strip()
        if _is_blank_or_comment(raw) or not line:
            continue

        first_word_match = re.match(r"^([A-Za-z][A-Za-z0-9_]*)\b", line)
        first_word = first_word_match.group(1) if first_word_match else ""

        if first_word in NO_SEMICOLON_LINES:
            continue
        if line.startswith("!") or line.startswith("%"):
            continue
        if line.endswith(";") or line.endswith("{") or line.endswith(","):
            continue
        if re.search(r"\b(THEN|DO)\s*$", line):
            continue

        issues.append(
            ValidationIssue(
                ln_idx, Severity.WARNING, "SEM001",
                f"该行可能缺少结尾分号: '{line[:50]}'",
            )
        )
    return issues


def _check_quotes(lines: list[str]) -> list[ValidationIssue]:
    """检查字符串引号是否配对。"""
    issues: list[ValidationIssue] = []
    for ln_idx, raw in enumerate(lines, start=1):
        line = _strip_comments(raw)
        if line.count('"') % 2 != 0:
            issues.append(
                ValidationIssue(
                    ln_idx, Severity.ERROR, "STR001",
                    "字符串引号不配对",
                )
            )
    return issues


def _check_module_declaration(lines: list[str]) -> list[ValidationIssue]:
    """必须有 MODULE 声明。"""
    issues: list[ValidationIssue] = []
    has_module = any(re.match(r"^\s*MODULE\b", line) for line in lines)
    if not has_module:
        issues.append(
            ValidationIssue(
                1, Severity.ERROR, "MOD001",
                "代码缺少 MODULE 声明",
            )
        )
    return issues


def _split_args(arg_str: str) -> list[str]:
    """按顶层逗号切分参数串。忽略 [] () 内的逗号。"""
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in arg_str:
        if ch in "[(":
            depth += 1
            buf.append(ch)
        elif ch in "])":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


# 在一行任意位置查找 PaintL/PaintC 调用，捕获到下一个分号为止的参数串。
# 这样 `IF cond THEN PaintL ...;` 这种内联格式也能被检出（M1）。
_PAINT_CALL_RE = re.compile(r"\b(PaintL|PaintC)\s+([^;]+);")
_BRUSHDATA_DECL_RE = re.compile(r"\bbrushdata\s+([A-Za-z_][A-Za-z0-9_]*)")
_TOOLDATA_DECL_RE = re.compile(
    r"\btooldata\s+([A-Za-z_][A-Za-z0-9_]*)\s*:=\s*(.+?);", re.DOTALL
)
# 行首匹配 IO 指令名；group(2) 为其后全部内容，交给 _extract_io_signal 解析。
_IO_INSTR_RE = re.compile(
    r"^\s*(SetDO|SetAO|WaitDI|WaitDO|PulseDO|Reset)\b(.*)$", re.IGNORECASE
)
# 开关参数：\High、\PLength:=3、\SDelay:=0.5 等（含其后可选逗号）。
_IO_SWITCH_RE = re.compile(r"^\s*\\[A-Za-z][A-Za-z0-9_]*(?:\s*:=\s*[^,;\s\\]+)?\s*,?")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Reset 之外的 IO 指令，操作数必为 IO 信号 → 恒做白名单校验（不受前缀启发式限制）。
_UNAMBIGUOUS_IO_INSTR = frozenset(["setdo", "setao", "waitdi", "waitdo", "pulsedo"])


def _check_paint_brushdata(
    lines: list[str], brush_mode: BrushMode = "setbrush"
) -> list[ValidationIssue]:
    """IRC5P PaintL/PaintC 参数校验，按 brush_mode 切换两种工艺写法。

    setbrush（默认，现场常见 IPS/RobotWare Paint 写法）：
      PaintL: target, speed, zone, tool [\\WObj:=wobj]        → 至少 4 个位置参数
      PaintC: pMid, pEnd, speed, zone, tool [\\WObj:=wobj]    → 至少 5 个
      刷子由独立的 SetBrush n 指令选择，PaintL/PaintC 不带 brushdata。

    brushdata_arg（旧变体，brushdata 作位置参数）：
      PaintL: target, speed, brushdata, zone, tool           → 至少 5 个
      PaintC: pMid, pEnd, speed, brushdata, zone, tool       → 至少 6 个
      若声明过 brushdata，调用中应引用其中一个名字。
    """
    code = "\n".join(lines)
    declared_brushes = set(_BRUSHDATA_DECL_RE.findall(code))

    if brush_mode == "brushdata_arg":
        paintl_min, paintc_min = 5, 6
        short_hint = "很可能缺少 brushdata 形参"
    else:
        paintl_min, paintc_min = 4, 5
        short_hint = "至少需要 目标, 速度, 转弯区, 工具"

    issues: list[ValidationIssue] = []
    for ln_idx, raw in enumerate(lines, start=1):
        line = _strip_comments(raw)
        # 同一行可能有多个 PaintL/PaintC（IF...THEN PaintL ...; PaintL ...; ENDIF）
        for m in _PAINT_CALL_RE.finditer(line):
            instr = m.group(1)
            # 把 \WObj:=xxx 这种 switch 参数剥离（值可以是标识符/数字/路径）
            body = re.sub(r"\\[A-Za-z]+\s*:=\s*[^,;\s\\]+", "", m.group(2))
            args = _split_args(body)

            min_args = paintl_min if instr == "PaintL" else paintc_min
            if len(args) < min_args:
                issues.append(
                    ValidationIssue(
                        ln_idx, Severity.ERROR, "PNT001",
                        f"{instr} 参数数量 {len(args)} 不足 ({min_args})，{short_hint}",
                    )
                )
                continue

            # brushdata_arg 模式额外校验：声明过 brushdata 则调用应引用其一
            if brush_mode == "brushdata_arg" and declared_brushes:
                tokens = {tok for arg in args for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", arg)}
                if not (tokens & declared_brushes):
                    issues.append(
                        ValidationIssue(
                            ln_idx, Severity.ERROR, "PNT001",
                            f"{instr} 没有引用任何已声明的 brushdata "
                            f"({', '.join(sorted(declared_brushes))})",
                        )
                    )
    return issues


def _check_default_tcp(lines: list[str]) -> list[ValidationIssue]:
    """tooldata 偏移仍是默认 [0,0,200] 时强提示现场标定。"""
    issues: list[ValidationIssue] = []
    code = "\n".join(lines)
    for m in _TOOLDATA_DECL_RE.finditer(code):
        decl_body = m.group(2)
        # 计算声明所在行号（取 := 出现的位置）
        decl_pos = m.start()
        ln_idx = code.count("\n", 0, decl_pos) + 1
        if DEFAULT_TCP_PATTERN.search(decl_body):
            issues.append(
                ValidationIssue(
                    ln_idx, Severity.ERROR, "TCP001",
                    f"tooldata '{m.group(1)}' 使用默认占位 TCP [0,0,200]，"
                    "上控制器前必须 4 点法重新标定",
                )
            )
    return issues


def _looks_like_io_signal(
    name: str, prefixes: Iterable[str] = IO_SIGNAL_PREFIXES
) -> bool:
    """启发式：标识符以 IO 命名前缀开头才算 IO（前缀可经配置扩展）。

    仅用于消歧 `Reset <名>`（Reset 既可复位 DO，名字也可能是其它对象），
    避免把非 IO 标识符误报为 IO001。SetDO/PulseDO 等专用 IO 指令不走这里。
    """
    lower = name.lower()
    return any(lower.startswith(p.lower()) for p in prefixes)


def _extract_io_signal(rest: str) -> str | None:
    """从 IO 指令名之后的部分剥离开关参数，取第一个标识符为信号名。

    兼容带开关的写法，信号名可能在开关之后：
      PulseDO\\PLength:=3,B_dopaintfinish   → B_dopaintfinish
      SetDO\\SDelay:=0.5, doSprayOn, 1       → doSprayOn
      WaitDI diBrushOK, 1                    → diBrushOK
    """
    while True:
        s = _IO_SWITCH_RE.match(rest)
        if not s:
            break
        rest = rest[s.end():]
    m = _IDENT_RE.search(rest)
    return m.group(0) if m else None


def _check_io_whitelist(
    lines: list[str],
    whitelist: Iterable[str],
    io_signal_prefixes: Iterable[str] = IO_SIGNAL_PREFIXES,
) -> list[ValidationIssue]:
    """检查代码引用的 IO 信号是否都在 EIO.cfg 白名单中（大小写不敏感）。

    - SetDO/SetAO/WaitDI/WaitDO/PulseDO：操作数必为 IO 信号，恒校验，不论命名风格
      （现场如 Hand_A_StartSpray / B_dopaintfinish 也会被纳入校验）。
    - Reset：多义，仅当信号形似 IO（前缀启发式，可配置）才校验，否则跳过。
    注：WaitUntil 等通用表达式不做 IO 校验（可能引用普通布尔/数值，易误报）。
    去重：同一未知信号引用多次只报一次。
    """
    allowed = {s.lower() for s in whitelist}
    prefixes = tuple(io_signal_prefixes)
    issues: list[ValidationIssue] = []
    reported: set[str] = set()
    for ln_idx, raw in enumerate(lines, start=1):
        line = _strip_comments(raw)
        m = _IO_INSTR_RE.match(line)
        if not m:
            continue
        instr = m.group(1).lower()
        signal = _extract_io_signal(m.group(2))
        if not signal:
            continue
        key = signal.lower()
        if key in allowed:
            continue
        # Reset 多义：只有形似 IO 的名字才报，避免误伤非 IO 对象
        if instr not in _UNAMBIGUOUS_IO_INSTR and not _looks_like_io_signal(signal, prefixes):
            continue
        if key in reported:
            continue
        reported.add(key)
        issues.append(
            ValidationIssue(
                ln_idx, Severity.ERROR, "IO001",
                f"IO 信号 '{signal}' 不在 EIO.cfg 白名单中。"
                f"已知信号: {', '.join(sorted(whitelist)) or '(空)'}",
            )
        )
    return issues


def validate(
    code: str,
    *,
    controller: ControllerKind = "IRC5",
    io_whitelist: Iterable[str] | None = None,
    strict_tcp: bool = False,
    brush_mode: BrushMode = "setbrush",
    io_signal_prefixes: Iterable[str] = IO_SIGNAL_PREFIXES,
) -> ValidationReport:
    """对完整 RAPID 代码做静态校验。

    Args:
        code: RAPID 源码字符串
        controller: 控制器类型；"IRC5P" 时启用 PaintL/PaintC 参数检查
        io_whitelist: 控制器 EIO.cfg 中已注册的信号集；None 跳过 IO 检查
        strict_tcp: True 时若 tooldata 仍为默认 TCP 占位则报错（上线前应开启）
        brush_mode: IRC5P 工艺写法；"setbrush"（默认，PaintL 4 参数 + SetBrush）
            或 "brushdata_arg"（PaintL 5 参数，brushdata 作位置参数）
        io_signal_prefixes: IO 命名前缀，用于消歧 Reset 等多义指令（可配置以适配
            现场不规范命名）；SetDO/PulseDO 等专用 IO 指令不受其限制

    Returns:
        ValidationReport: 所有问题汇总
    """
    lines = code.splitlines()
    issues: list[ValidationIssue] = []
    issues.extend(_check_module_declaration(lines))
    issues.extend(_check_blocks(lines))
    issues.extend(_check_keyword_case(lines))
    issues.extend(_check_semicolons(lines))
    issues.extend(_check_quotes(lines))

    if controller == "IRC5P":
        issues.extend(_check_paint_brushdata(lines, brush_mode))
        if strict_tcp:
            issues.extend(_check_default_tcp(lines))

    if io_whitelist is not None:
        issues.extend(_check_io_whitelist(lines, io_whitelist, io_signal_prefixes))

    return ValidationReport(issues=tuple(issues))
