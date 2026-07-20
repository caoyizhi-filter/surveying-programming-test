# calculator.py
# 基于RANSAC算法的稳健平面参数估计
# 仅使用 Python 标准库 math / random

import math
import random


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class Point3D:
    def __init__(self, idx, x, y, z):
        self.idx = idx           # 1 起始编号
        self.x   = x
        self.y   = y
        self.z   = z
        self.dist_to_best = 0.0  # 到最优平面的距离
        self.is_inlier    = True # True=内点 False=粗差


class RANSACResult:
    def __init__(self):
        # ── 基本统计 ──
        self.total_pts       = 0
        self.best_iter       = 0

        # ── 全局坐标范围 ──
        self.xmin = 0.0; self.xmax = 0.0
        self.ymin = 0.0; self.ymax = 0.0
        self.zmin = 0.0; self.zmax = 0.0

        # ── 栅格统计 ──
        self.grid_i     = 0
        self.grid_j     = 0
        self.grid_count = 0
        self.grid_mean  = 0.0
        self.grid_max   = 0.0
        self.grid_range = 0.0
        self.grid_var   = 0.0

        # ── 三角形面积 ──
        self.triangle_area = 0.0

        # ── S1 平面参数（非归一化） ──
        self.s1_A = 0.0; self.s1_B = 0.0
        self.s1_C = 0.0; self.s1_D = 0.0

        # ── S1 内外点 ──
        self.s1_inlier_count  = 0
        self.s1_outlier_count = 0
        self.s1_inlier_pts  : list = []
        self.s1_outlier_pts : list = []

        # ── 距离 ──
        self.dist_p5_s1    = 0.0
        self.dist_p1000_s1 = 0.0

        # ── J1 分割平面参数（非归一化） ──
        self.j1_A = 0.0; self.j1_B = 0.0
        self.j1_C = 0.0; self.j1_D = 0.0
        self.j1_inlier_count  = 0
        self.j1_outlier_count = 0

        # ── J2 分割平面参数（非归一化） ──
        self.j2_A = 0.0; self.j2_B = 0.0
        self.j2_C = 0.0; self.j2_D = 0.0
        self.j2_inlier_count  = 0
        self.j2_outlier_count = 0

        # ── 投影坐标 ──
        self.proj_p5_x = 0.0; self.proj_p5_y = 0.0; self.proj_p5_z = 0.0
        self.proj_p800_x = 0.0; self.proj_p800_y = 0.0; self.proj_p800_z = 0.0


# ══════════════════════════════════════════════════════════════
#  向量工具（纯标准库，禁止 numpy）
# ══════════════════════════════════════════════════════════════

def _vec_sub(a, b):
    """a - b，均为 (x,y,z) 元组"""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vec_cross(a, b):
    """向量叉积 a × b"""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _vec_norm(v):
    """向量模长"""
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _vec_dot(a, b):
    """向量点积"""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


# ══════════════════════════════════════════════════════════════
#  由三点构建平面（试题册公式：叉积求法向量）
# ══════════════════════════════════════════════════════════════

def build_plane(p1: Point3D, p2: Point3D, p3: Point3D):
    """
    三点确定平面 Ax + By + Cz + D = 0（非归一化参数）。
    返回 (A, B, C, D)
    """
    v1 = _vec_sub((p2.x, p2.y, p2.z), (p1.x, p1.y, p1.z))
    v2 = _vec_sub((p3.x, p3.y, p3.z), (p1.x, p1.y, p1.z))
    A, B, C = _vec_cross(v1, v2)
    D = -(A * p1.x + B * p1.y + C * p1.z)
    return (A, B, C, D)


# ══════════════════════════════════════════════════════════════
#  点到平面垂直距离（试题册公式）
# ══════════════════════════════════════════════════════════════

def point_to_plane_dist(pi: Point3D, A, B, C, D) -> float:
    """
    d = |Ax + By + Cz + D| / sqrt(A² + B² + C²)
    """
    num = A * pi.x + B * pi.y + C * pi.z + D
    den = math.sqrt(A * A + B * B + C * C)
    return abs(num) / den if den > 1e-14 else 0.0


# ══════════════════════════════════════════════════════════════
#  点投影到平面（试题册公式）
# ══════════════════════════════════════════════════════════════

def project_to_plane(pi: Point3D, A, B, C, D):
    """
    P' = P - (Ax+By+Cz+D) / (A²+B²+C²) · (A, B, C)
    返回 (x', y', z')
    """
    n2 = A * A + B * B + C * C
    if n2 < 1e-14:
        return (pi.x, pi.y, pi.z)
    t = (A * pi.x + B * pi.y + C * pi.z + D) / n2
    return (pi.x - A * t, pi.y - B * t, pi.z - C * t)


# ══════════════════════════════════════════════════════════════
#  三角形面积
# ══════════════════════════════════════════════════════════════

def triangle_area(p1: Point3D, p2: Point3D, p3: Point3D) -> float:
    """空间三角形面积 = 0.5 × |(P2-P1) × (P3-P1)|"""
    v1 = _vec_sub((p2.x, p2.y, p2.z), (p1.x, p1.y, p1.z))
    v2 = _vec_sub((p3.x, p3.y, p3.z), (p1.x, p1.y, p1.z))
    return 0.5 * _vec_norm(_vec_cross(v1, v2))


# ══════════════════════════════════════════════════════════════
#  最小二乘平面拟合（协方差特征向量法，返回非归一化参数）
# ══════════════════════════════════════════════════════════════

def _ls_plane_raw(inlier_pts, outlier_pts):
    """
    分别对两组点做最小二乘平面拟合。
    使用协方差矩阵 Jacobi 特征分解。
    返回 (j1_A,j1_B,j1_C,j1_D, j2_A,j2_B,j2_C,j2_D)
    """

    def _fit_one(pts):
        n = len(pts)
        if n < 3:
            return (0.0, 0.0, 1.0, 0.0)

        mx = sum(p.x for p in pts) / n
        my = sum(p.y for p in pts) / n
        mz = sum(p.z for p in pts) / n

        cxx = cxy = cxz = cyy = cyz = czz = 0.0
        for p in pts:
            dx, dy, dz = p.x - mx, p.y - my, p.z - mz
            cxx += dx * dx
            cxy += dx * dy
            cxz += dx * dz
            cyy += dy * dy
            cyz += dy * dz
            czz += dz * dz

        # Jacobi 对角化
        M = [[cxx, cxy, cxz],
             [cxy, cyy, cyz],
             [cxz, cyz, czz]]
        Q = [[1.0, 0.0, 0.0],
             [0.0, 1.0, 0.0],
             [0.0, 0.0, 1.0]]

        eps = 1e-14
        for _ in range(200):
            off = [(abs(M[0][1]), 0, 1),
                   (abs(M[0][2]), 0, 2),
                   (abs(M[1][2]), 1, 2)]
            max_off, p_idx, q_idx = max(off, key=lambda x: x[0])
            if max_off < eps:
                break

            Mpp, Mqq, Mpq = M[p_idx][p_idx], M[q_idx][q_idx], M[p_idx][q_idx]
            diff = Mqq - Mpp
            if abs(Mpq) < eps:
                continue

            t = Mpq / (abs(diff) + math.sqrt(diff * diff + 4.0 * Mpq * Mpq))
            ct = 1.0 / math.sqrt(1.0 + t * t)
            st = t * ct

            new_pp = ct*ct*Mpp + st*st*Mqq - 2.0*st*ct*Mpq
            new_qq = st*st*Mpp + ct*ct*Mqq + 2.0*st*ct*Mpq

            for r in range(3):
                if r != p_idx and r != q_idx:
                    m_rp = ct * M[r][p_idx] - st * M[r][q_idx]
                    m_rq = st * M[r][p_idx] + ct * M[r][q_idx]
                    M[r][p_idx] = M[p_idx][r] = m_rp
                    M[r][q_idx] = M[q_idx][r] = m_rq

            M[p_idx][p_idx] = new_pp
            M[q_idx][q_idx] = new_qq
            M[p_idx][q_idx] = M[q_idx][p_idx] = 0.0

            for r in range(3):
                q_rp = ct * Q[r][p_idx] - st * Q[r][q_idx]
                q_rq = st * Q[r][p_idx] + ct * Q[r][q_idx]
                Q[r][p_idx] = q_rp
                Q[r][q_idx] = q_rq

        diag = [M[0][0], M[1][1], M[2][2]]
        idx_min = diag.index(min(diag))
        A, B, C = Q[0][idx_min], Q[1][idx_min], Q[2][idx_min]
        D = -(A * mx + B * my + C * mz)
        return (A, B, C, D)

    j1 = _fit_one(inlier_pts)
    j2 = _fit_one(outlier_pts)
    return j1 + j2


# ══════════════════════════════════════════════════════════════
#  栅格统计工具
# ══════════════════════════════════════════════════════════════

def _build_grid(pts, xmin, xmax, ymin, ymax, nx=10, ny=10):
    """返回 { (i,j): [(idx, z), ...] }, dx, dy"""
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    grid = {}
    for p in pts:
        i = int((p.x - xmin) / dx)
        j = int((p.y - ymin) / dy)
        i = max(0, min(i, nx - 1))
        j = max(0, min(j, ny - 1))
        grid.setdefault((i, j), []).append((p.idx, p.z))
    return grid, dx, dy


def _grid_cell_of(x, y, xmin, ymin, dx, dy, nx, ny):
    i = int((x - xmin) / dx)
    j = int((y - ymin) / dy)
    return max(0, min(i, nx - 1)), max(0, min(j, ny - 1))


def _grid_stats(z_list):
    if not z_list:
        return 0, 0.0, 0.0, 0.0, 0.0
    n = len(z_list)
    mean = sum(z_list) / n
    max_z = max(z_list)
    min_z = min(z_list)
    rng = max_z - min_z
    var = sum((v - mean) ** 2 for v in z_list) / n
    return n, mean, max_z, rng, var


# ══════════════════════════════════════════════════════════════
#  主 RANSAC 计算器
# ══════════════════════════════════════════════════════════════

class RANSACCalculator:

    # 固定参数（试题册规定）
    T        = 0.25    # 归一化距离阈值
    K_MAX    = 2000    # 最大迭代次数
    MIN_SAMP = 3       # 最小样本数
    SEED     = 42      # 固定随机种子保证可重复性
    GRID_NX  = 10      # 栅格列数
    GRID_NY  = 10      # 栅格行数

    def __init__(self):
        self.points : list = []    # list[Point3D]
        self.result  = RANSACResult()

    def compute(self):
        pts = self.points
        n   = len(pts)
        res = self.result
        res.total_pts = n

        if n < self.MIN_SAMP:
            return

        rng = random.Random(self.SEED)

        # ── 全局坐标统计 ──────────────────────────────────────
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        res.xmin = min(xs); res.xmax = max(xs)
        res.ymin = min(ys); res.ymax = max(ys)
        res.zmin = min(zs); res.zmax = max(zs)

        # ── 三角形面积 P1-P2-P3 ───────────────────────────────
        res.triangle_area = triangle_area(pts[0], pts[1], pts[2])

        # ── 栅格统计 ─────────────────────────────────────────
        grid, dx, dy = _build_grid(
            pts, res.xmin, res.xmax, res.ymin, res.ymax,
            self.GRID_NX, self.GRID_NY)
        p5 = pts[4]
        gi, gj = _grid_cell_of(
            p5.x, p5.y, res.xmin, res.ymin,
            dx, dy, self.GRID_NX, self.GRID_NY)
        cell_entries = grid.get((gi, gj), [])
        # 排除 P5 自身 (idx=5)
        cell_zs = [z for idx, z in cell_entries if idx != 5]
        cnt_g, mean_g, max_g, rng_g, var_g = _grid_stats(cell_zs)

        res.grid_i     = gi
        res.grid_j     = gj
        res.grid_count = cnt_g
        res.grid_mean  = mean_g
        res.grid_max   = max_g
        res.grid_range = rng_g
        res.grid_var   = var_g

        # ── RANSAC 迭代 ──────────────────────────────────────
        best_inlier_count = -1
        best_A = best_B = best_C = best_D = 0.0
        best_inlier_ids = []
        best_iter = 0

        for k in range(1, self.K_MAX + 1):
            sample = rng.sample(range(n), 3)
            p1, p2, p3 = pts[sample[0]], pts[sample[1]], pts[sample[2]]

            # 三点共线或面积过小则跳过
            if triangle_area(p1, p2, p3) < 1e-12:
                continue

            A, B, C, D = build_plane(p1, p2, p3)

            inlier_ids = []
            for p in pts:
                d = point_to_plane_dist(p, A, B, C, D)
                if d <= self.T:
                    inlier_ids.append(p.idx)

            cnt = len(inlier_ids)
            if cnt > best_inlier_count:
                best_inlier_count = cnt
                best_A, best_B, best_C, best_D = A, B, C, D
                best_inlier_ids = inlier_ids[:]
                best_iter = k

        # ── 保存 S1 结果 ─────────────────────────────────────
        res.s1_A = best_A; res.s1_B = best_B
        res.s1_C = best_C; res.s1_D = best_D
        res.best_iter = best_iter

        inlier_set = set(best_inlier_ids)
        res.s1_inlier_pts  = [p for p in pts if p.idx in inlier_set]
        res.s1_outlier_pts = [p for p in pts if p.idx not in inlier_set]
        res.s1_inlier_count  = len(res.s1_inlier_pts)
        res.s1_outlier_count = len(res.s1_outlier_pts)

        # 标记每个点的属性
        for p in pts:
            p.dist_to_best = point_to_plane_dist(
                p, best_A, best_B, best_C, best_D)
            p.is_inlier = p.idx in inlier_set

        # ── 距离考核项 ───────────────────────────────────────
        res.dist_p5_s1    = pts[4].dist_to_best
        res.dist_p1000_s1 = pts[999].dist_to_best

        # ── 分割平面 J1 / J2（最小二乘） ─────────────────────
        j1A, j1B, j1C, j1D, j2A, j2B, j2C, j2D = _ls_plane_raw(
            res.s1_inlier_pts, res.s1_outlier_pts)

        res.j1_A = j1A; res.j1_B = j1B
        res.j1_C = j1C; res.j1_D = j1D

        res.j2_A = j2A; res.j2_B = j2B
        res.j2_C = j2C; res.j2_D = j2D

        # J1 内外点（全点统计）
        j1_in = sum(1 for p in pts
                    if point_to_plane_dist(p, j1A, j1B, j1C, j1D) <= self.T)
        res.j1_inlier_count  = j1_in
        res.j1_outlier_count = n - j1_in

        # J2 内外点（全点统计）
        j2_in = sum(1 for p in pts
                    if point_to_plane_dist(p, j2A, j2B, j2C, j2D) <= self.T)
        res.j2_inlier_count  = j2_in
        res.j2_outlier_count = n - j2_in

        # ── 投影 ─────────────────────────────────────────────
        res.proj_p5_x, res.proj_p5_y, res.proj_p5_z = \
            project_to_plane(pts[4], j1A, j1B, j1C, j1D)
        res.proj_p800_x, res.proj_p800_y, res.proj_p800_z = \
            project_to_plane(pts[799], j1A, j1B, j1C, j1D)
