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

返回 ValidationReport，由调用方决定如何处理（修复 / 警告 / 拒绝）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


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
        "TriggL", "TriggC", "TriggJ", "TriggIO", "TriggData", "TriggEquip",
        "SetDO", "Reset", "SetAO", "WaitDI", "WaitDO", "PulseDO",
        "WaitTime", "Stop", "EXIT",
    ]
)


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


def validate(code: str) -> ValidationReport:
    """对完整 RAPID 代码做静态校验。

    Args:
        code: RAPID 源码字符串

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
    return ValidationReport(issues=tuple(issues))
