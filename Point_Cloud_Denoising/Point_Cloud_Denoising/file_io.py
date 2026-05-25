# file_io.py
# 读取 point.txt，输出 result.txt（30项）

from calculator import Point


# ══════════════════════════════════════════════════════════════
#  读取点云文件
# ══════════════════════════════════════════════════════════════

def read_points(filepath: str) -> list:
    """
    读取 point.txt，每行 "x y z"（空格分隔）
    返回 list[Point]，序号从 1 开始
    """
    points = []
    with open(filepath, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"第{lineno}行格式错误：{line}")
            x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
            points.append(Point(lineno, x, y, z))
    return points


# ══════════════════════════════════════════════════════════════
#  输出结果文件
# ══════════════════════════════════════════════════════════════

def write_result(filepath: str, proc, points: list):
    """
    按试题册格式输出 result.txt，共29项（序号1-29）
    proc: PointCloudProcessor 实例（已 run 完毕）
    """
    p1  = points[0]    # P1  第1个点
    p6  = points[5]    # P6  第6个点
    p789= points[788]  # P789 第789个点

    # 网格(0,0,0)内的点数
    grid_000 = len(proc.grid.get((0, 0, 0), []))

    rows = [
        (1,  "点P1的x坐标",                    f"{p1.x:.3f}"),
        (2,  "点P6的y坐标",                    f"{p6.y:.3f}"),
        (3,  "点P789的z坐标",                  f"{p789.z:.3f}"),
        (4,  "原始点云总点数",                  str(len(points))),
        (5,  "点云数据x最大值",                 f"{proc.xmax:.3f}"),
        (6,  "点云数据y最大值",                 f"{proc.ymax:.3f}"),
        (7,  "点云数据z最大值",                 f"{proc.zmax:.3f}"),
        (8,  "格网xmin",                       f"{proc.xmin:.3f}"),
        (9,  "格网xmax1",                      f"{proc.xmax1:.3f}"),
        (10, "格网ymin",                       f"{proc.ymin:.3f}"),
        (11, "格网ymax1",                      f"{proc.ymax1:.3f}"),
        (12, "格网zmin",                       f"{proc.zmin:.3f}"),
        (13, "格网zmax1",                      f"{proc.zmax1:.3f}"),
        (14, "网格(0,0,0)内的点个数",           str(grid_000)),
        (15, "点P1的网格索引i分量",             str(p1.gi)),
        (16, "点P6的网格索引j分量",             str(p6.gj)),
        (17, "点P1的候选点总数",               str(p1.candidates)),
        (18, "点P6的候选点总数",               str(p6.candidates)),
        (19, "点P1的6个邻近点序号中最大值",     str(max(p1.neighbors))),
        (20, "点P6的6个邻近点序号中最大值",     str(max(p6.neighbors))),
        (21, "点P1的邻域平均距离u1",            f"{p1.mean_dist:.3f}"),
        (22, "点P1的邻域距离标准差σ1",          f"{p1.std_dist:.3f}"),
        (23, "点P6的邻域平均距离u6",            f"{p6.mean_dist:.3f}"),
        (24, "点P6的邻域距离标准差σ6",          f"{p6.std_dist:.3f}"),
        (25, "全局平均距离均值μ",              f"{proc.global_mean:.3f}"),
        (26, "全局距离标准差σ",               f"{proc.global_std:.3f}"),
        (27, "点P1是否为噪声点(1=是,0=否)",    str(p1.is_noise)),
        (28, "点P6是否为噪声点(1=是,0=否)",    str(p6.is_noise)),
        (29, "去噪后保留的点云总数",            str(proc.clean_count)),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,说明,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
