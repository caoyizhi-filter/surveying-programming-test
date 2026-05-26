# calculator.py
# 空间前方交会核心算法
# 仅使用 Python 标准库 math

import math


# ══════════════════════════════════════════════════════════════
#  数据容器
# ══════════════════════════════════════════════════════════════

class ImageData:
    """单张影像的外方位元素 + 方向余弦矩阵"""

    def __init__(self, Xs, Ys, Zs, phi_deg, omega_deg, kappa_deg):
        # 外方位元素（角度原始值）
        self.Xs        = Xs
        self.Ys        = Ys
        self.Zs        = Zs
        self.phi_deg   = phi_deg
        self.omega_deg = omega_deg
        self.kappa_deg = kappa_deg

        # 转弧度（公式1）
        self.phi   = math.radians(phi_deg)
        self.omega = math.radians(omega_deg)
        self.kappa = math.radians(kappa_deg)

        # 方向余弦矩阵（公式2）
        self.a1 = self.b1 = self.c1 = 0.0
        self.a2 = self.b2 = self.c2 = 0.0
        self.a3 = self.b3 = self.c3 = 0.0
        self._build_rotation()

    def _build_rotation(self):
        """按试题册公式2计算9个方向余弦"""
        p = self.phi
        o = self.omega
        k = self.kappa

        self.a1 =  math.cos(p) * math.cos(k) - math.sin(p) * math.sin(o) * math.sin(k)
        self.b1 = -math.cos(p) * math.sin(k) - math.sin(p) * math.sin(o) * math.cos(k)
        self.c1 = -math.sin(p) * math.cos(o)

        self.a2 =  math.cos(o) * math.sin(k)
        self.b2 =  math.cos(o) * math.cos(k)
        self.c2 = -math.sin(o)

        self.a3 =  math.sin(p) * math.cos(k) + math.cos(p) * math.sin(o) * math.sin(k)
        self.b3 = -math.sin(p) * math.sin(k) + math.cos(p) * math.sin(o) * math.cos(k)
        self.c3 =  math.cos(p) * math.cos(o)


class IntersectionResult:
    """前方交会计算结果"""

    def __init__(self):
        self.X = 0.0
        self.Y = 0.0
        self.Z = 0.0


# ══════════════════════════════════════════════════════════════
#  前方交会计算
# ══════════════════════════════════════════════════════════════

class SpaceIntersection:
    """
    空间前方交会解算器

    原理：
      由共线方程（公式3）可知，对左右两片各建立2个方程，
      共4个方程，未知数为地面点 X, Y, Z，
      用最小二乘或直接解析法求解。

    本程序采用投影光线交会法（直接解析）：
      将每条光线参数化为：
        P = Ps + t * d
      其中 d 由共线方程反推得投影方向向量，
      再用两直线最短距离中点作为交会点。
    """

    def __init__(self):
        self.left  : ImageData       = None
        self.right : ImageData       = None
        self.x0    = 0.0   # 像主点 x 偏移 (mm)
        self.y0    = 0.0   # 像主点 y 偏移 (mm)
        self.f     = 0.0   # 主距 (mm)

        # 像点坐标
        self.x1 = self.y1 = 0.0   # 左像点
        self.x2 = self.y2 = 0.0   # 右像点

        self.result : IntersectionResult = IntersectionResult()

    # ── 核心计算 ──────────────────────────────────────────────

    def compute(self):
        """主入口：解算地面点坐标"""
        L = self.left
        R = self.right

        # ── 左片光线方向向量（像空间坐标系 → 物空间）──────────
        # 像点改正
        dx1 = self.x1 - self.x0
        dy1 = self.y1 - self.y0
        dx2 = self.x2 - self.x0
        dy2 = self.y2 - self.y0

        # 物方投影方向（旋转矩阵 R^T * [x-x0, y-y0, -f]^T）
        # 即 d = (a1*x + a2*y - a3*f, b1*x + b2*y - b3*f, c1*x + c2*y - c3*f)
        #   注意：共线方程的标准写法中分母对应 a3/b3/c3 行
        d1x = L.a1 * dx1 + L.a2 * dy1 - L.a3 * self.f
        d1y = L.b1 * dx1 + L.b2 * dy1 - L.b3 * self.f
        d1z = L.c1 * dx1 + L.c2 * dy1 - L.c3 * self.f

        d2x = R.a1 * dx2 + R.a2 * dy2 - R.a3 * self.f
        d2y = R.b1 * dx2 + R.b2 * dy2 - R.b3 * self.f
        d2z = R.c1 * dx2 + R.c2 * dy2 - R.c3 * self.f

        # ── 两空间直线最近点（前方交会）─────────────────────────
        # 直线1: P1 + t1 * d1
        # 直线2: P2 + t2 * d2
        # 解方程组得 t1, t2，取中点

        # 向量基准差
        wx = R.Xs - L.Xs
        wy = R.Ys - L.Ys
        wz = R.Zs - L.Zs

        d1d1 = d1x*d1x + d1y*d1y + d1z*d1z
        d2d2 = d2x*d2x + d2y*d2y + d2z*d2z
        d1d2 = d1x*d2x + d1y*d2y + d1z*d2z

        d1w  = d1x*wx  + d1y*wy  + d1z*wz
        d2w  = d2x*wx  + d2y*wy  + d2z*wz

        denom = d1d1 * d2d2 - d1d2 * d1d2
        if abs(denom) < 1e-12:
            raise ValueError("左右光线近似平行，无法交会")

        t1 = ( d1w * d2d2 - d2w * d1d2) / denom
        t2 = ( d2w * d1d1 - d1w * d1d2) / denom

        # 两光线上的最近点
        P1x = L.Xs + t1 * d1x
        P1y = L.Ys + t1 * d1y
        P1z = L.Zs + t1 * d1z

        P2x = R.Xs + t2 * d2x
        P2y = R.Ys + t2 * d2y
        P2z = R.Zs + t2 * d2z

        # 取中点作为地面点
        self.result.X = (P1x + P2x) / 2.0
        self.result.Y = (P1y + P2y) / 2.0
        self.result.Z = (P1z + P2z) / 2.0
