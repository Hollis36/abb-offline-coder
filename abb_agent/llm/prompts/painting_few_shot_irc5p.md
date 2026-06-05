# 喷涂场景示例 · IRC5P（Few-Shot）

下面是 **IRC5P（ABB Paint 选项）** 的"需求→代码"对。
统一用 **`SetBrush n` 选刷子表 + 4 参数 `PaintL` / 5 参数 `PaintC`** 走原生工艺，
**不要**把 brushdata 当作 PaintL 的参数，也**不要**用 `MoveL`+`SetDO` 凑喷涂；
行间纯定位用不带工艺的 `MoveL`，回 Home 用 `MoveAbsJ`。
tooldata 的 TCP 用现场标定值（非占位 [0,0,200]），robtarget 坐标仅为占位。

---

## 示例 1：平板单道直线喷涂（SetBrush + PaintL）

**需求**：在平板上从 P1 到 P2 喷一道直线，速度 v600。

```rapid
MODULE PaintPlateLineP
    ! 平板单道直线喷涂 (IRC5P SetBrush + PaintL)
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[0,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    CONST speeddata vPaint := [600,500,5000,1000];
    CONST robtarget pStart := [[500,0,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pEnd := [[500,500,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    PROC main()
        ConfL\Off;
        SingArea\Wrist;
        ! 定位到起点（不喷）
        MoveL pStart, v500, fine, tSprayGun\WObj:=wobjPart;
        ! 选 1 号刷子，然后喷涂直线段（开关枪由刷子表时序自动管理）
        SetBrush 1;
        PaintL pEnd, vPaint, z10, tSprayGun\WObj:=wobjPart;
        ! 回 Home
        MoveAbsJ jHomePos\NoEOffs, v600, z50, tool0;
    ENDPROC
ENDMODULE
```

---

## 示例 2：平板 Z 字扫描（SetBrush + PaintL + FOR 循环）

**需求**：在 500(X) x 300(Y) 平板上做 Z 字扫描，行距 50mm，速度 v600。

```rapid
MODULE PaintPlateZigzagP
    ! 平板 Z 字扫描喷涂 (IRC5P SetBrush + PaintL)
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[0,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    CONST speeddata vPaint := [600,500,5000,1000];

    PROC main()
        VAR num i := 0;
        VAR num yPos := 0;
        VAR robtarget pStart;
        VAR robtarget pEnd;
        ConfL\Off;
        SingArea\Wrist;
        SetBrush 1;
        FOR i FROM 0 TO 6 DO
            yPos := i * 50;
            ! 偶数行 X 正向，奇数行 X 负向
            IF i MOD 2 = 0 THEN
                pStart := [[0,yPos,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
                pEnd := [[500,yPos,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
            ELSE
                pStart := [[500,yPos,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
                pEnd := [[0,yPos,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
            ENDIF
            ! 行起点定位（不喷）→ 整行 PaintL
            MoveL pStart, v500, fine, tSprayGun\WObj:=wobjPart;
            PaintL pEnd, vPaint, z30, tSprayGun\WObj:=wobjPart;
        ENDFOR
    ENDPROC
ENDMODULE
```

---

## 示例 3：车门外板 Z 字喷涂（SetBrush + PaintL）

**需求**：车门外板约 1000(X) x 500(Y)mm，Z 字扫描，行距 60mm，速度 v600。

```rapid
MODULE PaintCarDoorP
    ! 车门外板 Z 字喷涂 (IRC5P SetBrush + PaintL)
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjDoor := [FALSE,TRUE,"",[[1200,0,800],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    CONST speeddata vPaint := [600,400,5000,1000];

    PROC main()
        VAR num i := 0;
        VAR num yPos := 0;
        VAR robtarget pStart;
        VAR robtarget pEnd;
        ConfL\Off;
        SingArea\Wrist;
        SetBrush 2;
        FOR i FROM 0 TO 8 DO
            yPos := i * 60;
            IF i MOD 2 = 0 THEN
                pStart := [[0,yPos,250],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
                pEnd := [[1000,yPos,250],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
            ELSE
                pStart := [[1000,yPos,250],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
                pEnd := [[0,yPos,250],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
            ENDIF
            MoveL pStart, v500, fine, tSprayGun\WObj:=wobjDoor;
            PaintL pEnd, vPaint, z30, tSprayGun\WObj:=wobjDoor;
        ENDFOR
    ENDPROC
ENDMODULE
```

---

## 示例 4：曲面圆弧喷涂（SetBrush + PaintC）

**需求**：沿圆弧轨迹喷涂，3 点定义圆弧（起点-中点-终点），速度 v600。

```rapid
MODULE PaintArcP
    ! 曲面圆弧喷涂 (IRC5P SetBrush + PaintC)
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[0,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    CONST speeddata vPaint := [600,500,5000,1000];
    CONST robtarget pStart := [[300,0,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pMid := [[400,200,350],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pEnd := [[300,400,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    PROC main()
        ConfL\Off;
        SingArea\Wrist;
        MoveL pStart, v500, fine, tSprayGun\WObj:=wobjPart;
        ! 选刷子后走圆弧：pMid 定弧，pEnd 收尾（5 参数 PaintC）
        SetBrush 1;
        PaintC pMid, pEnd, vPaint, z10, tSprayGun\WObj:=wobjPart;
        MoveAbsJ jHomePos\NoEOffs, v600, z50, tool0;
    ENDPROC
ENDMODULE
```

---

## 示例 5：多道切换刷子 + 辅助风机/雾化

**需求**：不同段用不同刷子号，配合风机、雾化。

说明：换工艺时再 `SetBrush` 另一个号（开关枪时序由刷子表自动管理）；
风机/雾化等辅助 IO 用 `SetDO` 控制。

```rapid
MODULE PaintMultiBrushP
    ! 多道喷涂:分段切换刷子号;辅助风机/雾化用 SetDO
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[0,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    CONST speeddata vPaint := [600,500,5000,1000];
    CONST robtarget p10 := [[967,-1332,1108],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget p20 := [[-894,-1354,1093],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget p30 := [[-888,-1497,1098],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    PROC main()
        ConfL\Off;
        SingArea\Wrist;
        ! 喷涂前开辅助设备
        SetDO doFanOn, 1;
        SetDO doAtomOn, 1;
        MoveL p10, v500, fine, tSprayGun\WObj:=wobjPart;
        SetBrush 1;
        PaintL p20, vPaint, z30, tSprayGun\WObj:=wobjPart;
        ! 换 2 号刷子继续
        SetBrush 2;
        PaintL p30, vPaint, fine, tSprayGun\WObj:=wobjPart;
        ! 喷涂后关辅助设备
        Reset doAtomOn;
        Reset doFanOn;
    ENDPROC
ENDMODULE
```
