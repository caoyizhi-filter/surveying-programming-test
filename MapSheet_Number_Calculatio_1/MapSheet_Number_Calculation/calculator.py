# calculator.py
# 地形图图幅编号计算核心算法
# 仅使用 Python 标准库 math

import math


# ══════════════════════════════════════════════════════════════
#  各比例尺分幅参数（纬差°，经差°）
# ══════════════════════════════════════════════════════════════
SCALES = {
    "100万":  (4.0,          6.0),
    "50万":   (2.0,          3.0),
    "25万":   (1.0,          1.5),
    "10万":   (20/60,        30/60),
    "5万":    (10/60,        15/60),
    "2.5万":  (5/60,         7.5/60),
    "1万":    (2.5/60,       3.75/60),
    "5千":    (1.25/60,      1.875/60),
}

# 行列代码表
ROW_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"   # 1:100万行号字母

# 1:50万 代码（4格：左上A、右上B、左下C、右下D，按纬度从高到低）
CODE_50W  = ["A", "B", "C", "D"]             # 行优先
CODE_25W  = [f"[{i}]" for i in range(1, 17)] # 1-16
CODE_10W  = [str(i) for i in range(1, 145)]  # 1-144
CODE_5W   = ["A", "B", "C", "D"]
CODE_25K  = ["1", "2", "3", "4"]
CODE_1W   = [str(i) for i in range(1, 65)]   # 1-64
CODE_5K   = ["A", "B", "C", "D"]


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class GeoPoint:
    """单个测量点"""
    def __init__(self, name, B_dec, L_dec):
        self.name  = name
        self.B     = B_dec    # 十进制度纬度
        self.L     = L_dec    # 十进制度经度
        # 各比例尺编号
        self.codes : dict = {}
        # 1:10万图幅四至
        self.boundary_10w : dict = {}
        # 1:5万中心点
        self.center_5w : tuple = (0.0, 0.0)


class TopoResult:
    """汇总结果（30项）"""
    def __init__(self):
        self.points       : list  = []
        self.avg_B        = 0.0
        self.avg_L        = 0.0
        self.max_B_pt     = None
        self.min_B_pt     = None
        self.max_L_pt     = None
        self.min_L_pt     = None
        self.total_points = 0
        self.cross_points = 0   # 跨图幅点数（不同1:100万图幅）
        # 各比例尺图幅总数（在数据范围内）
        self.count_10w    = 0
        self.count_5w     = 0
        self.count_1w     = 0


# ══════════════════════════════════════════════════════════════
#  坐标转换
# ══════════════════════════════════════════════════════════════

def dms_to_dec(dms_str: str) -> float:
    """
    度分秒字符串 → 十进制度（公式3）
    支持：34°45′30″  /  34°45'30"  /  34.5
    """
    s = dms_str.strip()
    # 替换各种符号为统一分隔符
    for ch in ["°", "′", "'", "'", "'"]:
        s = s.replace(ch, " ")
    for ch in ["″", "\"", """]:
        s = s.replace(ch, "")
    parts = s.split()
    deg = float(parts[0]) if len(parts) > 0 else 0.0
    mn  = float(parts[1]) if len(parts) > 1 else 0.0
    sec = float(parts[2]) if len(parts) > 2 else 0.0
    return deg + mn / 60.0 + sec / 3600.0


def dec_to_dms(dec: float) -> str:
    """
    十进制度 → 度分秒字符串（公式3逆）
    返回格式：34°45′30.00″
    """
    d = int(dec)
    rem = (dec - d) * 60.0
    m = int(rem)
    s = (rem - m) * 60.0
    return f"{d}°{m:02d}′{s:05.2f}″"


# ══════════════════════════════════════════════════════════════
#  图幅编号计算
# ══════════════════════════════════════════════════════════════

def code_1m(B: float, L: float) -> str:
    """1:100万图幅编号（公式1）"""
    row = int(B / 4.0)           # 0起
    col = int((L + 180.0) / 6.0) # 列号（从西经180°起算）
    return ROW_LETTERS[row] + str(col)


def code_50w(B: float, L: float) -> str:
    """1:50万：在1:100万内 2行×2列=4格"""
    base = code_1m(B, L)
    B0   = int(B / 4.0) * 4.0    # 1:100万南边界
    L0   = (int(L / 6.0)) * 6.0  # 1:100万西边界
    r = 1 - int((B - B0) / 2.0)  # 0=北，1=南
    c =     int((L - L0) / 3.0)  # 0=西，1=东
    idx = r * 2 + c               # A=0,B=1,C=2,D=3
    return base + CODE_50W[idx]


def code_25w(B: float, L: float) -> str:
    """1:25万：在1:100万内 4行×4列=16格，编号[1]-[16]"""
    base = code_1m(B, L)
    B0   = int(B / 4.0) * 4.0
    L0   = int(L / 6.0) * 6.0
    r = 3 - int((B - B0) / 1.0)  # 从北往南 0-3
    c =     int((L - L0) / 1.5)  # 从西往东 0-3
    idx = r * 4 + c               # 0-15
    return base + CODE_25W[idx]


def code_10w(B: float, L: float) -> str:
    """1:10万：在1:100万内 12行×12列=144格"""
    base = code_1m(B, L)
    B0   = int(B / 4.0) * 4.0
    L0   = int(L / 6.0) * 6.0
    dB   = 20 / 60.0
    dL   = 30 / 60.0
    r = 11 - int((B - B0) / dB)
    c =      int((L - L0) / dL)
    idx = r * 12 + c
    return base + CODE_10W[idx]


def code_5w(B: float, L: float) -> str:
    """1:5万：在1:10万内 2行×2列=4格"""
    base = code_10w(B, L)
    # 1:10万图幅西南角
    B0_1m = int(B / 4.0) * 4.0
    L0_1m = int(L / 6.0) * 6.0
    dB10  = 20 / 60.0
    dL10  = 30 / 60.0
    row10 = 11 - int((B - B0_1m) / dB10)
    col10 =      int((L - L0_1m) / dL10)
    B0_10 = B0_1m + (11 - row10) * dB10
    L0_10 = L0_1m + col10 * dL10
    r = 1 - int((B - B0_10) / (10/60))
    c =     int((L - L0_10) / (15/60))
    idx = r * 2 + c
    return base + CODE_5W[idx]


def code_25k(B: float, L: float) -> str:
    """1:2.5万：在1:5万内 2行×2列=4格"""
    base = code_5w(B, L)
    B0_5w, L0_5w = _sw_corner_5w(B, L)
    r = 1 - int((B - B0_5w) / (5/60))
    c =     int((L - L0_5w) / (7.5/60))
    idx = r * 2 + c
    return base + CODE_25K[idx]


def code_1w(B: float, L: float) -> str:
    """1:1万：在1:10万内 8行×8列=64格"""
    base = code_10w(B, L)
    B0_10, L0_10 = _sw_corner_10w(B, L)
    dB = 2.5 / 60.0
    dL = 3.75 / 60.0
    r = 7 - int((B - B0_10) / dB)
    c =     int((L - L0_10) / dL)
    idx = r * 8 + c
    return base + CODE_1W[idx]


def code_5k(B: float, L: float) -> str:
    """1:5千：在1:1万内 2行×2列=4格"""
    base = code_1w(B, L)
    B0_1w, L0_1w = _sw_corner_1w(B, L)
    r = 1 - int((B - B0_1w) / (1.25/60))
    c =     int((L - L0_1w) / (1.875/60))
    idx = r * 2 + c
    return base + CODE_5K[idx]


# ── 图幅西南角工具函数 ────────────────────────────────────────

def _sw_corner_10w(B: float, L: float):
    B0_1m = int(B / 4.0) * 4.0
    L0_1m = int(L / 6.0) * 6.0
    dB = 20/60; dL = 30/60
    r = 11 - int((B - B0_1m) / dB)
    c =      int((L - L0_1m) / dL)
    return B0_1m + (11-r)*dB, L0_1m + c*dL


def _sw_corner_5w(B: float, L: float):
    B0_10, L0_10 = _sw_corner_10w(B, L)
    dB = 10/60; dL = 15/60
    r = 1 - int((B - B0_10) / dB)
    c =     int((L - L0_10) / dL)
    return B0_10 + (1-r)*dB, L0_10 + c*dL


def _sw_corner_1w(B: float, L: float):
    B0_10, L0_10 = _sw_corner_10w(B, L)
    dB = 2.5/60; dL = 3.75/60
    r = 7 - int((B - B0_10) / dB)
    c =     int((L - L0_10) / dL)
    return B0_10 + (7-r)*dB, L0_10 + c*dL


# ── 1:10万图幅四至 ────────────────────────────────────────────

def boundary_10w(B: float, L: float) -> dict:
    """返回点所在1:10万图幅四至（十进制度）"""
    Bs, Lw = _sw_corner_10w(B, L)
    dB = 20/60; dL = 30/60
    return {
        "南": Bs,
        "北": Bs + dB,
        "西": Lw,
        "东": Lw + dL,
    }


# ══════════════════════════════════════════════════════════════
#  主计算器
# ══════════════════════════════════════════════════════════════

class TopoCalculator:

    def __init__(self):
        self.points : list  = []   # list[GeoPoint]
        self.result  = TopoResult()

    def compute(self):
        res = self.result
        pts = self.points

        for p in pts:
            # 各比例尺编号
            p.codes = {
                "100万":  code_1m(p.B, p.L),
                "50万":   code_50w(p.B, p.L),
                "25万":   code_25w(p.B, p.L),
                "10万":   code_10w(p.B, p.L),
                "5万":    code_5w(p.B, p.L),
                "2.5万":  code_25k(p.B, p.L),
                "1万":    code_1w(p.B, p.L),
                "5千":    code_5k(p.B, p.L),
            }
            # 1:10万四至
            p.boundary_10w = boundary_10w(p.B, p.L)

            # Point2的1:5万图幅中心点
            B0_5w, L0_5w = _sw_corner_5w(p.B, p.L)
            p.center_5w = (B0_5w + 5/60, L0_5w + 7.5/60)

        # 统计
        n = len(pts)
        res.total_points = n
        res.points = pts
        res.avg_B  = sum(p.B for p in pts) / n
        res.avg_L  = sum(p.L for p in pts) / n
        res.max_B_pt = max(pts, key=lambda p: p.B)
        res.min_B_pt = min(pts, key=lambda p: p.B)
        res.max_L_pt = max(pts, key=lambda p: p.L)
        res.min_L_pt = min(pts, key=lambda p: p.L)

        # 各比例尺图幅总数（数据范围内不重复编号数）
        res.count_10w = len(set(p.codes["10万"] for p in pts))
        res.count_5w  = len(set(p.codes["5万"]  for p in pts))
        res.count_1w  = len(set(p.codes["1万"]  for p in pts))

        # 跨图幅点数（不同1:100万图幅）
        codes_1m = [p.codes["100万"] for p in pts]
        majority = max(set(codes_1m), key=codes_1m.count)
        res.cross_points = sum(1 for c in codes_1m if c != majority)
