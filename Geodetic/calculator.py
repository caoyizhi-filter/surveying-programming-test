# calculator.py
# 大地主题正反算 — 核心算法（高斯平均引数法）
# 仅使用 Python 标准库 math
# 严格按试题册公式实现

import math


# ══════════════════════════════════════════════════════════════
#  角度工具
# ══════════════════════════════════════════════════════════════

# 收敛判据: 角度 < 1e-8°, 长度 < 1e-4 m（按试题册）
ANGLE_CONV = 1e-8 * math.pi / 180.0   # 1×10⁻⁸° → rad ≈ 1.745e-10
LENGTH_CONV = 1e-4  # 长度收敛判据 (m)


def normalize_angle(deg: float) -> float:
    """角度归一化到 [0, 360)"""
    deg = deg % 360.0
    if deg < 0:
        deg += 360.0
    return deg


def normalize_signed(deg: float) -> float:
    """角度归一化到 [-180, 180)"""
    deg = deg % 360.0
    if deg < -180:
        deg += 360.0
    elif deg >= 180:
        deg -= 360.0
    return deg


# ══════════════════════════════════════════════════════════════
#  椭球参数
# ══════════════════════════════════════════════════════════════

class Ellipsoid:
    """椭球参数: 长半轴 a, 扁率分母 inv_f → 计算 e², e'², b"""

    def __init__(self, a: float, inv_f: float):
        self.a = a
        self.f = 1.0 / inv_f
        self.b = a * (1.0 - self.f)
        self.e2 = 2.0 * self.f - self.f * self.f      # 第一偏心率平方
        self.ep2 = self.e2 / (1.0 - self.e2)           # 第二偏心率平方 e'²

    def M(self, B: float) -> float:
        """子午圈曲率半径 M = a(1-e²) / (1 - e²sin²B)^(3/2)"""
        sinB = math.sin(B)
        W = math.sqrt(1.0 - self.e2 * sinB * sinB)
        return self.a * (1.0 - self.e2) / (W * W * W)

    def N(self, B: float) -> float:
        """卯酉圈曲率半径 N = a / √(1 - e²sin²B)"""
        sinB = math.sin(B)
        return self.a / math.sqrt(1.0 - self.e2 * sinB * sinB)

    def eta2(self, B: float) -> float:
        """η² = e'²·cos²B"""
        cosB = math.cos(B)
        return self.ep2 * cosB * cosB


# ══════════════════════════════════════════════════════════════
#  大地主题解算器
# ══════════════════════════════════════════════════════════════

class GeodeticSolver:
    """高斯平均引数法 — 大地主题正算与反算"""

    def __init__(self, ellipsoid: Ellipsoid):
        self.ell = ellipsoid
        self.max_iter = 100

    # ── 正算 ──────────────────────────────────────────────────

    def solve_direct(self, B1_deg: float, L1_deg: float,
                     A12_deg: float, S: float) -> tuple:
        """
        已知 B1, L1, A12, S 求 B2, L2, A21.
        返回 (B2_deg, L2_deg, A21_deg, iterations).

        长线（> SEGMENT_LEN）自动分段计算，确保高斯平均引数法收敛。
        """
        SEGMENT_LEN = 50000.0  # 50 km 分段

        if S <= SEGMENT_LEN:
            B2, L2, A21, it, _ = self._solve_direct_single(
                B1_deg, L1_deg, A12_deg, S)
            return (B2, L2, A21, it)

        # ── 分段计算 ──
        n_seg = max(1, int(math.ceil(S / SEGMENT_LEN)))
        dS = S / n_seg
        B_deg, L_deg = B1_deg, L1_deg
        A_fwd_deg = A12_deg
        total_iter = 0

        for seg in range(n_seg):
            B_deg, L_deg, _, it, A_fwd_deg = self._solve_direct_single(
                B_deg, L_deg, A_fwd_deg, dS)
            total_iter += it

        # 反方位角 = 前向 + 180°
        A21_rev = normalize_angle(A_fwd_deg + 180.0)
        return (B_deg, normalize_angle(L_deg), A21_rev, total_iter)

    # ── 单段正算（返回 5 值：B2, L2, A21_rev, iterations, A21_fwd）──

    def _solve_direct_single(self, B1_deg: float, L1_deg: float,
                             A12_deg: float, S: float) -> tuple:
        """单段正算，S ≤ SEGMENT_LEN 以保证收敛"""
        ell = self.ell
        B1 = math.radians(B1_deg)
        L1 = math.radians(L1_deg)
        A12 = math.radians(A12_deg)

        # ── 初始近似（球面大地问题正解，半径取 N₁≈a）──
        sigma = S / ell.a                         # 球面角距
        sinB1 = math.sin(B1)
        cosB1 = math.cos(B1)
        sinA12 = math.sin(A12)
        cosA12 = math.cos(A12)
        sin_sigma = math.sin(sigma)
        cos_sigma = math.cos(sigma)

        sinB2_0 = sinB1 * cos_sigma + cosB1 * sin_sigma * cosA12
        B2 = math.asin(max(-1.0, min(1.0, sinB2_0)))

        # A21 前向（球面公式）
        A21_sin = cosB1 * sinA12
        A21_cos = cosB1 * cos_sigma * cosA12 - sinB1 * sin_sigma
        A21_fwd = math.atan2(A21_sin, A21_cos)

        # ── 迭代 ──
        iterations = 0
        for iterations in range(1, self.max_iter + 1):
            Bm = (B1 + B2) * 0.5
            Am = (A12 + A21_fwd) * 0.5

            Mm = ell.M(Bm)
            Nm = ell.N(Bm)
            cosBm = math.cos(Bm)

            sinAm = math.sin(Am)
            cosAm = math.cos(Am)

            u = S * cosAm  # S·cos(Am)
            v = S * sinAm  # S·sin(Am)

            # 一阶公式（按试题册 5.1 节）
            dB = u / Mm
            dL = v / (Nm * cosBm)
            dA_fwd = dL * math.sin(Bm)   # ΔA = ΔL·sin(Bm)

            B2_new = B1 + dB
            A21_fwd_new = A12 + dA_fwd

            # 收敛判据
            if (abs(B2_new - B2) < ANGLE_CONV and
                abs(A21_fwd_new - A21_fwd) < ANGLE_CONV):
                B2 = B2_new
                A21_fwd = A21_fwd_new
                break

            B2 = B2_new
            A21_fwd = A21_fwd_new

        # ── 收敛后计算 L2, A21 ──
        L2 = math.degrees(L1 + dL)
        A21 = normalize_angle(math.degrees(A21_fwd + math.pi))
        B2_deg = math.degrees(B2)

        return (B2_deg, normalize_angle(L2), A21, iterations, math.degrees(A21_fwd))

    # ── 反算 ──────────────────────────────────────────────────

    def solve_inverse(self, B1_deg: float, L1_deg: float,
                      B2_deg: float, L2_deg: float) -> tuple:
        """
        已知 B1, L1, B2, L2 求 S, A12, A21.
        使用球面初值 + 直接迭代收敛方法，长线自动适应。
        返回 (S_m, A12_deg, A21_deg, iterations).
        """
        ell = self.ell
        B1 = math.radians(B1_deg)
        L1 = math.radians(L1_deg)
        B2 = math.radians(B2_deg)
        L2 = math.radians(L2_deg)

        dLon = L2 - L1
        sinB1 = math.sin(B1)
        cosB1 = math.cos(B1)
        sinB2 = math.sin(B2)
        cosB2 = math.cos(B2)
        cos_dLon = math.cos(dLon)
        sin_dLon = math.sin(dLon)

        # ── 球面初值 ──
        cos_sigma = sinB1 * sinB2 + cosB1 * cosB2 * cos_dLon
        cos_sigma = max(-1.0, min(1.0, cos_sigma))
        sigma = math.acos(cos_sigma)                 # 球面角距
        S = ell.a * sigma                            # 球面近似大地线长

        A12_sin = cosB2 * sin_dLon
        A12_cos = cosB1 * sinB2 - sinB1 * cosB2 * cos_dLon
        A12 = math.atan2(A12_sin, A12_cos)           # 球面正方位角

        # ── 直接迭代调整 S, A12 ──
        iterations = 0
        for iterations in range(1, self.max_iter + 1):
            # 用当前 S, A12 正算
            B2_calc_deg, L2_calc_deg, A21_deg, _ = self.solve_direct(
                B1_deg, L1_deg, math.degrees(A12), S)

            B2_calc = math.radians(B2_calc_deg)
            L2_calc = math.radians(L2_calc_deg)

            # 误差
            dB_err = B2 - B2_calc
            dL_err = dLon - (L2_calc - L1)

            # 收敛判据
            if (abs(dB_err) < ANGLE_CONV and abs(dL_err) < ANGLE_CONV):
                break

            # 用球面近似的 Jacobian 调整 S 和 A12
            Bm = (B1 + B2) * 0.5
            cosBm = math.cos(Bm)
            sinAm = math.sin(A12)
            cosAm = math.cos(A12)

            # d(dB)/dA12 ≈ -S * sinAm / Mm,   d(dB)/dS ≈ cosAm / Mm
            # d(dL)/dA12 ≈ S * cosAm / (Nm*cosBm),  d(dL)/dS ≈ sinAm / (Nm*cosBm)
            Mm = ell.M(Bm)
            Nm = ell.N(Bm)

            J00 = -S * sinAm / Mm
            J01 = cosAm / Mm
            J10 = S * cosAm / (Nm * cosBm)
            J11 = sinAm / (Nm * cosBm)

            det = J00 * J11 - J01 * J10
            if abs(det) < 1e-30:
                break

            dA12 = (J11 * dB_err - J01 * dL_err) / det
            dS   = (-J10 * dB_err + J00 * dL_err) / det

            # 阻尼因子（避免过调）
            damp = 0.8
            A12 += damp * dA12
            S += damp * dS

        A12_deg = normalize_angle(math.degrees(A12))
        _, _, A21_deg, _ = self.solve_direct(B1_deg, L1_deg, A12_deg, S)

        return (S, A12_deg, A21_deg, iterations)
