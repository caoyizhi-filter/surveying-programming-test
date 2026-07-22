# calculator.py
# 核心算法模块 — 仅使用 Python 标准库 math
# ============================================================
# 【使用说明】
#   框架内嵌两套完整可运行示例（均已注释）：
#
#   示例A — 道路曲线要素计算（简单，13项输出）
#     适合: 公式少、无迭代、无数据类
#
#   示例B — 激光点云平面分割（复杂，43项输出，含RANSAC迭代）
#     适合: 公式多、有迭代、有数据类（Point/Grid/Plane）
#
#   做你的题目时: 取消最接近的那个示例注释 → 跑通 → 替换成你的公式
# ============================================================

import math


# ============================================================
#  第1部分：工具函数（纯函数，不依赖 self）
# ============================================================

# ------------------------------------------------------------
# 示例A: 道路曲线 — 度分秒转换 + 角度归一化
# ------------------------------------------------------------

def dms_to_decimal(d: float, m: float, s: float) -> float:
    """度分秒 → 十进制度"""
    return d + m / 60.0 + s / 3600.0

def normalize_angle(deg: float) -> float:
    """角度归一化到 [0, 360)"""
    deg = deg % 360.0
    if deg < 0:
        deg += 360.0
    return deg

# ------------------------------------------------------------
# 示例B: 点云分割 — 距离计算 + 三角形面积 + 共线检测
# （如需使用，取消注释）
# ------------------------------------------------------------

# def distance_3d(p1, p2, /) -> float:
#     """三维空间中两点距离（Point对象）"""
#     return math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2 + (p1.z-p2.z)**2)

# def triangle_area(p1, p2, p3, /) -> float:
#     """公式(5): 海伦公式计算三角形面积，三点共线时返回 0"""
#     a = distance_3d(p1, p2)
#     b = distance_3d(p2, p3)
#     c = distance_3d(p3, p1)
#     p = (a + b + c) / 2.0
#     if p <= a or p <= b or p <= c:
#         return 0.0
#     return math.sqrt(p * (p - a) * (p - b) * (p - c))

# def is_collinear(p1, p2, p3, threshold=0.1) -> bool:
#     """三点共线检测：面积 <= 阈值 → 共线"""
#     return triangle_area(p1, p2, p3) <= threshold

# def assign_grid(p, dx=10.0, dy=10.0) -> tuple:
#     """公式(1): 点分配至栅格行列号 i=floor(yp/dy), j=floor(xp/dx)"""
#     i = int(math.floor(p.y / dy))
#     j = int(math.floor(p.x / dx))
#     return (i, j)

# <FILL: 你的题目需要的工具函数>


# ============================================================
#  第2部分：数据类（只存属性，不做计算）
# ============================================================

# ------------------------------------------------------------
# 示例B: 点云分割 — Point, Grid, Plane 三个数据类
# （如需使用，取消注释）
# ------------------------------------------------------------

# class Point:
#     """点云数据点"""
#     def __init__(self, name: str, x: float, y: float, z: float):
#         self.name = name
#         self.x = x
#         self.y = y
#         self.z = z

# class Grid:
#     """栅格单元"""
#     def __init__(self, i: int, j: int):
#         self.i = i
#         self.j = j
#         self.points = []              # 该栅格内的点列表
#
#     def add(self, p: Point):
#         self.points.append(p)
#
#     def size(self) -> int:
#         return len(self.points)
#
#     def avg_z(self) -> float:
#         """公式(2): 栅格平均高度"""
#         if not self.points:
#             return 0.0
#         return sum(p.z for p in self.points) / len(self.points)
#
#     def max_z(self) -> float:
#         return max(p.z for p in self.points) if self.points else 0.0
#
#     def min_z(self) -> float:
#         return min(p.z for p in self.points) if self.points else 0.0
#
#     def diff_z(self) -> float:
#         """公式(3): 高度差 = z_max - z_min"""
#         return self.max_z() - self.min_z()
#
#     def var_z(self) -> float:
#         """公式(4): 高度方差"""
#         if not self.points:
#             return 0.0
#         avg = self.avg_z()
#         return sum((p.z - avg) ** 2 for p in self.points) / len(self.points)

# class Plane:
#     """平面 Ax + By + Cz + D = 0"""
#     def __init__(self, A: float, B: float, C: float, D: float):
#         self.A = A
#         self.B = B
#         self.C = C
#         self.D = D
#
#     def normal_len(self) -> float:
#         return math.sqrt(self.A**2 + self.B**2 + self.C**2)
#
#     def distance(self, p: Point) -> float:
#         """公式(8): 点到平面距离"""
#         num = abs(self.A*p.x + self.B*p.y + self.C*p.z + self.D)
#         return num / self.normal_len()
#
#     def project(self, p: Point) -> tuple:
#         """公式(9): 点投影到平面，返回 (xt, yt, zt)"""
#         A, B, C, D = self.A, self.B, self.C, self.D
#         denom = A*A + B*B + C*C
#         xt = ((B*B+C*C)*p.x - A*(B*p.y + C*p.z + D)) / denom
#         yt = ((A*A+C*C)*p.y - B*(A*p.x + C*p.z + D)) / denom
#         zt = ((A*A+B*B)*p.z - C*(A*p.x + B*p.y + D)) / denom
#         return (xt, yt, zt)

# <FILL: 你的数据类>


# ============================================================
#  第3部分：主计算器类
# ============================================================

# ============================================================
# 示例A: 道路曲线 — 简单结构（3个步骤 + 1个入口）
# ============================================================

class Calculator_A:
    """
    道路曲线要素计算与里程桩计算 [简单示例]

    使用方法:
        calc = Calculator_A(JD里程, 半径R, 偏角度, 偏角分, 偏角秒)
        calc.compute_all(指定桩号)
        # 读取: calc.T, calc.L, calc.ZY, calc.QZ, calc.YZ
    """

    def __init__(self, JD_stake, R, alpha_deg, alpha_min, alpha_sec):
        # ===== A区: 保存原始输入 =====
        self.JD_stake = JD_stake
        self.R = R
        self.alpha_deg_raw = alpha_deg
        self.alpha_min_raw = alpha_min
        self.alpha_sec_raw = alpha_sec
        self.alpha_deg = dms_to_decimal(alpha_deg, alpha_min, alpha_sec)
        self.alpha_rad = math.radians(self.alpha_deg)

        # ===== B区: 声明输出属性（对照试题册输出清单，全部初始化为 0.0）=====
        self.T = 0.0          # 切线长
        self.L = 0.0          # 曲线总长
        self.E = 0.0          # 外距
        self.D = 0.0          # 校差值
        self.ZY = 0.0         # 直圆点
        self.QZ = 0.0         # 曲中点
        self.YZ = 0.0         # 圆直点
        self.JD_check = 0.0   # 校核JD
        self.specified_stake = 0.0
        self.l = 0.0          # 距ZY弧长
        self.x = 0.0          # 局部坐标x
        self.y = 0.0          # 局部坐标y

    # ── 子步骤 ──

    def compute_elements(self):
        """公式(1-4): T = R·tan(α/2), L = R·α·π/180, E = R·(sec(α/2)-1), D = 2T-L"""
        half = self.alpha_rad / 2.0
        self.T = self.R * math.tan(half)
        self.L = self.R * self.alpha_deg * math.pi / 180.0
        self.E = self.R * (1.0 / math.cos(half) - 1.0)
        self.D = 2.0 * self.T - self.L

    def compute_stakes(self):
        """公式(5-8): ZY=JD-T, YZ=ZY+L, QZ=ZY+L/2, JD校核=QZ+D/2"""
        self.ZY = self.JD_stake - self.T
        self.YZ = self.ZY + self.L
        self.QZ = self.ZY + self.L / 2.0
        self.JD_check = self.QZ + self.D / 2.0

    def compute_local_coords(self, specified_stake):
        """公式(9-11): l=桩号-ZY, β=l/R, x=R·sinβ, y=R·(1-cosβ)"""
        self.specified_stake = specified_stake
        self.l = specified_stake - self.ZY
        if self.l < 0 or self.l > self.L:
            raise ValueError(f"桩号 {specified_stake:.3f} 不在曲线范围内")
        beta = self.l / self.R
        self.x = self.R * math.sin(beta)
        self.y = self.R * (1.0 - math.cos(beta))

    # ── 入口 ──

    def compute_all(self, specified_stake=None):
        self.compute_elements()       # 步骤1: 不依赖别人
        self.compute_stakes()         # 步骤2: 依赖步骤1
        if specified_stake is not None:
            self.compute_local_coords(specified_stake)  # 步骤3(可选)


# ============================================================
# 示例B: 点云分割 — 复杂结构（数据类 + 6个计算阶段 + RANSAC迭代）
# （如需使用，取消整个 class 的注释）
# ============================================================

# class Calculator_B:
#     """
#     激光点云数据的平面分割 [复杂示例]
#
#     使用方法:
#         proc = Calculator_B(points)     # points = [Point, ...]
#         proc.run()
#         # 读取: proc.stats, proc.plane_J1, proc.J1_inliers, ...
#     """
#
#     def __init__(self, points: list):
#         # ===== A区: 保存原始输入 =====
#         self.points = points       # 所有点
#
#         # ===== B区: 声明输出属性 =====
#         self.stats = {}            # 统计: xmin, xmax, ymin, ymax, zmin, zmax
#         self.grids = {}            # 栅格: {(i,j): Grid}
#         self.plane_S1 = None       # P1-P2-P3 拟合平面
#         self.S1_area = 0.0         # 三角形面积
#         self.plane_J1 = None       # 最佳分割平面 J1
#         self.J1_inliers = []       # J1 内部点
#         self.plane_J2 = None       # 分割平面 J2
#         self.J2_inliers = []       # J2 内部点
#         self.P5_proj_J1 = (0,0,0)  # P5 投影到 J1
#         self.P800_proj_J2 = (0,0,0) # P800 投影到 J2
#
#     # ── 子步骤 ──
#
#     def _compute_stats(self):
#         """统计坐标极值"""
#         xs = [p.x for p in self.points]
#         ys = [p.y for p in self.points]
#         zs = [p.z for p in self.points]
#         self.stats = {
#             "xmin": min(xs), "xmax": max(xs),
#             "ymin": min(ys), "ymax": max(ys),
#             "zmin": min(zs), "zmax": max(zs),
#         }
#
#     def _build_grids(self):
#         """公式(1): 所有点分配至栅格"""
#         for p in self.points:
#             i, j = assign_grid(p)
#             key = (i, j)
#             if key not in self.grids:
#                 self.grids[key] = Grid(i, j)
#             self.grids[key].add(p)
#
#     def _fit_S1(self):
#         """公式(5)(7): P1-P2-P3 拟合平面 S1"""
#         p1, p2, p3 = self.points[0], self.points[1], self.points[2]
#         self.S1_area = triangle_area(p1, p2, p3)
#         # 三点拟合平面: 法向量 = (p2-p1) × (p3-p1)
#         A = (p2.y-p1.y)*(p3.z-p1.z) - (p3.y-p1.y)*(p2.z-p1.z)
#         B = (p2.z-p1.z)*(p3.x-p1.x) - (p3.z-p1.z)*(p2.x-p1.x)
#         C = (p2.x-p1.x)*(p3.y-p1.y) - (p3.x-p1.x)*(p2.y-p1.y)
#         D = -(A*p1.x + B*p1.y + C*p1.z)
#         self.plane_S1 = Plane(A, B, C, D)
#
#     def _ransac(self, max_iter=300, exclude_indices=None):
#         """
#         RANSAC 平面分割。
#         顺序取点: 第1次取 P1P2P3, 第2次取 P4P5P6, ...
#         返回: {"plane": Plane, "inliers": [Point], "fit_indices": (i,j,k)}
#         """
#         best_plane = None
#         best_inliers = []
#         best_indices = None
#         n = len(self.points)
#         exclude = set(exclude_indices or [])
#
#         for iteration in range(max_iter):
#             idx = iteration * 3
#             if idx + 2 >= n:
#                 break
#             if idx in exclude or idx+1 in exclude or idx+2 in exclude:
#                 continue
#
#             p1, p2, p3 = self.points[idx], self.points[idx+1], self.points[idx+2]
#             if is_collinear(p1, p2, p3):
#                 continue
#
#             # 三点拟合平面
#             A = (p2.y-p1.y)*(p3.z-p1.z) - (p3.y-p1.y)*(p2.z-p1.z)
#             B = (p2.z-p1.z)*(p3.x-p1.x) - (p3.z-p1.z)*(p2.x-p1.x)
#             C = (p2.x-p1.x)*(p3.y-p1.y) - (p3.x-p1.x)*(p2.y-p1.y)
#             D = -(A*p1.x + B*p1.y + C*p1.z)
#             plane = Plane(A, B, C, D)
#
#             # 统计内点（排除用于拟合的3个点）
#             inliers = []
#             for i, pt in enumerate(self.points):
#                 if i == idx or i == idx+1 or i == idx+2:
#                     continue
#                 if plane.distance(pt) < 0.1:     # 距离阈值 0.1m
#                     inliers.append(pt)
#
#             if len(inliers) > len(best_inliers):
#                 best_inliers = inliers
#                 best_plane = plane
#                 best_indices = (idx, idx+1, idx+2)
#
#         return {"plane": best_plane, "inliers": best_inliers, "fit_indices": best_indices}
#
#     def _ransac_J1(self):
#         result = self._ransac(max_iter=300)
#         self.plane_J1 = result["plane"]
#         self.J1_inliers = result["inliers"]
#         self.J1_fit_indices = result["fit_indices"]
#
#     def _ransac_J2(self):
#         # 排除 J1 的内部点 + 拟合用的3个点
#         exclude = set()
#         for pt in self.J1_inliers:
#             exclude.add(self.points.index(pt))
#         if self.J1_fit_indices:
#             for idx in self.J1_fit_indices:
#                 exclude.add(idx)
#         result = self._ransac(max_iter=100, exclude_indices=list(exclude))
#         self.plane_J2 = result["plane"]
#         self.J2_inliers = result["inliers"]
#
#     def _compute_projections(self):
#         """P5 投影到 J1, P800 投影到 J2"""
#         p5 = self.points[4]
#         if self.plane_J1:
#             self.P5_proj_J1 = self.plane_J1.project(p5)
#         p800 = self.points[799]
#         if self.plane_J2:
#             self.P800_proj_J2 = self.plane_J2.project(p800)
#
#     # ── 入口 ──
#
#     def run(self):
#         """按依赖顺序执行全部计算"""
#         self._compute_stats()        # 统计: 不依赖别人
#         self._build_grids()          # 栅格: 不依赖别人
#         self._fit_S1()               # S1平面: 依赖统计
#         self._ransac_J1()            # J1: 依赖栅格+点
#         self._ransac_J2()            # J2: 依赖J1结果(排除已分类点)
#         self._compute_projections()  # 投影: 依赖J1, J2
#
#     def get_label(self, p: Point) -> str:
#         """返回点的分割标识: J1 / J2 / 0"""
#         if self.plane_J1 and self.plane_J1.distance(p) < 0.1:
#             return "J1"
#         if self.plane_J2 and self.plane_J2.distance(p) < 0.1:
#             return "J2"
#         return "0"


# ============================================================
# 【使用你选择的示例】
#
#  简单题 → 取消 Calculator_A 的注释，改名为你的 Calculator
#  复杂题 → 取消 Calculator_B + Point/Grid/Plane 的注释，改名为你的 Calculator
#
#  然后:
#   1. 删掉不需要的另一个示例
#   2. 修改 __init__ 的输入参数 和 输出属性列表
#   3. 替换子步骤方法中的公式
#   4. 调整 compute_all / run 中的调用顺序
# ============================================================

# <FILL: 你的计算器类>
# 如果你选示例A — 把 class Calculator_A 改名并取消注释
# 如果你选示例B — 把 class Calculator_B + 三个数据类取消注释
