# file_io.py
# 读取 plane_cloud.txt，输出 plane_analysis_result.txt（43项）
# 格式：点号,x,y,z（4列，第1列为点号）

from calculator import Point3D, RANSACCalculator


def read_input(filepath: str) -> RANSACCalculator:
    """
    读取 plane_cloud.txt。
    格式：P1,x,y,z （4列，第1列为点号）
    跳过 # 注释行和空行。
    """
    calc = RANSACCalculator()
    idx  = 1
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")

            # 4列：点号, x, y, z
            if len(parts) == 4:
                try:
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    z = float(parts[3].strip())
                except ValueError:
                    continue

            # 3列纯数字兼容
            elif len(parts) == 3:
                try:
                    x = float(parts[0].strip())
                    y = float(parts[1].strip())
                    z = float(parts[2].strip())
                except ValueError:
                    continue

            else:
                continue

            calc.points.append(Point3D(idx, x, y, z))
            idx += 1

    if not calc.points:
        raise ValueError("文件为空或格式错误，支持 P1,x,y,z 或 x,y,z 两种格式")
    return calc


def write_result(filepath: str, calc: RANSACCalculator):
    """
    输出 plane_analysis_result.txt（43项）。
    """
    res = calc.result
    p5  = calc.points[4]
    p8  = calc.points[799]

    rows = [
        (1,  "P5的X坐标值",                    f"{p5.x:.3f}"),
        (2,  "P5的Y坐标值",                    f"{p5.y:.3f}"),
        (3,  "P5的Z坐标值",                    f"{p5.z:.3f}"),
        (4,  "全部点X坐标最小值",              f"{res.xmin:.3f}"),
        (5,  "全部点X坐标最大值",              f"{res.xmax:.3f}"),
        (6,  "全部点Y坐标最小值",              f"{res.ymin:.3f}"),
        (7,  "全部点Y坐标最大值",              f"{res.ymax:.3f}"),
        (8,  "全部点Z坐标最小值",              f"{res.zmin:.3f}"),
        (9,  "全部点Z坐标最大值",              f"{res.zmax:.3f}"),
        (10, "P5所在栅格行号i",               str(res.grid_i)),
        (11, "P5所在栅格列号j",               str(res.grid_j)),
        (12, "P5所在栅格内总测点数",          str(res.grid_count)),
        (13, "P5所在栅格高程平均值",          f"{res.grid_mean:.3f}"),
        (14, "P5所在栅格高程最大值",          f"{res.grid_max:.3f}"),
        (15, "P5所在栅格高程高差",            f"{res.grid_range:.3f}"),
        (16, "P5所在栅格高程方差",            f"{res.grid_var:.3f}"),
        (17, "三点P1P2P3围成三角形面积",       f"{res.triangle_area:.6f}"),
        (18, "RANSAC拟合平面S1参数A",          f"{res.s1_A:.6f}"),
        (19, "RANSAC拟合平面S1参数B",          f"{res.s1_B:.6f}"),
        (20, "RANSAC拟合平面S1参数C",          f"{res.s1_C:.6f}"),
        (21, "RANSAC拟合平面S1参数D",          f"{res.s1_D:.6f}"),
        (22, "测点P1000到平面S1垂直距离",       f"{res.dist_p1000_s1:.3f}"),
        (23, "测点P5到平面S1垂直距离",         f"{res.dist_p5_s1:.3f}"),
        (24, "拟合平面S1内点数量",             str(res.s1_inlier_count)),
        (25, "拟合平面S1粗差点数量",           str(res.s1_outlier_count)),
        (26, "最优分割平面J1参数A",            f"{res.j1_A:.6f}"),
        (27, "最优分割平面J1参数B",            f"{res.j1_B:.6f}"),
        (28, "最优分割平面J1参数C",            f"{res.j1_C:.6f}"),
        (29, "最优分割平面J1参数D",            f"{res.j1_D:.9f}"),
        (30, "分割平面J1内点数量",             str(res.j1_inlier_count)),
        (31, "分割平面J1粗差点数量",           str(res.j1_outlier_count)),
        (32, "分割平面J2参数A",                f"{res.j2_A:.6f}"),
        (33, "分割平面J2参数B",                f"{res.j2_B:.6f}"),
        (34, "分割平面J2参数C",                f"{res.j2_C:.6f}"),
        (35, "分割平面J2参数D",                f"{res.j2_D:.9f}"),
        (36, "分割平面J2内点数量",             str(res.j2_inlier_count)),
        (37, "分割平面J2粗差点数量",           str(res.j2_outlier_count)),
        (38, "P5在平面J1投影X坐标xi",          f"{res.proj_p5_x:.3f}"),
        (39, "P5在平面J1投影Y坐标yi",          f"{res.proj_p5_y:.3f}"),
        (40, "P5在平面J1投影Z坐标zi",          f"{res.proj_p5_z:.2f}"),
        (41, "P800在平面J1投影X坐标xi",        f"{res.proj_p800_x:.3f}"),
        (42, "P800在平面J1投影Y坐标yi",        f"{res.proj_p800_y:.3f}"),
        (43, "P800在平面J1投影Z坐标zi",        f"{res.proj_p800_z:.3f}"),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,指标名称,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
