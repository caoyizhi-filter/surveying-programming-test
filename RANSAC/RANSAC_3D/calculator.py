# calculator.py
# 基于RANSAC算法的稳健三维直线参数估计
# 仅使用 Python 标准库 math / random

import math
import random


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class Point3D:
    def __init__(self, idx, x, y, z):
        self.idx = idx    # 1 起
        self.x   = x
        self.y   = y
        self.z   = z
        self.dist_to_best = 0.0   # 到最优直线距离
        self.is_inlier    = True  # True=内点 False=粗差


class RANSACResult:
    def __init__(self):
        # 最优直线参数
        self.x0 = 0.0; self.y0 = 0.0; self.z0 = 0.0
        self.ux = 0.0; self.uy = 0.0; self.uz = 0.0

        # 统计
        self.total_pts     = 0
        self.inlier_count  = 0
        self.outlier_count = 0
        self.inlier_pts    : list = []
        self.outlier_pts   : list = []
        self.best_iter     = 0    # 最优模型对应迭代轮次

        # 第一次抽样信息（用于考核项21/22）
        self.first_ux      = 0.0
        self.first_inlier_count = 0

        # 考核项 12/13
        self.dist_pt1 = 0.0
        self.dist_pt7 = 0.0

        # 内点统计
        self.inlier_x_mean = 0.0
        self.inlier_y_mean = 0.0
        self.inlier_z_mean = 0.0
        self.inlier_x_min  = 0.0
        self.inlier_z_max  = 0.0

        # 粗差统计
        self.outlier_ids   = ""   # 编号字符串
        self.outlier_xyz_mean = ""  # 粗差均值

        # 内点比例
        self.inlier_ratio  = 0.0


# ══════════════════════════════════════════════════════════════
#  向量工具（纯标准库，禁止 numpy）
# ══════════════════════════════════════════════════════════════

def _vec_sub(a, b):
    """a - b，均为 (x,y,z) 元组"""
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def _vec_cross(a, b):
    """向量叉积 a × b"""
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )


def _vec_norm(v):
    """向量模长"""
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)


def _vec_normalize(v):
    """归一化"""
    n = _vec_norm(v)
    if n < 1e-12:
        return (0.0, 0.0, 0.0)
    return (v[0]/n, v[1]/n, v[2]/n)


# ══════════════════════════════════════════════════════════════
#  由两点构建三维直线（试题册公式）
# ══════════════════════════════════════════════════════════════

def build_line(p1: Point3D, p2: Point3D):
    """
    公式：
      v = (x2-x1, y2-y1, z2-z1)
      u = v / |v|
      P0 = P1
    返回 (P0_xyz, u_xyz)
    """
    v = _vec_sub((p2.x, p2.y, p2.z), (p1.x, p1.y, p1.z))
    u = _vec_normalize(v)
    return (p1.x, p1.y, p1.z), u


# ══════════════════════════════════════════════════════════════
#  点到三维直线距离（试题册公式）
# ══════════════════════════════════════════════════════════════

def point_to_line_dist(pi: Point3D, p0_xyz, u_xyz) -> float:
    """
    d = |P0Pi × u|
    P0Pi = (xi-x0, yi-y0, zi-z0)
    """
    p0pi = _vec_sub((pi.x, pi.y, pi.z), p0_xyz)
    cross = _vec_cross(p0pi, u_xyz)
    return _vec_norm(cross)


# ══════════════════════════════════════════════════════════════
#  主 RANSAC 计算器
# ══════════════════════════════════════════════════════════════

class RANSACCalculator:

    # 固定参数（试题册规定）
    T        = 0.8    # 距离阈值
    K_MAX    = 100    # 最大迭代次数
    MIN_SAMP = 2      # 最小样本数
    SEED     = 42     # 固定随机种子保证可重复性

    def __init__(self):
        self.points : list  = []    # list[Point3D]
        self.result  = RANSACResult()

    def compute(self):
        pts = self.points
        n   = len(pts)
        res = self.result
        res.total_pts = n

        rng = random.Random(self.SEED)

        best_inlier_count = -1
        best_p0  = None
        best_u   = None
        best_ids = []
        best_iter = 0

        first_done = False
        first_ux   = 0.0
        first_cnt  = 0

        for k in range(1, self.K_MAX + 1):
            # 随机不重复抽取2个点
            sample = rng.sample(range(n), 2)
            p1, p2 = pts[sample[0]], pts[sample[1]]

            # 构建三维直线
            p0_xyz, u_xyz = build_line(p1, p2)
            if _vec_norm(u_xyz) < 1e-10:
                continue   # 两点重合跳过

            # 第一次抽样记录
            if not first_done:
                first_ux  = u_xyz[0]
                # 统计本次内点数
                first_cnt = sum(
                    1 for p in pts
                    if point_to_line_dist(p, p0_xyz, u_xyz) <= self.T
                )
                first_done = True

            # 遍历所有点计算距离，统计内点
            inlier_ids = []
            for p in pts:
                d = point_to_line_dist(p, p0_xyz, u_xyz)
                if d <= self.T:
                    inlier_ids.append(p.idx)

            cnt = len(inlier_ids)
            if cnt > best_inlier_count:
                best_inlier_count = cnt
                best_p0  = p0_xyz
                best_u   = u_xyz
                best_ids = inlier_ids[:]
                best_iter = k

        # ── 保存最优结果 ──────────────────────────────────────
        res.x0 = best_p0[0]; res.y0 = best_p0[1]; res.z0 = best_p0[2]
        res.ux = best_u[0];  res.uy = best_u[1];  res.uz = best_u[2]
        res.best_iter = best_iter
        res.first_ux  = first_ux
        res.first_inlier_count = first_cnt

        inlier_set  = set(best_ids)
        inlier_pts  = [p for p in pts if p.idx in inlier_set]
        outlier_pts = [p for p in pts if p.idx not in inlier_set]

        res.inlier_count  = len(inlier_pts)
        res.outlier_count = len(outlier_pts)
        res.inlier_pts    = inlier_pts
        res.outlier_pts   = outlier_pts

        for p in pts:
            p.dist_to_best = point_to_line_dist(p, best_p0, best_u)
            p.is_inlier    = p.idx in inlier_set

        # 考核项 12 / 13
        res.dist_pt1 = pts[0].dist_to_best   # 1号点
        res.dist_pt7 = pts[6].dist_to_best   # 7号点

        # 内点统计
        if inlier_pts:
            xs = [p.x for p in inlier_pts]
            ys = [p.y for p in inlier_pts]
            zs = [p.z for p in inlier_pts]
            ni = len(inlier_pts)
            res.inlier_x_mean = sum(xs) / ni
            res.inlier_y_mean = sum(ys) / ni
            res.inlier_z_mean = sum(zs) / ni
            res.inlier_x_min  = min(xs)
            res.inlier_z_max  = max(zs)

        # 粗差统计
        if outlier_pts:
            res.outlier_ids = ",".join(str(p.idx) for p in outlier_pts)
            ox = sum(p.x for p in outlier_pts) / len(outlier_pts)
            oy = sum(p.y for p in outlier_pts) / len(outlier_pts)
            oz = sum(p.z for p in outlier_pts) / len(outlier_pts)
            res.outlier_xyz_mean = f"({ox:.4f},{oy:.4f},{oz:.4f})"
        else:
            res.outlier_ids = "无"
            res.outlier_xyz_mean = "无"

        res.inlier_ratio = res.inlier_count / n if n else 0.0
