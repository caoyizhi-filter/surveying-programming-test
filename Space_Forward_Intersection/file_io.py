# file_io.py
# 读取 input1.txt，输出 result1.txt

from calculator import ImageData, SpaceIntersection


# ══════════════════════════════════════════════════════════════
#  读取输入文件
# ══════════════════════════════════════════════════════════════

def read_input(filepath: str) -> SpaceIntersection:
    """
    解析 input1.txt，返回配置好的 SpaceIntersection 对象。
    格式：跳过以 "=" 或空白或汉字说明开头的行，
         只读取纯数字行。
    """
    solver = SpaceIntersection()
    data_lines = []

    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            # 跳过空行、注释行（以=或中文开头）
            if not line:
                continue
            first = line[0]
            if first == "=" or "\u4e00" <= first <= "\u9fff":
                continue
            # 尝试解析为数字行
            parts = line.split()
            try:
                [float(p) for p in parts]
                data_lines.append(parts)
            except ValueError:
                continue

    if len(data_lines) < 4:
        raise ValueError(f"数据行不足，只解析到 {len(data_lines)} 行，期望4行")

    # 第1行：左片外方位元素
    L = data_lines[0]
    left = ImageData(
        Xs=float(L[0]), Ys=float(L[1]), Zs=float(L[2]),
        phi_deg=float(L[3]), omega_deg=float(L[4]), kappa_deg=float(L[5])
    )

    # 第2行：右片外方位元素
    R = data_lines[1]
    right = ImageData(
        Xs=float(R[0]), Ys=float(R[1]), Zs=float(R[2]),
        phi_deg=float(R[3]), omega_deg=float(R[4]), kappa_deg=float(R[5])
    )

    # 第3行：内方位元素 x0 y0 f
    C = data_lines[2]
    solver.x0 = float(C[0])
    solver.y0 = float(C[1])
    solver.f  = float(C[2])

    # 第4行：同名像点坐标 x1 y1 x2 y2
    P = data_lines[3]
    solver.x1 = float(P[0])
    solver.y1 = float(P[1])
    solver.x2 = float(P[2])
    solver.y2 = float(P[3])

    solver.left  = left
    solver.right = right
    return solver


# ══════════════════════════════════════════════════════════════
#  写出结果文件
# ══════════════════════════════════════════════════════════════

def write_result(filepath: str, solver: SpaceIntersection):
    """
    按试题册格式输出 result1.txt（7项）
    """
    res = solver.result
    L   = solver.left
    R   = solver.right

    rows = [
        (1, "地面点X",  f"{res.X:.3f}"),
        (2, "地面点Y",  f"{res.Y:.3f}"),
        (3, "地面点Z",  f"{res.Z:.3f}"),
        (4, "φ1弧度",   f"{L.phi:.6f}"),
        (5, "κ2弧度",   f"{R.kappa:.6f}"),
        (6, "左a1",     f"{L.a1:.6f}"),
        (7, "右b2",     f"{R.b2:.6f}"),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,说明,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
