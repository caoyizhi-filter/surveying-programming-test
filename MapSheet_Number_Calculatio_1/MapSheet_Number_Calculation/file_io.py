# file_io.py
# 读取 topo_map.txt，输出 topo_result.txt（30项）

from calculator import GeoPoint, TopoCalculator, dms_to_dec, dec_to_dms


# ══════════════════════════════════════════════════════════════
#  读取输入文件
# ══════════════════════════════════════════════════════════════

def read_input(filepath: str) -> TopoCalculator:
    """
    解析 topo_map.txt
    格式：点号,纬度B,经度L
    例：Point1,34°45′30″,113°30′15″
    """
    calc = TopoCalculator()
    with open(filepath, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) != 3:
                raise ValueError(f"第{lineno}行格式错误（需3列）：{line}")
            name  = parts[0].strip()
            B_dec = dms_to_dec(parts[1].strip())
            L_dec = dms_to_dec(parts[2].strip())
            calc.points.append(GeoPoint(name, B_dec, L_dec))
    if not calc.points:
        raise ValueError("文件为空或格式错误")
    return calc


# ══════════════════════════════════════════════════════════════
#  写出结果文件（30项）
# ══════════════════════════════════════════════════════════════

def write_result(filepath: str, calc: TopoCalculator):
    res = calc.result
    p1  = res.points[0]    # Point1
    p2  = res.points[1]    # Point2
    bnd = p1.boundary_10w

    rows = [
        (1,  "Point1十进制度纬度",          f"{p1.B:.4f}"),
        (2,  "Point1十进制度经度",          f"{p1.L:.4f}"),
        (3,  "Point1 1:100万图幅编号",      p1.codes["100万"]),
        (4,  "Point1 1:50万图幅编号",       p1.codes["50万"]),
        (5,  "Point1 1:25万图幅编号",       p1.codes["25万"]),
        (6,  "Point1 1:10万图幅编号",       p1.codes["10万"]),
        (7,  "Point1 1:5万图幅编号",        p1.codes["5万"]),
        (8,  "Point1 1:2.5万图幅编号",      p1.codes["2.5万"]),
        (9,  "Point1 1:1万图幅编号",        p1.codes["1万"]),
        (10, "Point1 1:5千图幅编号",        p1.codes["5千"]),
        (11, "Point1所在1:10万图幅北界",    dec_to_dms(bnd["北"])),
        (12, "Point1所在1:10万图幅南界",    dec_to_dms(bnd["南"])),
        (13, "Point1所在1:10万图幅东界",    dec_to_dms(bnd["东"])),
        (14, "Point1所在1:10万图幅西界",    dec_to_dms(bnd["西"])),
        (15, "Point2 1:10万图幅编号",       p2.codes["10万"]),
        (16, "Point2 1:5万图幅编号",        p2.codes["5万"]),
        (17, "Point2 1:1万图幅编号",        p2.codes["1万"]),
        (18, "Point2所在图幅中心点纬度",    f"{p2.center_5w[0]:.4f}"),
        (19, "Point2所在图幅中心点经度",    f"{p2.center_5w[1]:.4f}"),
        (20, "1:10万图幅总数",              str(res.count_10w)),
        (21, "1:5万图幅总数",               str(res.count_5w)),
        (22, "1:1万图幅总数",               str(res.count_1w)),
        (23, "平均纬度值",                  f"{res.avg_B:.4f}"),
        (24, "平均经度值",                  f"{res.avg_L:.4f}"),
        (25, "最北点纬度",                  dec_to_dms(res.max_B_pt.B)),
        (26, "最南点纬度",                  dec_to_dms(res.min_B_pt.B)),
        (27, "最东点经度",                  dec_to_dms(res.max_L_pt.L)),
        (28, "最西点经度",                  dec_to_dms(res.min_L_pt.L)),
        (29, "总点数",                      str(res.total_points)),
        (30, "跨图幅点数",                  str(res.cross_points)),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,说明,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
