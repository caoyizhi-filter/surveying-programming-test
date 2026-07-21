# file_io.py
# 读取 curve_input.txt，输出 road_curve_result.txt

from calculator import RoadCurve


# ══════════════════════════════════════════════════════════════
#  读取输入文件
# ══════════════════════════════════════════════════════════════

def read_input(filepath: str) -> RoadCurve:
    """
    解析 curve_input.txt，返回 RoadCurve 对象。

    文件格式（制表符分隔）：
        序号\tJD里程,半径,偏角度,偏角分,偏角秒

    示例：
        1\t1326.480,280,32,16,42
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.readline().strip()
        if not raw:
            raise ValueError("输入文件为空")

    # 按制表符拆分为序号和数据
    parts = raw.split("\t")
    if len(parts) < 2:
        # 尝试逗号分隔（兼容无序号格式）
        data = parts[0].split(",")
    else:
        data = parts[1].split(",")

    if len(data) < 5:
        raise ValueError(f"数据列不足，期望5列（JD,R,度,分,秒），实际{len(data)}列")

    JD_stake  = float(data[0])
    R         = float(data[1])
    alpha_deg = float(data[2])
    alpha_min = float(data[3])
    alpha_sec = float(data[4])

    return RoadCurve(JD_stake, R, alpha_deg, alpha_min, alpha_sec)


# ══════════════════════════════════════════════════════════════
#  写出结果文件（13项）
# ══════════════════════════════════════════════════════════════

def write_result(filepath: str, curve: RoadCurve):
    """
    按试题册格式输出 road_curve_result.txt（13项）
    """
    rows = [
        (1,  "JD原始里程",          f"{curve.JD_stake:.3f}"),
        (2,  "圆曲线半径R",         f"{curve.R:.0f}"),
        (3,  "路偏角α(十进制度)",   f"{curve.alpha_deg:.4f}"),
        (4,  "切线长T",             f"{curve.T:.3f}"),
        (5,  "曲线总长L",           f"{curve.L:.3f}"),
        (6,  "外距E",               f"{curve.E:.3f}"),
        (7,  "校差值D",             f"{curve.D:.3f}"),
        (8,  "直圆点ZY里程",        f"{curve.ZY:.3f}"),
        (9,  "曲中点QZ里程",        f"{curve.QZ:.3f}"),
        (10, "圆直点YZ里程",        f"{curve.YZ:.3f}"),
        (11, "校核JD里程",          f"{curve.JD_check:.3f}"),
        (12, "指定桩号距ZY弧长l",   f"{curve.l:.3f}"),
        (13, f"指定桩号局部坐标(x,y)", f"{curve.x:.3f},{curve.y:.3f}"),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,说明,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
