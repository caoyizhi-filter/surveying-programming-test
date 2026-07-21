# file_io.py
# 大地主题正反算 — 文件读写
# 读取 geodetic_*_input.txt，写出 geodetic_result.txt

import re
from calculator import Ellipsoid


# ══════════════════════════════════════════════════════════════
#  解析输入文件
# ══════════════════════════════════════════════════════════════

def parse_input(filepath: str) -> dict:
    """
    解析输入文件，自动识别正算/反算模式。

    返回: {
        'ellipsoid': (a, inv_f),
        'tasks': [{'mode': 1|2, 'params': [数值列表]}]
    }

    自动识别规则：
      - 正算格式: P1,B1,L1,A12,S,P2  (P2在第6位, index 5)
      - 反算格式: P1,B1,L1,P2,B2,L2  (P2在第4位, index 3)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        raise ValueError("输入文件至少需要2行: 椭球参数 + 数据行")

    # 第一行: a, 1/f
    ell_parts = lines[0].split(',')
    if len(ell_parts) < 2:
        raise ValueError(f"椭球参数行格式错误: {lines[0]}")
    ellipsoid = (float(ell_parts[0]), float(ell_parts[1]))

    # 后续行: 提取浮点数 + 自动识别模式
    tasks = []
    for line in lines[1:]:
        # 按逗号分割
        tokens = [t.strip() for t in line.split(',')]

        # 过滤标记字符, 仅保留数值
        numbers = []
        for t in tokens:
            try:
                numbers.append(float(t))
            except ValueError:
                pass  # 跳过 P1, P2 等非数值标记

        if len(numbers) < 4:
            raise ValueError(f"数据行数值不足(期望≥4): {line}")

        # 自动识别模式: 查找 P2 标记位置
        mode = _detect_mode(tokens)

        tasks.append({'mode': mode, 'params': numbers})

    return {'ellipsoid': ellipsoid, 'tasks': tasks}


def _detect_mode(tokens: list) -> int:
    """
    通过 P2 标记位置判断模式。
    - P2 在 tokens 后半段(index>=3) → tokens中第4个 → 反算格式 → mode=2
    - P2 在 tokens 末尾(index>=5) → tokens中第6个 → 正算格式 → mode=1
    """
    p2_indices = [i for i, t in enumerate(tokens)
                  if t.strip().upper() == 'P2']
    if p2_indices:
        p2_idx = p2_indices[0]
        if p2_idx >= 5:          # P2在末尾, 正算: P1,B1,L1,A12,S,P2
            return 1
        elif p2_idx <= 3:        # P2在中间, 反算: P1,B1,L1,P2,B2,L2
            return 2
    # 回退: 若找不到P2, 用数值个数判断(不推荐但作为容错)
    return 1  # 默认正算


# ══════════════════════════════════════════════════════════════
#  写出结果文件
# ══════════════════════════════════════════════════════════════

def write_result_direct(filepath: str, B1: float, L1: float, A12: float,
                        S: float, B2: float, L2: float, A21: float,
                        iterations: int):
    """正算结果 → 9 项输出"""
    rows = [
        (1,  "计算模式标志",              "1"),
        (2,  "起点纬度B1",                f"{B1:.6f}"),
        (3,  "起点经度L1",                f"{L1:.6f}"),
        (4,  "起始大地方位角A12",          f"{A12:.6f}"),
        (5,  "大地线长度S",               f"{S:.3f}"),
        (6,  "终点纬度B2",                f"{B2:.6f}"),
        (7,  "终点经度L2",                f"{L2:.6f}"),
        (8,  "终点反方位角A21",            f"{A21:.6f}"),
        (9,  "迭代总次数",                f"{iterations}"),
    ]
    _write_rows(filepath, rows)


def write_result_inverse(filepath: str, B1: float, L1: float,
                         B2: float, L2: float,
                         S: float, A12: float, A21: float,
                         iterations: int):
    """反算结果 → 9 项输出"""
    rows = [
        (1,  "计算模式标志",              "2"),
        (2,  "起点纬度B1",                f"{B1:.6f}"),
        (3,  "起点经度L1",                f"{L1:.6f}"),
        (4,  "终点纬度B2",                f"{B2:.6f}"),
        (5,  "终点经度L2",                f"{L2:.6f}"),
        (6,  "大地线长度S",               f"{S:.3f}"),
        (7,  "正方位角A12",               f"{A12:.6f}"),
        (8,  "反方位角A21",               f"{A21:.6f}"),
        (9,  "迭代总次数",                f"{iterations}"),
    ]
    _write_rows(filepath, rows)


def _write_rows(filepath: str, rows: list):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("序号,指标名称,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
