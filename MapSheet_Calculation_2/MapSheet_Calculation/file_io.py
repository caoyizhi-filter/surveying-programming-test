# file_io.py
# 读取 map.txt（支持十进制度或度分秒格式），输出 map_result.txt（30项，坐标以度分秒显示）

import re
from calculator import GeoPoint, TopoCalculator, decimal_to_dms


# ══════════════════════════════════════════════════════════════
#  度分秒 → 十进制度 转换函数
# ══════════════════════════════════════════════════════════════

def dms_to_decimal(dms_str: str) -> float:
    """
    将度分秒字符串转换为十进制度数。
    支持的格式示例：
        "34°45′30″"  或  "34°45'30\""  或  "34度45分30秒"
        "34°45.5′"   (度分) 或  "34.5°"   (度)
    也允许包含北纬/东经等符号（如 N34°45′30″E），但会自动忽略字母。
    """
    # 去除首尾空白，并替换中文标点为英文兼容形式
    s = dms_str.strip()
    # 统一替换常见度分秒符号
    s = s.replace('°', '°').replace('′', "'").replace('″', '"')
    s = s.replace('度', '°').replace('分', "'").replace('秒', '"')
    
    # 提取数字和符号
    # 正则：匹配数字(可能带小数点) + 可选度分秒符号
    # 简单方法：提取所有浮点数
    nums = re.findall(r"(\d+(?:\.\d+)?)", s)
    if not nums:
        raise ValueError(f"无法从字符串中提取数字：{dms_str}")
    
    # 判断是否存在度分秒符号
    has_deg = '°' in s
    has_min = "'" in s or '′' in s
    has_sec = '"' in s or '″' in s
    
    if has_deg:
        deg = float(nums[0])
        if has_min:
            minute = float(nums[1]) if len(nums) > 1 else 0.0
        else:
            minute = 0.0
        if has_sec:
            second = float(nums[2]) if len(nums) > 2 else 0.0
        else:
            second = 0.0
        # 处理小数点分的情况，比如 34°45.5' -> 45.5分
        if '.' in s and has_min and not has_sec:
            # 如果第二个数字有小数点且没有秒，则视为带小数的分
            minute = float(nums[1])
            second = 0.0
        return deg + minute / 60.0 + second / 3600.0
    else:
        # 纯数字，视为已是十进制度
        return float(nums[0])


# ══════════════════════════════════════════════════════════════
#  读取输入文件（自动兼容十进制度与度分秒）
# ══════════════════════════════════════════════════════════════

def read_input(filepath: str) -> TopoCalculator:
    """
    解析 map.txt
    格式：点号,纬度,经度
    纬度/经度支持：
        - 十进制度，例：30.5
        - 度分秒，例：34°45′30″ 或 34°45'30" 或 34度45分30秒
    例：
        Point1,30.5,114.2
        Point2,34°45′30″,113°30′15″
    """
    calc = TopoCalculator()
    with open(filepath, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) != 3:
                raise ValueError(f"第{lineno}行格式错误（需3列）：{line}")
            name = parts[0].strip()
            B_str = parts[1].strip()
            L_str = parts[2].strip()

            # 转换为十进制度
            try:
                # 先尝试作为十进制度浮点数解析
                B = float(B_str)
            except ValueError:
                # 失败则作为度分秒解析
                B = dms_to_decimal(B_str)

            try:
                L = float(L_str)
            except ValueError:
                L = dms_to_decimal(L_str)

            calc.points.append(GeoPoint(name, B, L))

    if not calc.points:
        raise ValueError("文件为空或格式错误")
    return calc


# ══════════════════════════════════════════════════════════════
#  写出结果文件（30项，坐标以度分秒显示）
# ══════════════════════════════════════════════════════════════

def write_result(filepath: str, calc: TopoCalculator):
    res = calc.result
    p1  = res.points[0]
    p2  = res.points[1]

    # 转换函数
    def fmt(deg): return decimal_to_dms(deg)
    def fmt_sw(deg): return decimal_to_dms(deg)

    rows = [
        (1,  "Point1纬度B",              fmt(p1.B)),
        (2,  "Point1经度L",              fmt(p1.L)),
        (3,  "Point1_1:100万_老编号",    p1.old_codes["100万"]),
        (4,  "Point1_1:100万_新编号",    p1.new_codes["100万"]),
        (5,  "Point1_1:50万_老编号",     p1.old_codes["50万"]),
        (6,  "Point1_1:50万_新编号",     p1.new_codes["50万"]),
        (7,  "Point1_1:25万_老编号",     p1.old_codes["25万"]),
        (8,  "Point1_1:25万_新编号",     p1.new_codes["25万"]),
        (9,  "Point1_1:10万_老编号",     p1.old_codes["10万"]),
        (10, "Point1_1:10万_新编号",     p1.new_codes["10万"]),
        (11, "Point1_1:5万_老编号",      p1.old_codes["5万"]),
        (12, "Point1_1:5万_新编号",      p1.new_codes["5万"]),
        (13, "Point1_1:1万_老编号",      p1.old_codes["1万"]),
        (14, "Point1_1:1万_新编号",      p1.new_codes["1万"]),
        (15, "Point1图幅西南角纬度",     fmt_sw(p1.sw_lat_10w)),
        (16, "Point1图幅西南角经度",     fmt_sw(p1.sw_lon_10w)),
        (17, "Point2纬度B",              fmt(p2.B)),
        (18, "Point2经度L",              fmt(p2.L)),
        (19, "Point2_1:100万_老编号",    p2.old_codes["100万"]),
        (20, "Point2_1:100万_新编号",    p2.new_codes["100万"]),
        (21, "Point2_1:50万_老编号",     p2.old_codes["50万"]),
        (22, "Point2_1:50万_新编号",     p2.new_codes["50万"]),
        (23, "Point2_1:25万_老编号",     p2.old_codes["25万"]),
        (24, "Point2_1:25万_新编号",     p2.new_codes["25万"]),
        (25, "Point2_1:10万_老编号",     p2.old_codes["10万"]),
        (26, "Point2_1:10万_新编号",     p2.new_codes["10万"]),
        (27, "Point2_1:5万_老编号",      p2.old_codes["5万"]),
        (28, "Point2_1:5万_新编号",      p2.new_codes["5万"]),
        (29, "Point2_1:1万_老编号",      p2.old_codes["1万"]),
        (30, "Point2_1:1万_新编号",      p2.new_codes["1万"]),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,说明,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")