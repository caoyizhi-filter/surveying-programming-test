# file_io.py
# 读取 bhl1.txt（外方位元素）与 data.txt（同名像点）
# 输出 intersection_result.txt（41项）

from calculator import (
    ExteriorOrientation, ImagePointPair,
    SpaceIntersectionCalculator
)


def read_eo(filepath: str):
    """
    读取 bhl1.txt（18 行浮点数）。
    前 9 行 = 左片，后 9 行 = 右片。
    返回 (left_eo, right_eo)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        vals = []
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                vals.append(float(line))
            except ValueError:
                continue

    if len(vals) < 18:
        raise ValueError(f"bhl1.txt 数据不足：需 18 行，实际读取 {len(vals)} 行")

    left = ExteriorOrientation(*vals[0:9])
    right = ExteriorOrientation(*vals[9:18])
    return left, right


def read_image_points(filepath: str):
    """
    读取同名像点文件（12 行，每行 x1,y1,x2,y2）。
    也兼容 9 列格式（取前 4 列作为 x1,y1,x2,y2）。
    返回 list[ImagePointPair]
    """
    pairs = []
    with open(filepath, "r", encoding="utf-8") as f:
        idx = 1
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) < 4:
                continue
            try:
                x1 = float(parts[0].strip())
                y1 = float(parts[1].strip())
                x2 = float(parts[2].strip())
                y2 = float(parts[3].strip())
            except ValueError:
                continue
            pairs.append(ImagePointPair(idx, x1, y1, x2, y2))
            idx += 1

    if not pairs:
        raise ValueError("data.txt 为空或格式错误，需 x1,y1,x2,y2 逗号分隔格式")
    return pairs


def write_result(filepath: str, calc: SpaceIntersectionCalculator):
    """
    输出 intersection_result.txt（41项）。
    """
    res  = calc.result
    L    = res.left_eo
    R    = res.right_eo
    pair = res.pairs[0]  # 第 1 组

    rows = [
        (1,  "左片摄影中心Xs1",      f"{L.Xs:.6f}"),
        (2,  "左片摄影中心Ys1",      f"{L.Ys:.6f}"),
        (3,  "左片摄影中心Zs1",      f"{L.Zs:.6f}"),
        (4,  "左片角元素φ1",         f"{L.phi:.6f}"),
        (5,  "左片角元素ω1",         f"{L.omega:.6f}"),
        (6,  "左片角元素κ1",         f"{L.kappa:.6f}"),
        (7,  "左片主距f1",           f"{L.f:.6f}"),
        (8,  "左片像主点x01",        f"{L.x0:.6f}"),
        (9,  "左片像主点y01",        f"{L.y0:.6f}"),
        (10, "右片摄影中心Xs2",      f"{R.Xs:.6f}"),
        (11, "右片摄影中心Ys2",      f"{R.Ys:.6f}"),
        (12, "右片摄影中心Zs2",      f"{R.Zs:.6f}"),
        (13, "右片角元素φ2",         f"{R.phi:.6f}"),
        (14, "右片角元素ω2",         f"{R.omega:.6f}"),
        (15, "右片角元素κ2",         f"{R.kappa:.6f}"),
        (16, "右片主距f2",           f"{R.f:.6f}"),
        (17, "右片像主点x02",        f"{R.x0:.6f}"),
        (18, "右片像主点y02",        f"{R.y0:.6f}"),
        (19, "基线分量BX",            f"{res.BX:.6f}"),
        (20, "基线分量BY",            f"{res.BY:.6f}"),
        (21, "基线分量BZ",            f"{res.BZ:.6f}"),
        (22, "第1组像点左片标准化x1̄", f"{pair.x1_bar:.6f}"),
        (23, "第1组像点左片标准化ȳ1̄", f"{pair.y1_bar:.6f}"),
        (24, "第1组像点右片标准化x2̄", f"{pair.x2_bar:.6f}"),
        (25, "第1组像点右片标准化ȳ2̄", f"{pair.y2_bar:.6f}"),
        (26, "第1组左片像空间辅助X1", f"{pair.U1:.6f}"),
        (27, "第1组左片像空间辅助Y1", f"{pair.V1:.6f}"),
        (28, "第1组左片像空间辅助Z1", f"{pair.W1:.6f}"),
        (29, "第1组右片像空间辅助X2", f"{pair.U2:.6f}"),
        (30, "第1组右片像空间辅助Y2", f"{pair.V2:.6f}"),
        (31, "第1组右片像空间辅助Z2", f"{pair.W2:.6f}"),
        (32, "第1组投影系数N1",       f"{pair.N1:.6f}"),
        (33, "第1组投影系数N2",       f"{pair.N2:.6f}"),
        (34, "第1点地面摄影测量X坐标", f"{pair.X:.6f}"),
        (35, "第1点地面摄影测量Y坐标", f"{pair.Y:.6f}"),
        (36, "第1点地面摄影测量Z坐标", f"{pair.Z:.6f}"),
        (37, "12个地面点X坐标平均值",  f"{res.avg_X:.6f}"),
        (38, "12个地面点Y坐标平均值",  f"{res.avg_Y:.6f}"),
        (39, "12个地面点Z坐标平均值",  f"{res.avg_Z:.6f}"),
        (40, "全部地面点Z坐标最大值",  f"{res.max_Z:.6f}"),
        (41, "全部地面点Z坐标最小值",  f"{res.min_Z:.6f}"),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,指标名称,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
