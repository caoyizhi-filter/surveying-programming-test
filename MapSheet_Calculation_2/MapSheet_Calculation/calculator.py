# calculator.py
# 地形图图幅编号计算（老编号 + 新编号）
# 仅使用 Python 标准库 math

import math


# ══════════════════════════════════════════════════════════════
#  各比例尺参数
#  (纬差°, 经差°, 在1:100万内行数, 在1:100万内列数)
# ══════════════════════════════════════════════════════════════
#  注：1:100万本身作为基准，行列各1
SCALE_INFO = {
    "100万": (4.0,        6.0,       1,   1),
    "50万":  (2.0,        3.0,       2,   2),
    "25万":  (1.0,        1.5,       4,   4),
    "10万":  (20/60,      30/60,    12,  12),
    "5万":   (10/60,      15/60,    24,  24),
    "1万":   (2.5/60,     3.75/60,  96,  96),
}

# 老编号分幅代码
ROW_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"   # 1:100万纬度行号

# 各比例尺在上级图幅内的老编号代码
OLD_CODE_50W  = ["A", "B", "C", "D"]                     # 2×2
OLD_CODE_25W  = [f"[{i}]" for i in range(1, 17)]         # 4×4 → [1]~[16]
OLD_CODE_10W  = [str(i) for i in range(1, 145)]          # 12×12 → 1~144
OLD_CODE_5W   = ["A", "B", "C", "D"]                     # 2×2
OLD_CODE_1W   = [str(i) for i in range(1, 65)]           # 8×8 → 1~64


# ══════════════════════════════════════════════════════════════
#  十进制 → 度分秒 转换（用于输出）
# ══════════════════════════════════════════════════════════════

def decimal_to_dms(deg: float) -> str:
    """
    将十进制度数转换为度分秒字符串，秒四舍五入取整。
    例如：34.7583333333 → "34°45′30″"
    """
    sign = '-' if deg < 0 else ''
    deg = abs(deg)
    d = int(deg)
    minutes = (deg - d) * 60
    m = int(minutes)
    s = (minutes - m) * 60
    # 秒四舍五入，避免 59.999 显示为 60
    s_rounded = round(s)
    if s_rounded == 60:
        s_rounded = 0
        m += 1
        if m == 60:
            m = 0
            d += 1
    return f"{sign}{d}°{m}′{s_rounded}″"


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class GeoPoint:
    def __init__(self, name, B, L):
        self.name = name
        self.B    = B      # 十进制度纬度
        self.L    = L      # 十进制度经度

        # 各比例尺老编号、新编号
        self.old_codes : dict = {}
        self.new_codes : dict = {}

        # 1:10万图幅西南角
        self.sw_lat_10w = 0.0
        self.sw_lon_10w = 0.0


class TopoResult:
    def __init__(self):
        self.points : list = []


# ══════════════════════════════════════════════════════════════
#  1:100万图幅行列号（基础）
# ══════════════════════════════════════════════════════════════

def sheet_1m_row_col(B: float, L: float):
    """
    返回1:100万图幅行号(0起)和列号(0起)
    行号：从赤道起每4°一行，0=A
    列号：从180°W起每6°一列，0=第1列
    """
    row = int(B / 4.0)
    col = int((L + 180.0) / 6.0)   # 从-180°起算
    return row, col


def old_code_1m(B: float, L: float) -> str:
    """1:100万老编号，如 J-50"""
    row, col = sheet_1m_row_col(B, L)
    return f"{ROW_LETTERS[row]}-{col + 1}"


def new_code_1m(B: float, L: float) -> str:
    """1:100万新编号，如 J50（无连字符）"""
    row, col = sheet_1m_row_col(B, L)
    return f"{ROW_LETTERS[row]}{col + 1:02d}"


# ══════════════════════════════════════════════════════════════
#  各比例尺图幅西南角
# ══════════════════════════════════════════════════════════════

def sw_corner(B: float, L: float, dB: float, dL: float):
    """返回点所在图幅的西南角（纬度，经度）"""
    Bs = math.floor(B / dB) * dB
    Lw = math.floor(L / dL) * dL
    return Bs, Lw


# ══════════════════════════════════════════════════════════════
#  老编号计算
# ══════════════════════════════════════════════════════════════

def _local_index(B, L, dB, dL, rows_in_parent, cols_in_parent,
                 parent_dB, parent_dL):
    """
    在上级图幅内的本级行列索引（从左上角，行从上往下，列从左往右）
    返回 (row_idx, col_idx)，均从0起
    """
    # 上级图幅西南角
    Bs_p = math.floor(B / parent_dB) * parent_dB
    Lw_p = math.floor(L / parent_dL) * parent_dL
    # 在上级内的偏移
    row_from_south = int((B - Bs_p) / dB)
    col_from_west  = int((L - Lw_p) / dL)
    # 行号从上往下（0=最北行）
    row_from_north = rows_in_parent - 1 - row_from_south
    return row_from_north, col_from_west


def old_code_50w(B: float, L: float) -> str:
    r, c = _local_index(B, L, 2.0, 3.0, 2, 2, 4.0, 6.0)
    idx  = r * 2 + c
    return old_code_1m(B, L) + "-" + OLD_CODE_50W[idx]


def old_code_25w(B: float, L: float) -> str:
    r, c = _local_index(B, L, 1.0, 1.5, 4, 4, 4.0, 6.0)
    idx  = r * 4 + c
    return old_code_1m(B, L) + "-" + OLD_CODE_25W[idx]


def old_code_10w(B: float, L: float) -> str:
    r, c = _local_index(B, L, 20/60, 30/60, 12, 12, 4.0, 6.0)
    idx  = r * 12 + c
    return old_code_1m(B, L) + "-" + OLD_CODE_10W[idx]


def old_code_5w(B: float, L: float) -> str:
    # 1:5万在1:10万内 2×2
    base_10w = old_code_10w(B, L)
    # 取1:10万西南角
    Bs_10 = math.floor(B / (20/60)) * (20/60)
    Lw_10 = math.floor(L / (30/60)) * (30/60)
    r = 1 - int((B - Bs_10) / (10/60))
    c =     int((L - Lw_10) / (15/60))
    idx = r * 2 + c
    return base_10w + "-" + OLD_CODE_5W[idx]


def old_code_1w(B: float, L: float) -> str:
    # 1:1万在1:10万内 8×8
    base_10w = old_code_10w(B, L)
    Bs_10 = math.floor(B / (20/60)) * (20/60)
    Lw_10 = math.floor(L / (30/60)) * (30/60)
    r = 7 - int((B - Bs_10) / (2.5/60))
    c =     int((L - Lw_10) / (3.75/60))
    idx = r * 8 + c
    return base_10w + "-" + OLD_CODE_1W[idx]


# ══════════════════════════════════════════════════════════════
#  新编号计算（数字式：行列各3位，格式 Letter+列号+行代码+列代码）
#  国标新编号：比例尺代码 + 图幅行列（6位）
#  格式：行字母 + 两位列号 + 比例尺代码 + 三位行编号 + 三位列编号
# ══════════════════════════════════════════════════════════════

# 新编号中的比例尺代码
NEW_SCALE_CODE = {
    "100万": "",     # 无代码
    "50万":  "C",
    "25万":  "D",
    "10万":  "E",
    "5万":   "F",
    "1万":   "G",
}


def new_code(B: float, L: float, scale: str) -> str:
    """
    新编号格式（国家标准）：
    行字母 + 两位列号 + 比例尺代码 + 三位行编号 + 三位列编号
    例：J50E003004
    """
    row_1m, col_1m = sheet_1m_row_col(B, L)
    base = f"{ROW_LETTERS[row_1m]}{col_1m + 1:02d}"

    if scale == "100万":
        return base

    dB_map = {"50万": 2.0, "25万": 1.0, "10万": 20/60,
              "5万": 10/60, "1万": 2.5/60}
    dL_map = {"50万": 3.0, "25万": 1.5, "10万": 30/60,
              "5万": 15/60, "1万": 3.75/60}
    rows_map = {"50万": 2, "25万": 4, "10万": 12, "5万": 24, "1万": 96}
    cols_map = {"50万": 2, "25万": 4, "10万": 12, "5万": 24, "1万": 96}

    dB   = dB_map[scale]
    dL   = dL_map[scale]
    rows = rows_map[scale]
    cols = cols_map[scale]

    # 在1:100万内的行列位置（从左上角，1起）
    B0_1m = row_1m * 4.0
    L0_1m = (col_1m) * 6.0 - 180.0
    row_from_south = int((B - B0_1m) / dB)
    col_from_west  = int((L - L0_1m) / dL)
    row_from_north = rows - row_from_south   # 从北往南，1起
    col_no         = col_from_west + 1       # 从西往东，1起

    code = NEW_SCALE_CODE[scale]
    return f"{base}{code}{row_from_north:03d}{col_no:03d}"


# ══════════════════════════════════════════════════════════════
#  主计算器
# ══════════════════════════════════════════════════════════════

class TopoCalculator:

    def __init__(self):
        self.points : list  = []
        self.result  = TopoResult()

    def compute(self):
        for p in self.points:
            # 老编号
            p.old_codes = {
                "100万": old_code_1m(p.B, p.L),
                "50万":  old_code_50w(p.B, p.L),
                "25万":  old_code_25w(p.B, p.L),
                "10万":  old_code_10w(p.B, p.L),
                "5万":   old_code_5w(p.B, p.L),
                "1万":   old_code_1w(p.B, p.L),
            }
            # 新编号
            p.new_codes = {
                "100万": new_code(p.B, p.L, "100万"),
                "50万":  new_code(p.B, p.L, "50万"),
                "25万":  new_code(p.B, p.L, "25万"),
                "10万":  new_code(p.B, p.L, "10万"),
                "5万":   new_code(p.B, p.L, "5万"),
                "1万":   new_code(p.B, p.L, "1万"),
            }
            # 1:10万图幅西南角
            p.sw_lat_10w, p.sw_lon_10w = sw_corner(
                p.B, p.L, 20/60, 30/60
            )

        self.result.points = self.points