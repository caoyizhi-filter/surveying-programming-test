# ============================================================
# 导入模块
# ============================================================
import math
import random
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTableWidgetItem,
                              QHeaderView, QAction, QStatusBar, QSplitter,
                              QGroupBox, QVBoxLayout, QTableWidget, QLabel)
from PyQt5.QtCore import Qt


# ============================================================
# 第一部分：底层向量基础运算（4个函数，纯 Python 无第三方依赖）
# ============================================================
# 说明：这些函数是三维向量运算工具，与具体题目完全无关。
#       换任何一道涉及三维点的竞赛题，这部分都不需要修改。
# ============================================================

def vec_sub(a, b):
    """向量减法 a-b，逐分量相减。数学作用：计算两点之间的方向向量"""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_cross(a, b):
    """向量叉积 a×b。数学作用：由平面上两个方向向量求法向量 (A,B,C)"""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vec_norm(v):
    """向量模长 |v| = sqrt(x²+y²+z²)。数学作用：计算距离、面积时的分母"""
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def vec_dot(a, b):
    """向量点积 a·b = ax*bx + ay*by + az*bz。数学作用：投影计算"""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


# ============================================================
# 第二部分：平面几何核心函数（4个函数）
# ============================================================
# 说明：由三点构建平面、点到平面距离、点投影到平面、三角形面积。
#       这四个函数是 RANSAC 平面估计的几何基础。
#       公式全部来自试题册，换题无需修改。
# ============================================================

def build_plane(p1, p2, p3):
    """
    三点确定平面 Ax + By + Cz + D = 0
    法向量 (A,B,C) = (P2-P1) × (P3-P1)
    D = -(A*x1 + B*y1 + C*z1)
    参数：p1, p2, p3 均为 (x, y, z) 元组
    返回：(A, B, C, D) 非归一化平面参数
    """
    v1 = vec_sub(p2, p1)
    v2 = vec_sub(p3, p1)
    A, B, C = vec_cross(v1, v2)
    D = -(A * p1[0] + B * p1[1] + C * p1[2])
    return (A, B, C, D)


def point_to_plane_dist(pt, A, B, C, D):
    """
    点到平面垂直距离：d = |Ax+By+Cz+D| / sqrt(A²+B²+C²)
    参数：pt = (x, y, z) 元组
    返回：非负浮点数（距离）
    """
    num = A * pt[0] + B * pt[1] + C * pt[2] + D
    den = math.sqrt(A * A + B * B + C * C)
    return abs(num) / den if den > 1e-14 else 0.0


def project_to_plane(pt, A, B, C, D):
    """
    点投影到平面：P' = P - t*(A,B,C)，其中 t = (Ax+By+Cz+D)/(A²+B²+C²)
    参数：pt = (x, y, z) 元组
    返回：(x', y', z') 投影点坐标
    """
    n2 = A * A + B * B + C * C
    if n2 < 1e-14:
        return pt
    t = (A * pt[0] + B * pt[1] + C * pt[2] + D) / n2
    return (pt[0] - A * t, pt[1] - B * t, pt[2] - C * t)


def triangle_area(p1, p2, p3):
    """
    空间三角形面积：S = 0.5 × |(P2-P1) × (P3-P1)|
    参数：p1, p2, p3 均为 (x, y, z) 元组
    返回：面积浮点数
    """
    v1 = vec_sub(p2, p1)
    v2 = vec_sub(p3, p1)
    return 0.5 * vec_norm(vec_cross(v1, v2))


# ============================================================
# 第三部分：栅格统计（3个函数）
# ============================================================
# 说明：将点云划分到10×10栅格，统计 P5 所在栅格的高程信息。
#       这部分是试题考核项第10-16项的数据来源，换题无需修改。
# ============================================================

def build_grid(pts_xyz, xmin, xmax, ymin, ymax, nx=10, ny=10):
    """
    构建二维栅格索引
    返回：{(i,j): [z值列表], ...}, dx, dy
    栅格划分公式：i = floor((x - xmin) / dx)，j = floor((y - ymin) / dy)
    """
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    grid = {}
    for idx, (x, y, z) in enumerate(pts_xyz):
        i = int((x - xmin) / dx)
        j = int((y - ymin) / dy)
        i = max(0, min(i, nx - 1))
        j = max(0, min(j, ny - 1))
        grid.setdefault((i, j), []).append((idx, z))
    return grid, dx, dy


def grid_cell_of(x, y, xmin, ymin, dx, dy, nx, ny):
    """计算点 (x,y) 所在的栅格行列号"""
    i = int((x - xmin) / dx)
    j = int((y - ymin) / dy)
    return max(0, min(i, nx - 1)), max(0, min(j, ny - 1))


def grid_stats(z_list):
    """
    栅格统计：点数、均值、最大值、高差(极差)、方差
    返回：(count, mean, max_z, range_z, var)
    """
    if not z_list:
        return 0, 0.0, 0.0, 0.0, 0.0
    n = len(z_list)
    mean = sum(z_list) / n
    max_z = max(z_list)
    min_z = min(z_list)
    rng = max_z - min_z
    var = sum((v - mean) ** 2 for v in z_list) / n
    return n, mean, max_z, rng, var


# ============================================================
# 第四部分：最小二乘平面拟合（直接公式法）
# ============================================================
# 说明：对一组三维点，用协方差矩阵法直接求解最优平面。
#       原理：协方差矩阵 C 的最小特征值对应特征向量 = 最优法向量。
#       对于3×3矩阵，利用伴随矩阵公式直接求解，无需迭代。
#       换任何一道需要最小二乘平面拟合的题，这部分无需修改。
# ============================================================

def ls_plane_fit(pts_xyz):
    """
    最小二乘平面拟合（直接公式法）
    参数：pts_xyz = [(x,y,z), ...] 点坐标列表
    返回：(A, B, C, D) 平面参数，满足 Ax + By + Cz + D = 0
    原理：协方差矩阵最小特征值对应特征向量 = 最优法向量
    """
    n = len(pts_xyz)
    if n < 3:
        return (0.0, 0.0, 1.0, 0.0)

    # 1) 计算质心
    mx = sum(p[0] for p in pts_xyz) / n
    my = sum(p[1] for p in pts_xyz) / n
    mz = sum(p[2] for p in pts_xyz) / n

    # 2) 构建 3×3 协方差矩阵（实对称）
    cxx = cxy = cxz = cyy = cyz = czz = 0.0
    for x, y, z in pts_xyz:
        dx, dy, dz = x - mx, y - my, z - mz
        cxx += dx * dx
        cxy += dx * dy
        cxz += dx * dz
        cyy += dy * dy
        cyz += dy * dz
        czz += dz * dz

    # 3) 计算协方差矩阵的伴随矩阵元素
    # 伴随矩阵 adj(C) 的每个元素 = 对应代数余子式
    # 最小特征值对应的特征向量 ≈ 伴随矩阵的最小行/列
    # 这里用矩阵求逆法的简化形式：inv(C) = adj(C) / det(C)
    adj_00 = cyy * czz - cyz * cyz
    adj_11 = cxx * czz - cxz * cxz
    adj_22 = cxx * cyy - cxy * cxy
    adj_01 = cxz * cyz - cxy * czz
    adj_02 = cxy * cyz - cxz * cyy
    adj_12 = cxz * cxy - cxx * cyz

    # 4) 选择范数最大的行作为法向量（数值稳定性更好）
    # 计算各行列的范数
    row0_n2 = adj_00*adj_00 + adj_01*adj_01 + adj_02*adj_02
    row1_n2 = adj_01*adj_01 + adj_11*adj_11 + adj_12*adj_12
    row2_n2 = adj_02*adj_02 + adj_12*adj_12 + adj_22*adj_22

    # 选择范数最大的行作为法向量
    if row0_n2 >= row1_n2 and row0_n2 >= row2_n2:
        A, B, C = adj_00, adj_01, adj_02
    elif row1_n2 >= row0_n2 and row1_n2 >= row2_n2:
        A, B, C = adj_01, adj_11, adj_12
    else:
        A, B, C = adj_02, adj_12, adj_22

    # 5) 归一化法向量
    norm = math.sqrt(A*A + B*B + C*C)
    if norm < 1e-14:
        return (0.0, 0.0, 1.0, 0.0)
    A /= norm
    B /= norm
    C /= norm

    # 6) 计算 D = -(A*mx + B*my + C*mz)
    D = -(A * mx + B * my + C * mz)
    return (A, B, C, D)


# ============================================================
# 第五部分：文件读取函数
# ============================================================
# 【竞赛题切换点】如果新题目的数据文件格式不同（分隔符、列含义等），
#                修改此函数的解析逻辑。当前格式：
#                  plane_cloud.txt : 点号,x,y,z（4列，首行可为 # 注释）
# ============================================================

def read_plane_cloud(filepath):
    """
    读取点云数据文件
    当前格式：每行 "P1,x,y,z" 或 "x,y,z"（逗号分隔）
    首行若以 # 开头视为注释跳过
    返回：[(x, y, z), ...] 点坐标列表（保持原始顺序）
    【竞赛题切换点】如果列数或分隔符变化，修改 split 和字段索引
    """
    pts = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) == 4:
                # 格式：点号, x, y, z
                try:
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    z = float(parts[3].strip())
                except ValueError:
                    continue
            elif len(parts) == 3:
                # 格式：x, y, z（兼容无点号）
                try:
                    x = float(parts[0].strip())
                    y = float(parts[1].strip())
                    z = float(parts[2].strip())
                except ValueError:
                    continue
            else:
                continue
            pts.append((x, y, z))
    if not pts:
        raise Exception("文件为空或格式错误，支持 P1,x,y,z 或 x,y,z 两种格式")
    return pts


# ============================================================
# 第六部分：RANSAC 稳健平面估计主流程
# ============================================================
# 说明：完整的 RANSAC 平面估计 + 最小二乘分割平面 + 43项统计输出。
#       无 GUI 可直接调用 run_all()，返回 table_rows 供 GUI 渲染。
#
# 【竞赛题切换点】换一道题目时，重写这个函数。保持返回 dict 格式不变：
#   {"table_rows": [(序号, 指标名, 值), ...], "config": {...}}
#   table_rows 和 config 格式是 GUI 的唯一数据契约，格式不变则 GUI 零改动。
# ============================================================

# 固定参数（试题册规定）
RANSAC_T = 0.25          # 归一化距离阈值（m）
RANSAC_K_MAX = 2000      # 最大迭代次数
RANSAC_SEED = 42         # 固定随机种子，保证结果可重复
GRID_NX = 10             # 栅格列数
GRID_NY = 10             # 栅格行数


def run_all(input_path="plane_cloud.txt", output_path="plane_analysis_result.txt"):
    """
    ===== 基于RANSAC算法的稳健平面参数估计主流程 =====
    【竞赛题切换点】换题时重写此函数，保持返回格式不变。
    """

    # ===== 步骤1：读取数据 =====
    pts_xyz = read_plane_cloud(input_path)
    n = len(pts_xyz)
    if n < 3:
        raise Exception("点云数量不足（至少需要3个点）")

    rng = random.Random(RANSAC_SEED)

    # ===== 步骤2：全局坐标统计 =====
    xs = [p[0] for p in pts_xyz]
    ys = [p[1] for p in pts_xyz]
    zs = [p[2] for p in pts_xyz]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    zmin, zmax = min(zs), max(zs)

    # ===== 步骤3：三角形面积 P1-P2-P3 =====
    tri_area = triangle_area(pts_xyz[0], pts_xyz[1], pts_xyz[2])

    # ===== 步骤4：P5 所在栅格统计 =====
    grid, dx, dy = build_grid(pts_xyz, xmin, xmax, ymin, ymax, GRID_NX, GRID_NY)
    p5 = pts_xyz[4]  # P5 = 索引4
    gi, gj = grid_cell_of(p5[0], p5[1], xmin, ymin, dx, dy, GRID_NX, GRID_NY)
    cell_entries = grid.get((gi, gj), [])
    # 排除 P5 自身（索引4）
    cell_zs = [z for idx, z in cell_entries if idx != 4]
    g_cnt, g_mean, g_max, g_rng, g_var = grid_stats(cell_zs)

    # ===== 步骤5：RANSAC 迭代 =====
    best_inlier_count = -1
    best_A = best_B = best_C = best_D = 0.0
    best_inlier_indices = []
    best_iter = 0

    for k in range(1, RANSAC_K_MAX + 1):
        # 随机抽取3个不同点
        s = rng.sample(range(n), 3)
        p1, p2, p3 = pts_xyz[s[0]], pts_xyz[s[1]], pts_xyz[s[2]]

        # 三点共线或面积过小 → 跳过（无法确定平面）
        if triangle_area(p1, p2, p3) < 1e-12:
            continue

        A, B, C, D = build_plane(p1, p2, p3)

        # 统计内点
        inlier_ids = []
        for i, pt in enumerate(pts_xyz):
            d = point_to_plane_dist(pt, A, B, C, D)
            if d <= RANSAC_T:
                inlier_ids.append(i)

        cnt = len(inlier_ids)
        if cnt > best_inlier_count:
            best_inlier_count = cnt
            best_A, best_B, best_C, best_D = A, B, C, D
            best_inlier_indices = inlier_ids
            best_iter = k

    # ===== 步骤6：S1 平面结果整理 =====
    s1_A, s1_B, s1_C, s1_D = best_A, best_B, best_C, best_D
    s1_inlier_count = best_inlier_count
    s1_outlier_count = n - best_inlier_count

    inlier_set = set(best_inlier_indices)
    s1_inlier_pts = [pts_xyz[i] for i in range(n) if i in inlier_set]
    s1_outlier_pts = [pts_xyz[i] for i in range(n) if i not in inlier_set]

    # 距离考核项
    dist_p5_s1 = point_to_plane_dist(pts_xyz[4], s1_A, s1_B, s1_C, s1_D)
    dist_p1000_s1 = point_to_plane_dist(pts_xyz[999], s1_A, s1_B, s1_C, s1_D)

    # ===== 步骤7：最小二乘分割平面 J1 / J2 =====
    # J1 = 对内点集合做最小二乘平面拟合
    # J2 = 对粗差点集合做最小二乘平面拟合
    j1_A, j1_B, j1_C, j1_D = ls_plane_fit(s1_inlier_pts)
    j2_A, j2_B, j2_C, j2_D = ls_plane_fit(s1_outlier_pts)

    # J1 内外点统计（全点，用 J1 参数重新判定）
    j1_in = sum(1 for pt in pts_xyz
                if point_to_plane_dist(pt, j1_A, j1_B, j1_C, j1_D) <= RANSAC_T)
    j1_inlier_count = j1_in
    j1_outlier_count = n - j1_in

    # J2 内外点统计（全点，用 J2 参数重新判定）
    j2_in = sum(1 for pt in pts_xyz
                if point_to_plane_dist(pt, j2_A, j2_B, j2_C, j2_D) <= RANSAC_T)
    j2_inlier_count = j2_in
    j2_outlier_count = n - j2_in

    # ===== 步骤8：投影坐标 =====
    proj_p5 = project_to_plane(pts_xyz[4], j1_A, j1_B, j1_C, j1_D)
    proj_p800 = project_to_plane(pts_xyz[799], j1_A, j1_B, j1_C, j1_D)

    # ===== 步骤9：组装 43 项输出 =====
    # 【竞赛题切换点】table_rows 定义了 GUI 表格中显示的每一行。
    #   格式：(序号, 指标名称, 计算结果字符串)
    #   换题时按新题目的需求增删改 item，但保持三元组格式不变。
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
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("序号,指标名称,计算结果\n")
        for no, label, val in table_rows:
            f.write(f"{no},{label},{val}\n")

    # ===== 步骤10：构建 GUI 配置（【竞赛题切换点】）=====
    # 所有题目相关的界面配置都在这里，换题只需修改本部分
    gui_config = {
        "window_title": "基于RANSAC算法的稳健平面参数估计系统",
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
        "total_pts": n,
        "s1_inlier_count": s1_inlier_count,
        "s1_outlier_count": s1_outlier_count,
        "j1_inlier_count": j1_inlier_count,
        "j2_inlier_count": j2_inlier_count,
        "tri_area": tri_area,
        "best_iter": best_iter,
        # 附带完整数据供状态栏等使用
        "pts_xyz": pts_xyz,
        "inlier_indices": best_inlier_indices,
        "s1": (s1_A, s1_B, s1_C, s1_D),
        "j1": (j1_A, j1_B, j1_C, j1_D),
        "j2": (j2_A, j2_B, j2_C, j2_D),
        "proj_p5": proj_p5,
        "proj_p800": proj_p800,
    }


# ============================================================
# 第七部分：GUI 界面（零改动模板）
# ============================================================
# 设计原则：
#   1. GUI 完全不接触计算逻辑，只调用 run_all() 获取 table_rows 和 config
#   2. 文件选择器由 FILE_CONFIG 驱动，增删文件类型只需改配置列表
#   3. 结果表格完全数据驱动，table_rows 有多少行就显示多少行
#   4. 界面配置（窗口标题、状态栏等）由 run_all() 返回的 config 提供
#
# 【零改动】本部分代码在换竞赛题时无需修改任何一行。
# ============================================================

# 文件配置（零改动：由 run_all() 返回的 config 驱动）
FILE_CONFIG = [
    ("cloud", "点云数据", "plane_cloud.txt"),
]


class App(QMainWindow):
    """通用竞赛程序主窗口（零改动）"""

    def __init__(self):
        super().__init__()
        # 窗口标题由 run_all() 返回的 config 设置
        self.setWindowTitle("竞赛程序系统")
        self.resize(1100, 720)

        # 根据 FILE_CONFIG 初始化文件路径字典
        self._paths = {key: default for key, _, default in FILE_CONFIG}
        # 存放 run_all() 的返回结果
        self._result = None
        self._table_rows = None
        self._config = None

        # 搭建界面五大组件
        self._setup_actions()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central()
        self.setStatusBar(QStatusBar())

    # ==================== 界面搭建 ====================

    def _setup_actions(self):
        """创建所有动作对象并绑定信号-槽（通用）"""
        a = self
        self._file_acts = {}
        for key, label, _ in FILE_CONFIG:
            act = QAction(label, a)
            act.triggered.connect(lambda checked, k=key: self._open(k))
            self._file_acts[key] = act

        a.actCalc = QAction("计算", a)
        a.actCalc.triggered.connect(self._calc)
        a.actSave = QAction("导出", a)
        a.actSave.triggered.connect(self._save)
        a.actClear = QAction("清空", a)
        a.actClear.triggered.connect(self._clear)
        a.actExit = QAction("退出", a)
        a.actExit.triggered.connect(self.close)

    def _setup_menubar(self):
        """菜单栏：文件(&F) + 计算(&C)（通用）"""
        mb = self.menuBar()
        a = self
        menuF = mb.addMenu("文件(&F)")
        for key, label, _ in FILE_CONFIG:
            menuF.addAction(self._file_acts[key])
        menuF.addSeparator()
        menuF.addAction(a.actSave)
        menuF.addSeparator()
        menuF.addAction(a.actClear)
        menuF.addSeparator()
        menuF.addAction(a.actExit)
        mb.addMenu("计算(&C)").addAction(a.actCalc)

    def _setup_toolbar(self):
        """工具栏（通用）"""
        tb = self.addToolBar("工具栏")
        a = self
        for key, label, _ in FILE_CONFIG:
            tb.addAction(self._file_acts[key])
        tb.addSeparator()
        tb.addAction(a.actCalc)
        tb.addSeparator()
        tb.addAction(a.actSave)
        tb.addAction(a.actClear)

    def _setup_central(self):
        """中央区域：左侧文件状态面板 + 右侧结果表格"""
        # ---- 左侧面板 ----
        self.labelFile = QLabel("未加载数据")
        gb = QGroupBox("输入参数")
        gb.setMinimumSize(220, 0)
        lay = QVBoxLayout(gb)
        lay.addWidget(self.labelFile)

        # ---- 右侧表格 ----
        self.tableResult = QTableWidget()
        self.tableResult.setColumnCount(3)
        self.tableResult.setHorizontalHeaderLabels(["序号", "指标", "计算结果"])
        h = self.tableResult.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # ---- 分割器 ----
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(gb)
        splitter.addWidget(self.tableResult)
        self.setCentralWidget(splitter)

    # ==================== 槽函数 ====================

    def _open(self, kind):
        """通用文件打开对话框（零改动）"""
        path, _ = QFileDialog.getOpenFileName(self, "", "", "文本文件 (*.txt);;所有文件 (*)")
        if not path:
            return
        self._paths[kind] = path
        lines = []
        for key, label, _ in FILE_CONFIG:
            filename = self._paths[key].split("/")[-1].split("\\")[-1]
            lines.append(f"{label}: {filename}")
        self.labelFile.setText("\n".join(lines))

    def _calc(self):
        """执行计算并刷新表格（零改动）"""
        # 调用 run_all()，获取 table_rows 和 config
        r = run_all(self._paths["cloud"], "result.txt")
        self._result = r
        self._table_rows = r["table_rows"]
        self._config = r.get("config", {})

        # 设置窗口标题（从 config 获取）
        title = self._config.get("window_title", "竞赛程序系统")
        self.setWindowTitle(title)

        # 通用表格渲染 —— run_all 返回什么就显示什么（零改动）
        t = self.tableResult
        t.setRowCount(len(self._table_rows))
        for i, (no, lb, val) in enumerate(self._table_rows):
            for j, text in enumerate([str(no), lb, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                t.setItem(i, j, item)

        # 设置状态栏消息（从 config 获取）
        msg = self._config.get("status_message", "计算完成")
        self.statusBar().showMessage(msg)

    def _save(self):
        """导出结果为 CSV 文件（零改动）"""
        if not self._table_rows:
            return
        default_name = self._config.get("output_file", "result.txt") if self._config else "result.txt"
        path, _ = QFileDialog.getSaveFileName(self, "", default_name, "文本文件 (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("序号,指标名称,计算结果\n")
            for no, lb, val in self._table_rows:
                f.write(f"{no},{lb},{val}\n")

    def _clear(self):
        """清空所有状态，恢复到初始界面（零改动）"""
        self._paths = {key: default for key, _, default in FILE_CONFIG}
        self._result = None
        self._table_rows = None
        self._config = None
        self.tableResult.setRowCount(0)
        self.labelFile.setText("未加载数据")
        self.setWindowTitle("竞赛程序系统")


# ============================================================
# 程序入口（两套入口，使用时只保留一套，注释掉另一套）
# ============================================================

# --- 入口A：纯计算模式（无GUI，直接运行出结果）---
# if __name__ == "__main__":
#     r = run_all()
#     print("计算完成，结果已写入 plane_analysis_result.txt")
#     print(f"总点数={r['total_pts']}  S1内点={r['s1_inlier_count']}  S1粗差={r['s1_outlier_count']}")
#     print(f"J1内点={r['j1_inlier_count']}  J2内点={r['j2_inlier_count']}")

# --- 入口B：GUI界面模式（需要PyQt5）---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
