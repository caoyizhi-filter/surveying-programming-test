# file_io.py
# 读取 Point.txt（正式数据），输出 result.txt（分割结果）

from calculator import Point, PointCloudProcessor


# ══════════════════════════════════════════════════════════════
#  读取输入文件
# ══════════════════════════════════════════════════════════════

def read_points(filepath: str) -> list:
    """
    解析 Point.txt
    第1行: 点云数量
    后续行: 点名,x,y,z
    """
    points = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        raise ValueError("输入文件为空")

    count = int(lines[0].strip())
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) < 4:
            continue
        name = parts[0].strip()
        x = float(parts[1])
        y = float(parts[2])
        z = float(parts[3])
        points.append(Point(name, x, y, z))

    if len(points) != count:
        raise ValueError(f"点数不匹配: 期望 {count}, 实际读取 {len(points)}")

    return points


# ══════════════════════════════════════════════════════════════
#  写出结果文件
# ══════════════════════════════════════════════════════════════

def write_result(filepath: str, processor: PointCloudProcessor):
    """
    按试题册格式输出 result.txt
    格式: 点名,X,Y,Z,标识
    X,Y,Z 保留 3 位小数
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("点名,X,Y,Z,标识\n")
        for p in processor.points:
            label = processor.get_label(p)
            f.write(f"{p.name},{p.x:.3f},{p.y:.3f},{p.z:.3f},{label}\n")
