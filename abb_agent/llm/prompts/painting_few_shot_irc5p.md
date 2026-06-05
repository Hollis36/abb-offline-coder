# 喷涂场景示例 · IRC5P（Few-Shot）

下面是 **IRC5P（ABB Paint 选项）** 的"需求→代码"对。
统一用 `PaintL` / `PaintC` + `PERS brushdata` 走原生工艺，**不要用 `MoveL`+`SetDO` 凑喷涂**；
行间纯定位仍用不带 brushdata 的 `MoveL`。tooldata 的 TCP 用现场标定值（非占位 [0,0,200]），
robtarget 坐标仅为占位，实际由现场示教。

---

## 示例 1：平板单道直线喷涂（PaintL）

**需求**：在平板上从 P1 到 P2 喷一道直线，速度 v200，开关枪由工艺自动管理。

```rapid
MODULE PaintPlateLineP
    ! 平板单道直线喷涂 (IRC5P PaintL)
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[0,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    PERS brushdata bdMain := [80,300,50,50,50,0,FALSE,"bdMain",0];
    CONST speeddata vPaint := [200,500,5000,1000];
    CONST robtarget pStart := [[500,0,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pEnd := [[500,500,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    PROC main()
        ConfL\Off;
        SingArea\Wrist;
        ! 定位到起点（不喷）
        MoveL pStart, v500, fine, tSprayGun\WObj:=wobjPart;
        ! PaintL：brushdata 内部按 preOpen/postClose 自动开关枪
        PaintL pEnd, vPaint, bdMain, z10, tSprayGun\WObj:=wobjPart;
        ! 撤离
        MoveJ pStart, v1000, z50, tSprayGun\WObj:=wobjPart;
    ENDPROC
ENDMODULE
```

---

## 示例 2：平板 Z 字扫描（PaintL + FOR 循环）

**需求**：在 500(X) x 300(Y) 平板上做 Z 字扫描，行距 50mm，速度 v200。

```rapid
MODULE PaintPlateZigzagP
    ! 平板 Z 字扫描喷涂 (IRC5P PaintL)
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[0,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    PERS brushdata bdMain := [80,300,50,50,50,0,FALSE,"bdMain",0];
    CONST speeddata vPaint := [200,500,5000,1000];

    PROC main()
        VAR num i := 0;
        VAR num yPos := 0;
        VAR robtarget pStart;
        VAR robtarget pEnd;
        ConfL\Off;
        SingArea\Wrist;
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
            PaintL pEnd, vPaint, bdMain, z10, tSprayGun\WObj:=wobjPart;
        ENDFOR
    ENDPROC
ENDMODULE
```

---

## 示例 3：车门外板 Z 字喷涂（PaintL）

**需求**：车门外板约 1000(X) x 500(Y)mm，Z 字扫描，行距 60mm，速度 v150。

```rapid
MODULE PaintCarDoorP
    ! 车门外板 Z 字喷涂 (IRC5P PaintL)
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjDoor := [FALSE,TRUE,"",[[1200,0,800],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    PERS brushdata bdDoor := [85,350,55,60,60,0,FALSE,"bdDoor",0];
    CONST speeddata vPaint := [150,400,5000,1000];

    PROC main()
        VAR num i := 0;
        VAR num yPos := 0;
        VAR robtarget pStart;
        VAR robtarget pEnd;
        ConfL\Off;
        SingArea\Wrist;
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
            PaintL pEnd, vPaint, bdDoor, z10, tSprayGun\WObj:=wobjDoor;
        ENDFOR
    ENDPROC
ENDMODULE
```

---

## 示例 4：曲面圆弧喷涂（PaintC）

**需求**：沿圆弧轨迹喷涂，3 点定义圆弧（起点-中点-终点），速度 v200。

```rapid
MODULE PaintArcP
    ! 曲面圆弧喷涂 (IRC5P PaintC)
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[0,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    PERS brushdata bdMain := [80,300,50,50,50,0,FALSE,"bdMain",0];
    CONST speeddata vPaint := [200,500,5000,1000];
    CONST robtarget pStart := [[300,0,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pMid := [[400,200,350],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pEnd := [[300,400,400],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    PROC main()
        ConfL\Off;
        SingArea\Wrist;
        MoveL pStart, v500, fine, tSprayGun\WObj:=wobjPart;
        ! PaintC：圆弧喷涂，pMid 定弧、pEnd 收尾
        PaintC pMid, pEnd, vPaint, bdMain, z10, tSprayGun\WObj:=wobjPart;
        MoveJ pStart, v1000, z50, tSprayGun\WObj:=wobjPart;
    ENDPROC
ENDMODULE
```

---

## 示例 5：精确开关枪时序 + 辅助风机/雾化

**需求**：要求精确开关枪（避免延时）并配合风机、雾化。

说明：IRC5P 不用 IRC5 的 `TriggIO`——开关枪时序由 brushdata 的 `preOpen`/`postClose`
字段在控制器内部精确管理（本例 preOpen=80ms、postClose=60ms）；
风机/雾化等辅助 IO 仍用 `SetDO` 控制。

```rapid
MODULE PaintSyncBrushP
    ! 精确开关枪由 brushdata preOpen/postClose 管理；辅助 IO 用 SetDO
    PERS tooldata tSprayGun := [TRUE,[[12.5,0.3,287.6],[1,0,0,0]],[2.5,[0,0,80],[1,0,0,0],0,0,0]];
    PERS wobjdata wobjPart := [FALSE,TRUE,"",[[0,0,0],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    ! preOpen=80ms 提前开枪, postClose=60ms 延迟关枪
    PERS brushdata bdFine := [70,250,55,80,60,0,FALSE,"bdFine",0];
    CONST speeddata vPaint := [200,500,5000,1000];
    CONST robtarget pStart := [[400,0,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pEnd := [[400,600,300],[0,0,1,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];

    PROC main()
        ConfL\Off;
        SingArea\Wrist;
        ! 喷涂前开辅助设备
        SetDO doFanOn, 1;
        SetDO doAtomOn, 1;
        WaitTime 0.5;
        MoveL pStart, v500, fine, tSprayGun\WObj:=wobjPart;
        ! brushdata 自动按 preOpen/postClose 精确开关枪
        PaintL pEnd, vPaint, bdFine, z10, tSprayGun\WObj:=wobjPart;
        ! 喷涂后关辅助设备
        Reset doAtomOn;
        Reset doFanOn;
    ENDPROC
ENDMODULE
```
