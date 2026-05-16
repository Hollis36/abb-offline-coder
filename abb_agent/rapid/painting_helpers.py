"""喷涂场景专用 RAPID 代码片段生成器。

这些函数提供"参数化模板"能力 —— LLM 可以选择性调用它们生成关键代码块，
保证语法 100% 正确。即使 LLM 表现差，关键路径仍可用。

所有函数都是纯函数，返回 RAPID 代码字符串。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pose:
    """笛卡尔位姿 (x,y,z + 欧拉/四元数)。这里用四元数表达。"""

    x: float
    y: float
    z: float
    q1: float = 1.0
    q2: float = 0.0
    q3: float = 0.0
    q4: float = 0.0

    def to_robtarget_pos(self) -> str:
        return f"[{self.x},{self.y},{self.z}]"

    def to_robtarget_orient(self) -> str:
        return f"[{self.q1},{self.q2},{self.q3},{self.q4}]"


@dataclass(frozen=True)
class BrushParams:
    """笔刷/喷涂工艺参数。"""

    flow_rate: int = 80
    fan_width: int = 300
    atom_pressure: int = 50
    pre_open_ms: int = 50
    post_close_ms: int = 50


def brush_data_decl(name: str = "bdMain", params: BrushParams | None = None) -> str:
    """生成 brushdata 声明。

    注意：brushdata 是 ABB Paint 选项才有的特殊数据类型。普通 IRC5 无 Paint
    选项时，用我们自定义的 num/PERS 表示。
    """
    p = params or BrushParams()
    return (
        f"    ! 喷涂工艺参数 - {name}\n"
        f"    PERS num {name}_flow := {p.flow_rate};        ! 流量百分比\n"
        f"    PERS num {name}_fan := {p.fan_width};         ! 扇幅宽度 mm\n"
        f"    PERS num {name}_atom := {p.atom_pressure};    ! 雾化压力 kPa\n"
        f"    PERS num {name}_preOpen := {p.pre_open_ms};   ! 喷枪提前开 ms\n"
        f"    PERS num {name}_postClose := {p.post_close_ms};! 喷枪延迟关 ms"
    )


def robtarget_decl(name: str, pose: Pose, conf: str = "[0,0,0,0]", extax: str = "[9E9,9E9,9E9,9E9,9E9,9E9]") -> str:
    """生成 robtarget 声明。"""
    return (
        f"CONST robtarget {name} := ["
        f"{pose.to_robtarget_pos()},"
        f"{pose.to_robtarget_orient()},"
        f"{conf},{extax}];"
    )


def linear_scan(
    start: Pose,
    end: Pose,
    *,
    speed: str = "vPaint",
    zone: str = "z10",
    tool: str = "tSprayGun",
    wobj: str = "wobjPart",
    spray_signal: str = "doSprayOn",
) -> str:
    """生成"开喷 → 直线扫描 → 关喷"RAPID 片段。"""
    return (
        f"        ! 直线扫描喷涂段\n"
        f"        MoveL {robtarget_inline(start)}, v200, fine, {tool}\\WObj:={wobj};\n"
        f"        SetDO {spray_signal}, 1;\n"
        f"        MoveL {robtarget_inline(end)}, {speed}, {zone}, {tool}\\WObj:={wobj};\n"
        f"        SetDO {spray_signal}, 0;"
    )


def robtarget_inline(pose: Pose, conf: str = "[0,0,0,0]") -> str:
    """生成内联 robtarget 字面量。"""
    return (
        f"[{pose.to_robtarget_pos()},{pose.to_robtarget_orient()},"
        f"{conf},[9E9,9E9,9E9,9E9,9E9,9E9]]"
    )


def zigzag_scan(
    origin: Pose,
    width: float,
    height: float,
    *,
    row_spacing: float = 50.0,
    speed: str = "vPaint",
    zone: str = "z10",
    tool: str = "tSprayGun",
    wobj: str = "wobjPart",
    spray_signal: str = "doSprayOn",
) -> str:
    """Z 字扫描喷涂。

    工件坐标系下从 origin 开始，沿 X 方向往返，每次 Y 偏移 row_spacing。
    """
    num_rows = int(height / row_spacing) + 1
    lines = ["        ! Z 字扫描喷涂"]
    for i in range(num_rows):
        y_off = i * row_spacing
        # 偶数行向右，奇数行向左
        x_start = origin.x if i % 2 == 0 else origin.x + width
        x_end = origin.x + width if i % 2 == 0 else origin.x
        p_start = Pose(x_start, origin.y + y_off, origin.z, origin.q1, origin.q2, origin.q3, origin.q4)
        p_end = Pose(x_end, origin.y + y_off, origin.z, origin.q1, origin.q2, origin.q3, origin.q4)

        # 移动到起点（高速 fine）
        lines.append(
            f"        MoveL {robtarget_inline(p_start)}, v500, fine, {tool}\\WObj:={wobj};"
        )
        lines.append(f"        SetDO {spray_signal}, 1;")
        lines.append(
            f"        MoveL {robtarget_inline(p_end)}, {speed}, {zone}, {tool}\\WObj:={wobj};"
        )
        lines.append(f"        SetDO {spray_signal}, 0;")
    return "\n".join(lines)


def trigg_io_setup(
    trigg_name: str,
    distance_mm: float,
    signal: str = "doSprayOn",
    value: int = 1,
) -> str:
    """TriggIO 同步喷枪开关。

    用于把 IO 切换精确锁定到路径上的某个距离点，避免普通 SetDO 的时延误差。
    """
    return (
        f"        ! TriggIO 触发 - 距离起点 {distance_mm}mm 时切换 {signal}\n"
        f"        VAR triggdata {trigg_name};\n"
        f"        TriggIO {trigg_name}, {distance_mm} \\DOp:={signal}, {value};"
    )


def trigg_l_movement(
    target: str,
    trigg_data: str,
    *,
    speed: str = "vPaint",
    zone: str = "z10",
    tool: str = "tSprayGun",
    wobj: str = "wobjPart",
) -> str:
    """带触发的直线移动。"""
    return (
        f"        TriggL {target}, {speed}, {trigg_data}, {zone}, "
        f"{tool}\\WObj:={wobj};"
    )


def tcp_calibration_program(name: str = "CalibrateSprayTCP") -> str:
    """生成喷枪 TCP 校准程序模板。

    使用 4 点法：选定空间中固定参考点（如校准针尖），让喷枪 TCP 从 4 个不同
    姿态接触该点，机器人控制器自动计算 TCP 偏移。
    """
    return (
        f"PROC {name}()\n"
        f"        ! 喷枪 TCP 校准 - 4 点法\n"
        f"        ! 操作步骤：\n"
        f"        !   1. 在空间中固定一根校准针（参考点）\n"
        f"        !   2. 手动将喷枪嘴对准针尖（不同姿态 4 次）\n"
        f"        !   3. 每次到位后按下示教器按钮记录该点\n"
        f"        !   4. 4 点采集后控制器自动算出 TCP\n"
        f"        ! 推荐：在示教器中使用 \"Hand Guide\" 配合 Define 功能完成\n"
        f"        ConfL\\Off;\n"
        f"        SingArea\\Wrist;\n"
        f"        TPWrite \"请按示教器引导，依次到达 4 个校准位姿\";\n"
        f"        WaitTime 1;\n"
        f"        ! 校准结果会自动写入 tSprayGun.tframe\n"
        f"    ENDPROC"
    )


def arc_segment(p_start: Pose, p_mid: Pose, p_end: Pose, *, speed: str = "vPaint", zone: str = "z10",
                tool: str = "tSprayGun", wobj: str = "wobjPart") -> str:
    """圆弧路径段（MoveC）。"""
    return (
        f"        MoveC {robtarget_inline(p_mid)}, {robtarget_inline(p_end)}, "
        f"{speed}, {zone}, {tool}\\WObj:={wobj};"
    )
