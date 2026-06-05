## IRC5P (ABB Paint 选项) 额外约束

当前目标控制器是 **IRC5P**，必须使用 ABB Paint 工艺指令，禁止用 MoveL + SetDO 凑喷涂。

### 必须遵守
1. **喷涂直线段**：用 `PaintL target, speed, zone, tool\WObj:=wobj;`（4 个位置参数），不要用 `MoveL + SetDO`。
2. **喷涂圆弧段**：用 `PaintC pMid, pEnd, speed, zone, tool\WObj:=wobj;`（5 个位置参数），不要用 `MoveC + SetDO`。
3. **选刷子**：用独立的 `SetBrush n;` 指令选择控制器 Brush Table 里第 `n` 号刷子（工艺参数：流量/扇幅/雾化/开关枪时序都在刷子表里配置）。在一段喷涂开始前 `SetBrush`，需要换工艺时再 `SetBrush` 另一个号。
4. **不要把 brushdata 当作 PaintL 的参数**：本控制器用 `SetBrush n` + 4 参数 `PaintL`，**不**在 `PaintL` 里写 brushdata，也**不**需要 `PERS brushdata` 声明。
5. **行间定位**：用 `MoveL target, v500, fine, tool\WObj:=wobj;`（不喷漆，仅定位到下一段起点）；回 Home 用 `MoveAbsJ jHomePos\NoEOffs, v600, z50, tool0;`。
6. **禁止 SetDO 切换喷涂主信号**：开关枪由刷子表内部时序自动管理。其他辅助 IO（风机、雾化）可用 `SetDO`。

### IRC5P 输出范例（SetBrush 写法）
```rapid
MODULE PaintProgram
    PERS tooldata tSprayGun := [TRUE, [[12.5,0.3,287.6],[1,0,0,0]], [2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE, TRUE, "", [[100,0,0],[1,0,0,0]], [[0,0,0],[1,0,0,0]]];
    CONST speeddata vPaint := [600, 500, 5000, 1000];

    CONST robtarget pStart := [[500,0,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pEnd := [[700,0,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    PROC main()
        ConfL\Off;
        SingArea\Wrist;
        MoveL pStart, v500, fine, tSprayGun\WObj:=wobjPart;
        SetBrush 1;
        PaintL pEnd, vPaint, z10, tSprayGun\WObj:=wobjPart;
    ENDPROC
ENDMODULE
```

### 现场标定提醒（务必在注释里给出）
- `tSprayGun` 的 TCP 需现场 4 点法标定，不能用占位值 [0,0,200]。
- `SetBrush n` 里的刷子号要对应控制器 Brush Table 中已配置的工艺，上控制器前在 RobotStudio 中核对刷子表。

> 注：少数老配置把 brushdata 当作 `PaintL` 的位置参数（`PaintL p, v, brushdata, zone, tool`）。本控制器用上面的 `SetBrush` 写法；除非明确要求，否则不要用 brushdata 形参写法。
