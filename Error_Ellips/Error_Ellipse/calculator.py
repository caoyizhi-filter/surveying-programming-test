# calculator.py
# 误差椭圆核心计算，只用 math 标准库

import math


class Point:
    """单个点的数据容器"""

    def __init__(self, name, Qxx, Qyy, Qxy, mu):
        # 输入数据
        self.name = name
        self.Qxx  = Qxx
        self.Qyy  = Qyy
        self.Qxy  = Qxy
        self.mu   = mu

        # 计算结果（初始为0，调用 compute 后填入）
        self.sigma_xx = 0.0
        self.sigma_yy = 0.0
        self.sigma_xy = 0.0
        self.E        = 0.0   # 长半轴
        self.F        = 0.0   # 短半轴
        self.phi_E    = 0.0   # 长轴方位角（度）
        self.sigma_0  = 0.0   # σ(0°)
        self.sigma_45 = 0.0   # σ(45°)
        self.sigma_90 = 0.0   # σ(90°)
        self.sigma_135= 0.0   # σ(135°)
        self.sigma_180= 0.0   # σ(180°)
        self.anomaly  = 0     # 1=异常 0=正常


def sigma_dir(sxx, syy, sxy, deg):
    """任意方向位差：σ(α)² = σxx·cos²α + σyy·sin²α - 2σxy·sinα·cosα"""
    a = math.radians(deg)
    val = sxx * math.cos(a)**2 + syy * math.sin(a)**2 - 2 * sxy * math.sin(a) * math.cos(a)
    return math.sqrt(max(val, 0.0))


def compute(p: Point):
    """对单个 Point 完成全部计算"""
    mu2 = p.mu ** 2

    # 1. 点位方差
    p.sigma_xx = mu2 * p.Qxx
    p.sigma_yy = mu2 * p.Qyy
    p.sigma_xy = mu2 * p.Qxy

    sxx = p.sigma_xx
    syy = p.sigma_yy
    sxy = p.sigma_xy

    # 2. 长短半轴
    half_sum  = (sxx + syy) / 2.0
    half_diff = (sxx - syy) / 2.0
    root      = math.sqrt(half_diff**2 + sxy**2)
    p.E = math.sqrt(max(half_sum + root, 0.0))
    p.F = math.sqrt(max(half_sum - root, 0.0))

    # 3. 长轴方位角
    if abs(sxx - syy) < 1e-12:
        two_phi = math.pi / 2.0
    else:
        two_phi = math.atan2(2.0 * sxy, sxx - syy)
    p.phi_E = math.degrees(two_phi / 2.0) % 180.0

    # 4. 各方向位差
    p.sigma_0   = sigma_dir(sxx, syy, sxy, 0)
    p.sigma_45  = sigma_dir(sxx, syy, sxy, 45)
    p.sigma_90  = sigma_dir(sxx, syy, sxy, 90)
    p.sigma_135 = sigma_dir(sxx, syy, sxy, 135)
    p.sigma_180 = sigma_dir(sxx, syy, sxy, 180)

    # 5. 异常判定
    p.anomaly = 1 if (p.E > 0.20 or p.F > 0.10 or p.sigma_90 > 0.15) else 0


def compute_all(points: list) -> dict:
    """批量计算，返回统计汇总"""
    for p in points:
        compute(p)

    n = len(points)
    return {
        "avg_E":        sum(p.E      for p in points) / n,
        "avg_F":        sum(p.F      for p in points) / n,
        "avg_phi_E":    sum(p.phi_E  for p in points) / n,
        "anomaly_count":sum(p.anomaly for p in points),
        "normal_count": sum(1 - p.anomaly for p in points),
        "total_count":  n,
    }
