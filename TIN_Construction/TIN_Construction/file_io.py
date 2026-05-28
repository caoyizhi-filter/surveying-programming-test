# file_io.py
# 读取 input3.txt，输出 result3.txt

from calculator import Point3D, TINCalculator


# ══════════════════════════════════════════════════════════════
#  读取输入文件
# ══════════════════════════════════════════════════════════════

def read_input(filepath: str) -> TINCalculator:
    """
    解析 input3.txt，返回配置好的 TINCalculator。
    格式：跳过 === 注释行和中文说明行，只读数字行。
    """
    data_lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("=") or ("\u4e00" <= line[0] <= "\u9fff"):
                continue
            parts = line.split()
            try:
                [float(p) for p in parts]
                data_lines.append(parts)
            except ValueError:
                continue

    if len(data_lines) < 3:
        raise ValueError("数据行不足，请检查文件格式")

    calc = TINCalculator()

    # 第1行：基准高程 Hd
    calc.Hd = float(data_lines[0][0])

    # 第2行：点数 n
    n = int(float(data_lines[1][0]))

    # 第3行起：n 个点坐标
    if len(data_lines) < 2 + n:
        raise ValueError(f"期望 {n} 个点，实际只有 {len(data_lines)-2} 个")

    for i in range(n):
        row = data_lines[2 + i]
        calc.points.append(Point3D(
            idx=i+1,
            x=float(row[0]),
            y=float(row[1]),
            z=float(row[2])
        ))

    return calc


# ══════════════════════════════════════════════════════════════
#  写出结果文件
# ══════════════════════════════════════════════════════════════

def write_result(filepath: str, calc: TINCalculator):
    """
    输出 result3.txt（7项）
    """
    res = calc.result
    rows = [
        (1, "总点数",    str(res.total_points)),
        (2, "z_min",    f"{res.z_min:.2f}"),
        (3, "z_max",    f"{res.z_max:.2f}"),
        (4, "总面积",    f"{res.total_area:.2f}"),
        (5, "填方",      f"{res.fill_volume:.2f}"),
        (6, "挖方",      f"{res.cut_volume:.2f}"),
        (7, "三角形数",  str(res.triangle_count)),
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,说明,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
