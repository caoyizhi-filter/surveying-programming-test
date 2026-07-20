# calculator.py
# 遥感图像空间前方交会 — 核心计算模块
# 仅使用 Python 标准库 math

import math


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class ExteriorOrientation:
    """单张影像的外方位元素"""
    def __init__(self, Xs, Ys, Zs, phi, omega, kappa, f, x0, y0):
        self.Xs    = Xs
        self.Ys    = Ys
        self.Zs    = Zs
        self.phi   = phi      # 俯仰角 (rad)
        self.omega = omega    # 滚动角 (rad)
        self.kappa = kappa    # 偏航角 (rad)
        self.f     = f        # 主距
        self.x0    = x0       # 像主点 x 偏移
        self.y0    = y0       # 像主点 y 偏移

        # 旋转矩阵（9 元素），由 build_rotation_matrix 填充
        self.R = [[0.0]*3 for _ in range(3)]


class ImagePointPair:
    """一组同名像点"""
    def __init__(self, idx, x1, y1, x2, y2):
        self.idx = idx
        self.x1  = x1; self.y1  = y1   # 左片原始像平面坐标
        self.x2  = x2; self.y2  = y2   # 右片原始像平面坐标

        # 标准化像平面坐标
        self.x1_bar = 0.0; self.y1_bar = 0.0
        self.x2_bar = 0.0; self.y2_bar = 0.0

        # 像空间辅助坐标
        self.U1 = 0.0; self.V1 = 0.0; self.W1 = 0.0
        self.U2 = 0.0; self.V2 = 0.0; self.W2 = 0.0

        # 投影系数
        self.N1 = 0.0; self.N2 = 0.0

        # 地面摄影测量坐标
        self.X = 0.0; self.Y = 0.0; self.Z = 0.0

        # 校核差（左右片独立算得地面坐标之差）
        self.dX = 0.0; self.dY = 0.0; self.dZ = 0.0


class IntersectionResult:
    def __init__(self):
        self.left_eo  = None   # ExteriorOrientation
        self.right_eo = None
        self.pairs    : list = []   # list[ImagePointPair]

        # 基线分量
        self.BX = 0.0; self.BY = 0.0; self.BZ = 0.0

        # 统计
        self.avg_X = 0.0; self.avg_Y = 0.0; self.avg_Z = 0.0
        self.max_Z = 0.0; self.min_Z = 0.0


# ══════════════════════════════════════════════════════════════
#  旋转矩阵（试题册公式：φ-ω-κ 转角系统）
# ══════════════════════════════════════════════════════════════

def build_rotation_matrix(phi, omega, kappa):
    """
    由 φ(俯仰角)、ω(滚动角)、κ(偏航角) 计算旋转矩阵 R(3×3)。
    R = R_φ · R_ω · R_κ
    返回 3×3 二维列表 [[a1,a2,a3],[b1,b2,b3],[c1,c2,c3]]
    """
    cp, sp = math.cos(phi),   math.sin(phi)
    co, so = math.cos(omega), math.sin(omega)
    ck, sk = math.cos(kappa), math.sin(kappa)

    a1 =  cp*ck - sp*so*sk
    a2 = -cp*sk - sp*so*ck
    a3 = -sp*co
    b1 =  co*sk
    b2 =  co*ck
    b3 = -so
    c1 =  sp*ck + cp*so*sk
    c2 = -sp*sk + cp*so*ck
    c3 =  cp*co

    return [[a1, a2, a3],
            [b1, b2, b3],
            [c1, c2, c3]]


# ══════════════════════════════════════════════════════════════
#  像点标准化（扣除像主点偏移）
# ══════════════════════════════════════════════════════════════

def standardize_point(x, y, x0, y0):
    """x̄ = x - x0, ȳ = y - y0"""
    return (x - x0, y - y0)


# ══════════════════════════════════════════════════════════════
#  像空间辅助坐标计算
# ══════════════════════════════════════════════════════════════

def image_to_auxiliary(x_bar, y_bar, f, R):
    """
    [U, V, W]^T = R · [x̄, ȳ, -f]^T
    返回 (U, V, W)
    """
    U = R[0][0]*x_bar + R[0][1]*y_bar + R[0][2]*(-f)
    V = R[1][0]*x_bar + R[1][1]*y_bar + R[1][2]*(-f)
    W = R[2][0]*x_bar + R[2][1]*y_bar + R[2][2]*(-f)
    return (U, V, W)


# ══════════════════════════════════════════════════════════════
#  投影系数（试题册公式）
# ══════════════════════════════════════════════════════════════

def compute_projection_coeffs(BX, BZ, U1, W1, U2, W2):
    """
    N1 = (BX·W2 - BZ·U2) / (U1·W2 - U2·W1)
    N2 = (BX·W1 - BZ·U1) / (U1·W2 - U2·W1)
    返回 (N1, N2)
    """
    denom = U1*W2 - U2*W1
    if abs(denom) < 1e-14:
        return (0.0, 0.0)
    N1 = (BX*W2 - BZ*U2) / denom
    N2 = (BX*W1 - BZ*U1) / denom
    return (N1, N2)


# ══════════════════════════════════════════════════════════════
#  地面摄影测量坐标
# ══════════════════════════════════════════════════════════════

def compute_ground_coords(Xs, Ys, Zs, N, U, V, W):
    """X = Xs + N·U, Y = Ys + N·V, Z = Zs + N·W"""
    X = Xs + N*U
    Y = Ys + N*V
    Z = Zs + N*W
    return (X, Y, Z)


# ══════════════════════════════════════════════════════════════
#  空间前方交会计算器
# ══════════════════════════════════════════════════════════════

class SpaceIntersectionCalculator:

    def __init__(self):
        self.left_eo  : ExteriorOrientation = None
        self.right_eo : ExteriorOrientation = None
        self.pairs    : list = []   # list[ImagePointPair]
        self.result    = IntersectionResult()

    def set_eo(self, left: ExteriorOrientation, right: ExteriorOrientation):
        self.left_eo  = left
        self.right_eo = right

    def add_pair(self, pair: ImagePointPair):
        self.pairs.append(pair)

    def compute(self):
        L = self.left_eo
        R = self.right_eo
        res = self.result
        res.left_eo  = L
        res.right_eo = R
        res.pairs    = self.pairs

        # ── 构建旋转矩阵 ──────────────────────────────────────
        L.R = build_rotation_matrix(L.phi, L.omega, L.kappa)
        R.R = build_rotation_matrix(R.phi, R.omega, R.kappa)

        # ── 基线分量 ──────────────────────────────────────────
        res.BX = R.Xs - L.Xs
        res.BY = R.Ys - L.Ys
        res.BZ = R.Zs - L.Zs

        Z_vals = []

        for pair in self.pairs:
            # 标准化像平面坐标
            pair.x1_bar, pair.y1_bar = standardize_point(pair.x1, pair.y1, L.x0, L.y0)
            pair.x2_bar, pair.y2_bar = standardize_point(pair.x2, pair.y2, R.x0, R.y0)

            # 像空间辅助坐标
            pair.U1, pair.V1, pair.W1 = image_to_auxiliary(pair.x1_bar, pair.y1_bar, L.f, L.R)
            pair.U2, pair.V2, pair.W2 = image_to_auxiliary(pair.x2_bar, pair.y2_bar, R.f, R.R)

            # 投影系数
            pair.N1, pair.N2 = compute_projection_coeffs(
                res.BX, res.BZ, pair.U1, pair.W1, pair.U2, pair.W2)

            # 地面摄影测量坐标（左片）
            pair.X, pair.Y, pair.Z = compute_ground_coords(
                L.Xs, L.Ys, L.Zs, pair.N1, pair.U1, pair.V1, pair.W1)

            # 校核：右片独立算得地面坐标
            Xc, Yc, Zc = compute_ground_coords(
                R.Xs, R.Ys, R.Zs, pair.N2, pair.U2, pair.V2, pair.W2)
            pair.dX = pair.X - Xc
            pair.dY = pair.Y - Yc
            pair.dZ = pair.Z - Zc

            Z_vals.append(pair.Z)

        # ── 统计 ──────────────────────────────────────────────
        n = len(self.pairs)
        if n:
            res.avg_X = sum(p.X for p in self.pairs) / n
            res.avg_Y = sum(p.Y for p in self.pairs) / n
            res.avg_Z = sum(p.Z for p in self.pairs) / n
            res.max_Z = max(p.Z for p in self.pairs)
            res.min_Z = min(p.Z for p in self.pairs)
