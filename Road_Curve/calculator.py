# calculator.py
# 道路曲线要素计算与里程桩计算 — 核心算法
# 仅使用 Python 标准库 math
# 严格使用试题册 5.1 / 5.2 / 5.3 公式，无工程修正

import math


# ══════════════════════════════════════════════════════════════
#  度分秒 → 十进制度（保持 ≥8 位小数参与全部后续计算）
# ══════════════════════════════════════════════════════════════

def dms_to_decimal(deg: float, min_: float, sec: float) -> float:
    """
    将度分秒转换为十进制度。
    Python float 为双精度（约 15–17 位有效数字），
    自动满足 8 位小数精度要求，中间过程不做任何舍入。
    """
    return deg + min_ / 60.0 + sec / 3600.0


# ══════════════════════════════════════════════════════════════
#  道路圆曲线计算器
# ══════════════════════════════════════════════════════════════

class RoadCurve:

    def __init__(self, JD_stake: float, R: float,
                 alpha_deg: float, alpha_min: float, alpha_sec: float):
        # ── 原始输入 ──────────────────────────────────────────
        self.JD_stake = JD_stake
        self.R = R
        self.alpha_deg_raw = alpha_deg
        self.alpha_min_raw = alpha_min
        self.alpha_sec_raw = alpha_sec

        # ── 偏角（全程保持 ≥8 位小数，不截断）────────────────
        self.alpha_deg = dms_to_decimal(alpha_deg, alpha_min, alpha_sec)
        self.alpha_rad = math.radians(self.alpha_deg)  # = α° × π / 180

        # ── 曲线要素（试题 5.1 四条公式）────────────────────
        self.T = 0.0   # 切线长
        self.L = 0.0   # 曲线总长
        self.E = 0.0   # 外距
        self.D = 0.0   # 校差值（切曲差）

        # ── 主点里程（试题 5.2）────────────────────────────
        self.ZY = 0.0  # 直圆点
        self.QZ = 0.0  # 曲中点
        self.YZ = 0.0  # 圆直点
        self.JD_check = 0.0  # 校核 JD

        # ── 指定桩号（试题 5.3）────────────────────────────
        self.specified_stake = 0.0
        self.l = 0.0    # 距 ZY 弧长
        self.x = 0.0    # 局部坐标 x
        self.y = 0.0    # 局部坐标 y

    # ── 试题 5.1：圆曲线要素计算（4 条公式）─────────────────

    def compute_elements(self):
        """
        公式 1: T = R · tan(α / 2)
        公式 2: L = R · α · π / 180
        公式 3: E = R · (sec(α/2) − 1) = R · (1 / cos(α/2) − 1)
        公式 4: D = 2T − L
        """
        half_rad = self.alpha_rad / 2.0

        # 公式 1
        self.T = self.R * math.tan(half_rad)

        # 公式 2（直接用 α° × π/180，不用 math.radians 缩写，严格对应试题册公式形式）
        self.L = self.R * self.alpha_deg * math.pi / 180.0

        # 公式 3
        self.E = self.R * (1.0 / math.cos(half_rad) - 1.0)

        # 公式 4
        self.D = 2.0 * self.T - self.L

    # ── 试题 5.2：主点里程桩号计算 ──────────────────────────

    def compute_stakes(self):
        """
        ZY = JD − T
        YZ = ZY + L
        QZ = ZY + L / 2
        JD 校核 = QZ + D / 2
        """
        self.ZY = self.JD_stake - self.T
        self.YZ = self.ZY + self.L
        self.QZ = self.ZY + self.L / 2.0
        self.JD_check = self.QZ + self.D / 2.0

    # ── 试题 5.3：指定桩号局部坐标 ──────────────────────────

    def compute_local_coords(self, specified_stake: float):
        """
        以 ZY 为原点，切线前进方向为 x 轴，曲线内侧径向为 y 轴。

        l   = 指定桩号 − ZY
        β   = l / R   （圆心角，弧度）
        x   = R · sin(β)
        y   = R · (1 − cos(β))
        """
        self.specified_stake = specified_stake
        self.l = specified_stake - self.ZY
        if self.l < 0 or self.l > self.L:
            raise ValueError(
                f"指定桩号 {specified_stake:.3f} 不在曲线范围内 "
                f"(ZY={self.ZY:.3f} ~ YZ={self.YZ:.3f})"
            )
        beta = self.l / self.R
        self.x = self.R * math.sin(beta)
        self.y = self.R * (1.0 - math.cos(beta))

    # ── 一键计算 ─────────────────────────────────────────────

    def compute_all(self, specified_stake: float = None):
        self.compute_elements()
        self.compute_stakes()
        if specified_stake is not None:
            self.compute_local_coords(specified_stake)
