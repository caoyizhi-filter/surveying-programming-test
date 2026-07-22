# file_io.py
# 文件读写模块 — 读取多历元卫星数据，写出定位结果
# ============================================================

from calculator import Satellite, GNSSSolver
import re


# ============================================================
#  读取输入文件
# ============================================================

def _try_read_lines(filepath: str):
    """尝试多种编码读取文件，返回行列表"""
    for enc in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return [line.strip() for line in f if line.strip()]
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 最后兜底
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return [line.strip() for line in f if line.strip()]


def parse_input(filepath: str):
    """
    读取 Pseudorange Data.txt，返回 (satellites, approx_position, light_speed)

    输入格式:
        APPROX_POSITION: X, Y, Z (m)
        PRN,s:, Satposition(X), ..., Trop Delay(m)   [列标题行]
        Satellite Number: N, GPS time: T
        PRN, X, Y, Z, SatClock, Elevation, CL, TropDelay
        ...
        (多历元重复)
    """
    lines = _try_read_lines(filepath)

    if not lines:
        raise ValueError("输入文件为空")

    approx_position = (0.0, 0.0, 0.0)
    satellites = []
    light_speed = 299792458.0
    current_epoch = 0.0

    for line in lines:
        # ── 近似坐标行 ──
        if 'APPROX' in line.upper() or (
            approx_position == (0.0, 0.0, 0.0) and line.strip().startswith('-')
        ):
            nums = re.findall(r'[-+]?\d+\.?\d*', line)
            if len(nums) >= 3:
                approx_position = (float(nums[0]), float(nums[1]), float(nums[2]))
            continue

        # ── 跳过标题行 ──
        if 'PRN' in line and ('Satposition' in line or 'satposition' in line):
            continue
        if 'PRN' in line and 'CL' in line:
            continue

        # ── 历元头行 ──
        if 'Satellite Number' in line:
            nums = re.findall(r'\d+\.?\d*', line)
            if nums:
                current_epoch = float(nums[-1])
            continue

        # ── 光速行 ──
        if 'Speed of Light' in line or 'speed of light' in line.lower():
            nums = re.findall(r'\d+\.?\d*', line)
            if nums:
                light_speed = float(nums[-1])
            continue

        # ── 卫星数据行 (以G开头) ──
        if line.startswith('G'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 8:
                try:
                    prn = parts[0]
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    sat_clock = float(parts[4])
                    elevation = float(parts[5])
                    cl = float(parts[6])
                    trop_delay = float(parts[7])
                    satellites.append(Satellite(
                        prn=prn, x=x, y=y, z=z,
                        sat_clock=sat_clock, elevation=elevation,
                        cl=cl, trop_delay=trop_delay, epoch=current_epoch
                    ))
                except (ValueError, IndexError):
                    pass

    if not satellites:
        raise ValueError("未读取到卫星数据")

    return satellites, approx_position, light_speed


# ============================================================
#  写出结果文件
# ============================================================

def write_result(filepath: str, solver: GNSSSolver):
    """
    按试题册格式写出 6 项结果

    输出格式 (result5.txt):
        序号,说明,计算结果
        1,接收机X,<Xr:.3f>
        2,接收机Y,<Yr:.3f>
        3,接收机Z,<Zr:.3f>
        4,迭代次数,<iterations>
        5,单位权方差,<unit_variance:.6f>
        6,PDOP值,<PDOP:.6f>
    """
    rows = [
        (1, "接收机X",       f"{solver.Xr:.3f}"),
        (2, "接收机Y",       f"{solver.Yr:.3f}"),
        (3, "接收机Z",       f"{solver.Zr:.3f}"),
        (4, "迭代次数",      str(solver.iterations)),
        (5, "单位权方差",    f"{solver.unit_variance:.6f}"),
        (6, "PDOP值",        f"{solver.PDOP:.6f}"),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,说明,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
