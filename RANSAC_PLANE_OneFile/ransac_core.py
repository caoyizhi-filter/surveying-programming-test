# ============================================================
# ransac_core.py —— 纯计算模块（无 GUI 依赖）
# ============================================================
# 数据契约：run_all() 返回 {"table_rows": [...], "config": {...}}
# GUI 只读这两个字段，换题时 GUI 文件零改动。
# ============================================================

import math
import random


# ---- 向量运算 ----

def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vec_norm(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


# ---- 平面几何 ----

def point_to_plane_dist(pt, A, B, C, D):
    num = A * pt[0] + B * pt[1] + C * pt[2] + D
    den = math.sqrt(A * A + B * B + C * C)
    return abs(num) / den if den > 1e-14 else 0.0


def project_to_plane(pt, A, B, C, D):
    n2 = A * A + B * B + C * C
    if n2 < 1e-14:
        return pt
    t = (A * pt[0] + B * pt[1] + C * pt[2] + D) / n2
    return (pt[0] - A * t, pt[1] - B * t, pt[2] - C * t)


def triangle_area(p1, p2, p3):
    v1 = vec_sub(p2, p1)
    v2 = vec_sub(p3, p1)
    return 0.5 * vec_norm(vec_cross(v1, v2))


# ---- 栅格统计 ----

def grid_cell_of(x, y, xmin, ymin, dx, dy, nx, ny):
    i = int((x - xmin) / dx)
    j = int((y - ymin) / dy)
    return max(0, min(i, nx - 1)), max(0, min(j, ny - 1))


def build_grid(pts_xyz, xmin, xmax, ymin, ymax, nx=10, ny=10):
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    grid = {}
    for idx, (x, y, z) in enumerate(pts_xyz):
        i, j = grid_cell_of(x, y, xmin, ymin, dx, dy, nx, ny)
        if (i, j) not in grid:
            grid[(i, j)] = []
        grid[(i, j)].append((idx, z))
    return grid, dx, dy


def grid_stats(z_list):
    if not z_list:
        return 0, 0.0, 0.0, 0.0, 0.0
    n = len(z_list)
    mean = sum(z_list) / n
    max_z = max(z_list)
    min_z = min(z_list)
    rng = max_z - min_z
    var = 0.0
    for v in z_list:
        var += (v - mean) ** 2
    var = var / n
    return n, mean, max_z, rng, var


# ---- 最小二乘平面拟合 ----

def ls_plane_fit(pts_xyz):
    n = len(pts_xyz)
    if n < 3:
        return (0.0, 0.0, 1.0, 0.0)

    # 简化质心计算
    mx = sum(p[0] for p in pts_xyz) / n
    my = sum(p[1] for p in pts_xyz) / n
    mz = sum(p[2] for p in pts_xyz) / n

    cxx = cxy = cxz = cyy = cyz = czz = 0.0
    for x, y, z in pts_xyz:
        dx, dy, dz = x - mx, y - my, z - mz
        cxx += dx * dx
        cxy += dx * dy
        cxz += dx * dz
        cyy += dy * dy
        cyz += dy * dz
        czz += dz * dz

    adj_00 = cyy * czz - cyz * cyz
    adj_11 = cxx * czz - cxz * cxz
    adj_22 = cxx * cyy - cxy * cxy
    adj_01 = cxz * cyz - cxy * czz
    adj_02 = cxy * cyz - cxz * cyy
    adj_12 = cxz * cxy - cxx * cyz

    row0_n2 = adj_00 * adj_00 + adj_01 * adj_01 + adj_02 * adj_02
    row1_n2 = adj_01 * adj_01 + adj_11 * adj_11 + adj_12 * adj_12
    row2_n2 = adj_02 * adj_02 + adj_12 * adj_12 + adj_22 * adj_22

    if row0_n2 >= row1_n2 and row0_n2 >= row2_n2:
        A, B, C = adj_00, adj_01, adj_02
    elif row1_n2 >= row0_n2 and row1_n2 >= row2_n2:
        A, B, C = adj_01, adj_11, adj_12
    else:
        A, B, C = adj_02, adj_12, adj_22

    norm = math.sqrt(A * A + B * B + C * C)
    if norm < 1e-14:
        return (0.0, 0.0, 1.0, 0.0)
    A /= norm
    B /= norm
    C /= norm
    D = -(A * mx + B * my + C * mz)
    return (A, B, C, D)


# ---- 文件读取（【竞赛题切换点】数据格式变化时改这里）----

def read_plane_cloud(filepath):
    pts = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) == 4:
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                except ValueError:
                    continue
            elif len(parts) == 3:
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2])
                except ValueError:
                    continue
            else:
                continue
            pts.append((x, y, z))
    if not pts:
        raise Exception("文件为空或格式错误")
    return pts


# ---- RANSAC 主流程 ----
# 【竞赛题切换点】换题时修改以下所有标记位置
#
# 切换清单（按修改顺序）：
#   1. 算法参数常量（RANSAC_T / K_MAX / SEED / GRID 等）
#   2. WINDOW_TITLE 窗口标题
#   3. read_plane_cloud()  数据文件解析格式
#   4. run_all() 主函数内部 —— 测点索引、table_rows 内容、gui_config 文案
#   5. run_all() 参数默认值（input_path / output_path）

RANSAC_T = 0.25          # 【竞赛题切换点】RANSAC 距离阈值
RANSAC_K_MAX = 2000      # 【竞赛题切换点】最大迭代次数
RANSAC_SEED = 42         # 【竞赛题切换点】随机种子（可改可不改）
GRID_NX = 10             # 【竞赛题切换点】栅格列数
GRID_NY = 10             # 【竞赛题切换点】栅格行数

# 【竞赛题切换点】窗口标题
WINDOW_TITLE = "基于RANSAC算法的稳健平面参数估计系统"


def run_all(input_path="plane_cloud.txt", output_path="plane_analysis_result.txt"):
    # 【竞赛题切换点】↑ 默认文件名和输出文件名

    # 1. 读取数据
    pts_xyz = read_plane_cloud(input_path)
    n = len(pts_xyz)
    if n < 3:
        raise Exception("点云数量不足（至少需要3个点）")

    rng = random.Random(RANSAC_SEED)

    # 2. 全局坐标统计
    xs = [p[0] for p in pts_xyz]
    ys = [p[1] for p in pts_xyz]
    zs = [p[2] for p in pts_xyz]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    zmin, zmax = min(zs), max(zs)

    # 3. 三角形面积 P1-P2-P3
    # 【竞赛题切换点】P1/P2/P3 的索引（此处为 0/1/2，即前三个点）
    tri_area = triangle_area(pts_xyz[0], pts_xyz[1], pts_xyz[2])

    # 4. P5 所在栅格统计
    # 【竞赛题切换点】P5 的索引（此处为 4）
    grid, dx, dy = build_grid(pts_xyz, xmin, xmax, ymin, ymax, GRID_NX, GRID_NY)
    p5 = pts_xyz[4]
    gi, gj = grid_cell_of(p5[0], p5[1], xmin, ymin, dx, dy, GRID_NX, GRID_NY)
    cell_entries = grid.get((gi, gj), [])
    # 【竞赛题切换点】排除 P5 自身的索引（此处为 4）
    cell_zs = [z for idx, z in cell_entries if idx != 4]
    g_cnt, g_mean, g_max, g_rng, g_var = grid_stats(cell_zs)

    # 5. RANSAC 迭代
    best_inlier_count = -1
    best_A = best_B = best_C = best_D = 0.0
    best_inlier_indices = []

    for k in range(1, RANSAC_K_MAX + 1):
        s = rng.sample(range(n), 3)
        p1, p2, p3 = pts_xyz[s[0]], pts_xyz[s[1]], pts_xyz[s[2]]

        v1 = vec_sub(p2, p1)
        v2 = vec_sub(p3, p1)
        A, B, C = vec_cross(v1, v2)
        if vec_norm((A, B, C)) < 1e-12:
            continue
        D = -(A * p1[0] + B * p1[1] + C * p1[2])
        inlier_ids = []
        for i, pt in enumerate(pts_xyz):
            if point_to_plane_dist(pt, A, B, C, D) <= RANSAC_T:
                inlier_ids.append(i)

        if len(inlier_ids) > best_inlier_count:
            best_inlier_count = len(inlier_ids)
            best_A, best_B, best_C, best_D = A, B, C, D
            best_inlier_indices = inlier_ids

    # 6. S1 平面结果整理
    s1_A, s1_B, s1_C, s1_D = best_A, best_B, best_C, best_D
    s1_inlier_count = best_inlier_count
    s1_outlier_count = n - best_inlier_count

    inlier_set = set(best_inlier_indices)
    # 简化内点/外点分类
    s1_inlier_pts = [pts_xyz[i] for i in range(n) if i in inlier_set]
    s1_outlier_pts = [pts_xyz[i] for i in range(n) if i not in inlier_set]

    # 【竞赛题切换点】P5=4, P1000=999
    dist_p5_s1 = point_to_plane_dist(pts_xyz[4], s1_A, s1_B, s1_C, s1_D)
    dist_p1000_s1 = point_to_plane_dist(pts_xyz[999], s1_A, s1_B, s1_C, s1_D)

    # 7. 最小二乘分割平面 J1 / J2
    j1_A, j1_B, j1_C, j1_D = ls_plane_fit(s1_inlier_pts)
    j2_A, j2_B, j2_C, j2_D = ls_plane_fit(s1_outlier_pts)

    # 简化内点计数
    j1_inlier_count = sum(1 for pt in pts_xyz
                          if point_to_plane_dist(pt, j1_A, j1_B, j1_C, j1_D) <= RANSAC_T)
    j1_outlier_count = n - j1_inlier_count

    j2_inlier_count = sum(1 for pt in pts_xyz
                          if point_to_plane_dist(pt, j2_A, j2_B, j2_C, j2_D) <= RANSAC_T)
    j2_outlier_count = n - j2_inlier_count

    # 8. 投影坐标
    # 【竞赛题切换点】P5=4, P800=799
    proj_p5 = project_to_plane(pts_xyz[4], j1_A, j1_B, j1_C, j1_D)
    proj_p800 = project_to_plane(pts_xyz[799], j1_A, j1_B, j1_C, j1_D)

    # 9. 组装输出
    # 【竞赛题切换点】按新题需求增删改以下全部 table_rows
    p5x, p5y, p5z = pts_xyz[4]
    table_rows = [
        (1,  "P5的X坐标值",                    f"{p5x:.3f}"),
        (2,  "P5的Y坐标值",                    f"{p5y:.3f}"),
        (3,  "P5的Z坐标值",                    f"{p5z:.3f}"),
        (4,  "全部点X坐标最小值",              f"{xmin:.3f}"),
        (5,  "全部点X坐标最大值",              f"{xmax:.3f}"),
        (6,  "全部点Y坐标最小值",              f"{ymin:.3f}"),
        (7,  "全部点Y坐标最大值",              f"{ymax:.3f}"),
        (8,  "全部点Z坐标最小值",              f"{zmin:.3f}"),
        (9,  "全部点Z坐标最大值",              f"{zmax:.3f}"),
        (10, "P5所在栅格行号i",                str(gi)),
        (11, "P5所在栅格列号j",                str(gj)),
        (12, "P5所在栅格内总测点数",           str(g_cnt)),
        (13, "P5所在栅格高程平均值",           f"{g_mean:.3f}"),
        (14, "P5所在栅格高程最大值",           f"{g_max:.3f}"),
        (15, "P5所在栅格高程高差",             f"{g_rng:.3f}"),
        (16, "P5所在栅格高程方差",             f"{g_var:.3f}"),
        (17, "三点P1P2P3围成三角形面积",       f"{tri_area:.6f}"),
        (18, "RANSAC拟合平面S1参数A",          f"{s1_A:.6f}"),
        (19, "RANSAC拟合平面S1参数B",          f"{s1_B:.6f}"),
        (20, "RANSAC拟合平面S1参数C",          f"{s1_C:.6f}"),
        (21, "RANSAC拟合平面S1参数D",          f"{s1_D:.6f}"),
        (22, "测点P1000到平面S1垂直距离",      f"{dist_p1000_s1:.3f}"),
        (23, "测点P5到平面S1垂直距离",         f"{dist_p5_s1:.3f}"),
        (24, "拟合平面S1内点数量",             str(s1_inlier_count)),
        (25, "拟合平面S1粗差点数量",           str(s1_outlier_count)),
        (26, "最优分割平面J1参数A",            f"{j1_A:.6f}"),
        (27, "最优分割平面J1参数B",            f"{j1_B:.6f}"),
        (28, "最优分割平面J1参数C",            f"{j1_C:.6f}"),
        (29, "最优分割平面J1参数D",            f"{j1_D:.9f}"),
        (30, "分割平面J1内点数量",             str(j1_inlier_count)),
        (31, "分割平面J1粗差点数量",           str(j1_outlier_count)),
        (32, "分割平面J2参数A",                f"{j2_A:.6f}"),
        (33, "分割平面J2参数B",                f"{j2_B:.6f}"),
        (34, "分割平面J2参数C",                f"{j2_C:.6f}"),
        (35, "分割平面J2参数D",                f"{j2_D:.9f}"),
        (36, "分割平面J2内点数量",             str(j2_inlier_count)),
        (37, "分割平面J2粗差点数量",           str(j2_outlier_count)),
        (38, "P5在平面J1投影X坐标xi",          f"{proj_p5[0]:.3f}"),
        (39, "P5在平面J1投影Y坐标yi",          f"{proj_p5[1]:.3f}"),
        (40, "P5在平面J1投影Z坐标zi",          f"{proj_p5[2]:.2f}"),
        (41, "P800在平面J1投影X坐标xi",        f"{proj_p800[0]:.3f}"),
        (42, "P800在平面J1投影Y坐标yi",        f"{proj_p800[1]:.3f}"),
        (43, "P800在平面J1投影Z坐标zi",        f"{proj_p800[2]:.3f}"),
    ]

    # 写结果文件
    # 【竞赛题切换点】CSV 表头按新题修改
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("序号,指标名称,计算结果\n")
        for no, label, val in table_rows:
            f.write(f"{no},{label},{val}\n")

    # 10. 构建 GUI 配置
    # 【竞赛题切换点】修改状态栏汇总信息和输出文件名
    gui_config = {
        "window_title": WINDOW_TITLE,
        "status_message": (
            f"完成 | 总点数={n} | "
            f"S1内点={s1_inlier_count} S1粗差={s1_outlier_count} | "
            f"J1内点={j1_inlier_count} J2内点={j2_inlier_count} | "
            f"三角面积={tri_area:.4f}"
        ),
        "output_file": output_path,
    }

    return {
        "table_rows": table_rows,
        "config": gui_config,
    }


# ============================================================
# 独立运行入口：python ransac_core.py 直接出结果文件
# ============================================================
if __name__ == "__main__":
    r = run_all()
    cfg = r["config"]
    print(f"计算完成，共 {len(r['table_rows'])} 项输出")
    print(cfg["status_message"])
