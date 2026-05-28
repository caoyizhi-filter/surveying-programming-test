# calculator.py
# TIN构建与填挖方体积计算
# 仅使用 Python 标准库 math
# TIN 构建采用 Bowyer-Watson 算法（Delaunay 三角剖分）

import math


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class Point3D:
    """三维离散点"""
    def __init__(self, idx, x, y, z):
        self.idx = idx
        self.x   = x
        self.y   = y
        self.z   = z


class Triangle:
    """TIN 中的单个三角形"""
    def __init__(self, p1: Point3D, p2: Point3D, p3: Point3D):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        # 以下由 compute() 填充
        self.area    = 0.0   # 平面面积（m²）
        self.z_avg   = 0.0   # 三顶点平均高程（m）
        self.volume  = 0.0   # 填挖方体积（正=挖，负=填）


class TINResult:
    """汇总结果"""
    def __init__(self):
        self.total_points   = 0
        self.z_min          = 0.0
        self.z_max          = 0.0
        self.total_area     = 0.0
        self.fill_volume    = 0.0   # 填方（绝对值）
        self.cut_volume     = 0.0   # 挖方
        self.triangle_count = 0
        self.triangles      : list = []


# ══════════════════════════════════════════════════════════════
#  海伦公式
# ══════════════════════════════════════════════════════════════

def _dist2d(p1: Point3D, p2: Point3D) -> float:
    """XY 平面距离"""
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)


def heron_area(p1: Point3D, p2: Point3D, p3: Point3D) -> float:
    """
    海伦公式（公式1）：
    p = (a+b+c)/2, S = sqrt(p(p-a)(p-b)(p-c))
    使用 XY 平面边长
    """
    a = _dist2d(p1, p2)
    b = _dist2d(p2, p3)
    c = _dist2d(p3, p1)
    s = (a + b + c) / 2.0
    val = s * (s - a) * (s - b) * (s - c)
    return math.sqrt(max(val, 0.0))


# ══════════════════════════════════════════════════════════════
#  Bowyer-Watson Delaunay 三角剖分
# ══════════════════════════════════════════════════════════════

def _circumcircle(ax, ay, bx, by, cx, cy):
    """
    求三角形外接圆（圆心 cx,cy 和半径平方 r²）
    返回 (ox, oy, r2)，不在外接圆内时用于判断
    """
    ax_ = bx - ax
    ay_ = by - ay
    bx_ = cx - ax
    by_ = cy - ay
    D = 2.0 * (ax_ * by_ - ay_ * bx_)
    if abs(D) < 1e-10:
        return 0.0, 0.0, float('inf')
    ux = (by_ * (ax_**2 + ay_**2) - ay_ * (bx_**2 + by_**2)) / D
    uy = (ax_ * (bx_**2 + by_**2) - bx_ * (ax_**2 + ay_**2)) / D
    ox = ax + ux
    oy = ay + uy
    r2 = ux**2 + uy**2
    return ox, oy, r2


def _in_circumcircle(ax, ay, bx, by, cx, cy, px, py) -> bool:
    """判断点 (px,py) 是否在三角形(a,b,c)外接圆内"""
    ox, oy, r2 = _circumcircle(ax, ay, bx, by, cx, cy)
    d2 = (px - ox)**2 + (py - oy)**2
    return d2 < r2 - 1e-10


def bowyer_watson(points: list) -> list:
    """
    Bowyer-Watson 算法构建 Delaunay TIN
    输入：list[Point3D]
    输出：list of (idx1, idx2, idx3)  — 三角形顶点索引组合
    """
    n = len(points)
    # 计算包围盒
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx = max_x - min_x
    dy = max_y - min_y
    delta = max(dx, dy) * 10.0

    # 创建足够大的超级三角形（使用虚拟点，索引 n, n+1, n+2）
    class _Pt:
        def __init__(self, x, y):
            self.x = x; self.y = y; self.idx = -1

    sp1 = _Pt(min_x - delta,     min_y - delta)
    sp2 = _Pt(min_x + 2*delta,   min_y - delta)
    sp3 = _Pt(min_x + delta/2.0, min_y + 2*delta)

    all_pts = list(points) + [sp1, sp2, sp3]
    ni1, ni2, ni3 = n, n+1, n+2

    # 三角形集合：每个元素 (i, j, k) 为 all_pts 中的索引
    triangles = [(ni1, ni2, ni3)]

    for pi, p in enumerate(points):
        px, py = p.x, p.y

        # 找出外接圆包含 p 的所有三角形
        bad = []
        for tri in triangles:
            a, b, c = tri
            if _in_circumcircle(
                all_pts[a].x, all_pts[a].y,
                all_pts[b].x, all_pts[b].y,
                all_pts[c].x, all_pts[c].y,
                px, py
            ):
                bad.append(tri)

        # 找出多边形边界（非共享边）
        boundary = {}
        for tri in bad:
            edges = [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])]
            for e in edges:
                key = tuple(sorted(e))
                boundary[key] = boundary.get(key, 0) + 1

        # 删除 bad 三角形
        for tri in bad:
            triangles.remove(tri)

        # 用边界边与新点组成新三角形
        for (ei, ej), cnt in boundary.items():
            if cnt == 1:   # 只属于一个坏三角形的边
                triangles.append((ei, ej, pi))

    # 移除含超级三角形顶点的三角形
    result = []
    for tri in triangles:
        if all(idx < n for idx in tri):
            result.append(tri)

    return result


# ══════════════════════════════════════════════════════════════
#  主计算器
# ══════════════════════════════════════════════════════════════

class TINCalculator:

    def __init__(self):
        self.points  : list  = []    # list[Point3D]
        self.Hd      : float = 0.0   # 设计基准高程
        self.result  = TINResult()

    def compute(self):
        pts = self.points
        res = self.result

        res.total_points = len(pts)
        res.z_min = min(p.z for p in pts)
        res.z_max = max(p.z for p in pts)

        # 构建 Delaunay TIN
        tri_indices = bowyer_watson(pts)

        # 计算每个三角形
        triangles = []
        total_area = 0.0
        fill_vol   = 0.0
        cut_vol    = 0.0

        for (i, j, k) in tri_indices:
            p1, p2, p3 = pts[i], pts[j], pts[k]
            tri = Triangle(p1, p2, p3)

            # 海伦公式面积（公式1）
            tri.area  = heron_area(p1, p2, p3)

            # 平均高程
            tri.z_avg = (p1.z + p2.z + p3.z) / 3.0

            # 填挖方体积（公式2）
            # V = S * (z1+z2+z3)/3 - S * Hd
            tri.volume = tri.area * tri.z_avg - tri.area * self.Hd

            total_area += tri.area

            # 判定（公式3）
            if tri.volume > 0:
                cut_vol  += tri.volume    # 挖方
            else:
                fill_vol += abs(tri.volume)   # 填方

            triangles.append(tri)

        res.total_area     = total_area
        res.fill_volume    = fill_vol
        res.cut_volume     = cut_vol
        res.triangle_count = len(triangles)
        res.triangles      = triangles
