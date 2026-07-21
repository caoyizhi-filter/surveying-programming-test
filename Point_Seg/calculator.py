# calculator.py
# 激光点云数据的平面分割 — 核心算法
# 仅使用 Python 标准库 math
# 严格按试题册公式 (1)-(9) 实现

import math


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class Point:
    """点云数据点"""
    __slots__ = ('name', 'x', 'y', 'z')

    def __init__(self, name: str, x: float, y: float, z: float):
        self.name = name
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"{self.name}({self.x:.3f},{self.y:.3f},{self.z:.3f})"


class Grid:
    """栅格单元"""
    def __init__(self, i: int, j: int):
        self.i = i          # 行号
        self.j = j          # 列号
        self.points: list = []

    def add(self, p: Point):
        self.points.append(p)

    @property
    def size(self) -> int:
        return len(self.points)

    def avg_z(self) -> float:
        """公式 (2): 栅格单元平均高度"""
        if not self.points:
            return 0.0
        return sum(p.z for p in self.points) / len(self.points)

    def max_z(self) -> float:
        if not self.points:
            return 0.0
        return max(p.z for p in self.points)

    def min_z(self) -> float:
        if not self.points:
            return 0.0
        return min(p.z for p in self.points)

    def diff_z(self) -> float:
        """公式 (3): 高度差 = z_max - z_min"""
        if not self.points:
            return 0.0
        return self.max_z() - self.min_z()

    def var_z(self) -> float:
        """公式 (4): 高度方差"""
        if not self.points:
            return 0.0
        avg = self.avg_z()
        return sum((p.z - avg) ** 2 for p in self.points) / len(self.points)


class Plane:
    """平面 Ax + By + Cz + D = 0"""
    def __init__(self, A: float, B: float, C: float, D: float):
        self.A = A
        self.B = B
        self.C = C
        self.D = D

    @property
    def normal_len(self) -> float:
        return math.sqrt(self.A ** 2 + self.B ** 2 + self.C ** 2)

    def distance(self, p: Point) -> float:
        """公式 (8): 点到平面距离"""
        num = abs(self.A * p.x + self.B * p.y + self.C * p.z + self.D)
        return num / self.normal_len

    def signed_distance(self, p: Point) -> float:
        """带符号的距离（分子不含绝对值）"""
        return (self.A * p.x + self.B * p.y + self.C * p.z + self.D) / self.normal_len

    def project(self, p: Point) -> tuple:
        """公式 (9): 三维点投影到平面，返回 (xt, yt, zt)"""
        A, B, C, D = self.A, self.B, self.C, self.D
        denom = A * A + B * B + C * C
        xt = ((B * B + C * C) * p.x - A * (B * p.y + C * p.z + D)) / denom
        yt = ((A * A + C * C) * p.y - B * (A * p.x + C * p.z + D)) / denom
        zt = ((A * A + B * B) * p.z - C * (A * p.x + B * p.y + D)) / denom
        return (xt, yt, zt)


# ══════════════════════════════════════════════════════════════
#  距离计算
# ══════════════════════════════════════════════════════════════

def distance_3d(p1: Point, p2: Point) -> float:
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2)


# ══════════════════════════════════════════════════════════════
#  三点拟合平面（公式 7）
# ══════════════════════════════════════════════════════════════

def fit_plane(p1: Point, p2: Point, p3: Point) -> Plane:
    """用三点拟合平面，返回 Plane 对象"""
    x1, y1, z1 = p1.x, p1.y, p1.z
    x2, y2, z2 = p2.x, p2.y, p2.z
    x3, y3, z3 = p3.x, p3.y, p3.z

    A = (y2 - y1) * (z3 - z1) - (y3 - y1) * (z2 - z1)
    B = (z2 - z1) * (x3 - x1) - (z3 - z1) * (x2 - x1)
    C = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    D = -(A * x1 + B * y1 + C * z1)

    return Plane(A, B, C, D)


def triangle_area(p1: Point, p2: Point, p3: Point) -> float:
    """公式 (5): 海伦公式计算三角形面积"""
    a = distance_3d(p1, p2)
    b = distance_3d(p2, p3)
    c = distance_3d(p3, p1)
    p = (a + b + c) / 2.0
    if p <= a or p <= b or p <= c:
        return 0.0
    return math.sqrt(p * (p - a) * (p - b) * (p - c))


def is_collinear(p1: Point, p2: Point, p3: Point, threshold: float = 0.1) -> bool:
    """三点共线检测：面积 <= 阈值时视为共线"""
    return triangle_area(p1, p2, p3) <= threshold


# ══════════════════════════════════════════════════════════════
#  栅格化（公式 1）
# ══════════════════════════════════════════════════════════════

def assign_grid(p: Point, dx: float = 10.0, dy: float = 10.0) -> tuple:
    """
    公式 (1): 将点分配至栅格行列号
    i = floor(yp / dy), j = floor(xp / dx)
    返回 (i, j)
    """
    i = int(math.floor(p.y / dy))
    j = int(math.floor(p.x / dx))
    return (i, j)


def build_grids(points: list, dx: float = 10.0, dy: float = 10.0) -> dict:
    """将所有点分配到栅格，返回 {(i,j): Grid} 字典"""
    grids: dict = {}
    for p in points:
        i, j = assign_grid(p, dx, dy)
        key = (i, j)
        if key not in grids:
            grids[key] = Grid(i, j)
        grids[key].add(p)
    return grids


# ══════════════════════════════════════════════════════════════
#  RANSAC 平面分割
# ══════════════════════════════════════════════════════════════

def ransac_find_best_plane(
    points: list,
    max_iterations: int,
    distance_threshold: float = 0.1,
    area_threshold: float = 0.1
) -> dict:
    """
    顺序取点 RANSAC:
    - 第1次: P1,P2,P3; 第2次: P4,P5,P6; ...
    - 共迭代 max_iterations 次
    - 返回 {"plane": Plane, "inliers": [...], "fit_indices": (i,j,k)}
    """
    best_plane = None
    best_inliers = []
    best_fit_indices = None

    n = len(points)
    for iteration in range(max_iterations):
        idx = iteration * 3
        if idx + 2 >= n:
            break

        p1, p2, p3 = points[idx], points[idx + 1], points[idx + 2]

        # 共线检测
        if is_collinear(p1, p2, p3, area_threshold):
            continue

        plane = fit_plane(p1, p2, p3)

        # 统计内部点（排除用于拟合的3个点）
        inliers = []
        for i, pt in enumerate(points):
            if i == idx or i == idx + 1 or i == idx + 2:
                continue
            if plane.distance(pt) < distance_threshold:
                inliers.append(pt)

        if len(inliers) > len(best_inliers):
            best_inliers = inliers
            best_plane = plane
            best_fit_indices = (idx, idx + 1, idx + 2)

    return {
        "plane": best_plane,
        "inliers": best_inliers,
        "fit_indices": best_fit_indices,
    }


# ══════════════════════════════════════════════════════════════
#  统计
# ══════════════════════════════════════════════════════════════

def compute_stats(points: list) -> dict:
    """计算坐标极值"""
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    zs = [p.z for p in points]
    return {
        "xmin": min(xs), "xmax": max(xs),
        "ymin": min(ys), "ymax": max(ys),
        "zmin": min(zs), "zmax": max(zs),
    }


# ══════════════════════════════════════════════════════════════
#  主计算器
# ══════════════════════════════════════════════════════════════

class PointCloudProcessor:
    """激光点云平面分割处理器"""

    def __init__(self, points: list):
        self.points = points          # 所有点
        self.stats: dict = {}         # 统计信息
        self.grids: dict = {}         # 栅格
        self.plane_S1: Plane = None   # P1-P2-P3 拟合平面
        self.plane_J1: Plane = None   # 最佳分割平面 J1
        self.plane_J2: Plane = None   # 最佳分割平面 J2
        self.J1_result: dict = {}     # J1 RANSAC 结果
        self.J2_result: dict = {}     # J2 RANSAC 结果

    def run(self):
        """执行全部计算"""
        self._compute_stats()
        self._build_grids()
        self._fit_S1()
        self._ransac_J1()
        self._ransac_J2()
        self._compute_projections()

    # ── 统计 ────────────────────────────────────────────────

    def _compute_stats(self):
        self.stats = compute_stats(self.points)

    # ── 栅格化 ──────────────────────────────────────────────

    def _build_grids(self):
        self.grids = build_grids(self.points)

    # ── S1 平面 ─────────────────────────────────────────────

    def _fit_S1(self):
        p1, p2, p3 = self.points[0], self.points[1], self.points[2]
        self.S1_area = triangle_area(p1, p2, p3)
        self.plane_S1 = fit_plane(p1, p2, p3)

    # ── RANSAC J1 ───────────────────────────────────────────

    def _ransac_J1(self):
        self.J1_result = ransac_find_best_plane(
            self.points, max_iterations=300
        )
        self.plane_J1 = self.J1_result["plane"]
        self.J1_inliers = self.J1_result["inliers"]
        self.J1_fit_indices = self.J1_result["fit_indices"]

    # ── RANSAC J2 ───────────────────────────────────────────

    def _ransac_J2(self):
        # 排除 J1 的内部点 + J1 拟合所用的 3 个点
        exclude_set = set()
        for pt in self.J1_inliers:
            exclude_set.add(pt.name)
        if self.J1_fit_indices:
            for idx in self.J1_fit_indices:
                exclude_set.add(self.points[idx].name)

        remaining = [p for p in self.points if p.name not in exclude_set]

        self.J2_result = ransac_find_best_plane(
            remaining, max_iterations=100
        )
        self.plane_J2 = self.J2_result["plane"]
        self.J2_inliers = self.J2_result["inliers"]
        self.J2_fit_indices_in_remaining = self.J2_result["fit_indices"]

    # ── 投影 ────────────────────────────────────────────────

    def _compute_projections(self):
        # P5 → J1
        p5 = self.points[4]  # 0-indexed, P5 = index 4
        if self.plane_J1:
            self.P5_proj_J1 = self.plane_J1.project(p5)
        else:
            self.P5_proj_J1 = (0, 0, 0)

        # P800 → J2 (index 799)
        p800 = self.points[799]
        if self.plane_J2:
            self.P800_proj_J2 = self.plane_J2.project(p800)
        else:
            self.P800_proj_J2 = (0, 0, 0)

    # ── 生成标识标签 ────────────────────────────────────────

    def get_label(self, p: Point) -> str:
        """返回点的分割标识: J1 / J2 / 0"""
        if self.plane_J1 and self.plane_J1.distance(p) < 0.1:
            return "J1"
        if self.plane_J2 and self.plane_J2.distance(p) < 0.1:
            return "J2"
        return "0"
