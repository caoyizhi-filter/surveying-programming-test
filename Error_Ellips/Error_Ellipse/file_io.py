# file_io.py
# 读取 ellipse.txt，输出 ellipse_result.txt


from calculator import Point


def read_input(filepath: str) -> list:
    """
    读取 ellipse.txt
    每行格式：点号,Qxx,Qyy,Qxy,μ
    返回 Point 列表
    """
    points = []
    with open(filepath, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) != 5:
                raise ValueError(f"第{lineno}行格式错误，需要5列：{line}")
            name = parts[0].strip()
            Qxx  = float(parts[1])
            Qyy  = float(parts[2])
            Qxy  = float(parts[3])
            mu   = float(parts[4])
            points.append(Point(name, Qxx, Qyy, Qxy, mu))
    return points


def write_output(filepath: str, points: list, stat: dict):
    """
    输出 ellipse_result.txt
    格式：序号,说明,计算结果（共30行）
    """
    rows = []

    # P1（序号1-12）和 P2（序号13-24）各12项
    for p in points[:2]:
        rows.append((f"{p.name}的σxx",      f"{p.sigma_xx:.6f}"))
        rows.append((f"{p.name}的σyy",      f"{p.sigma_yy:.6f}"))
        rows.append((f"{p.name}的σxy",      f"{p.sigma_xy:.6f}"))
        rows.append((f"{p.name}长半轴E",     f"{p.E:.6f}"))
        rows.append((f"{p.name}短半轴F",     f"{p.F:.6f}"))
        rows.append((f"{p.name}方位角φ_E",   f"{p.phi_E:.4f}"))
        rows.append((f"{p.name} σ(0°)",     f"{p.sigma_0:.6f}"))
        rows.append((f"{p.name} σ(45°)",    f"{p.sigma_45:.6f}"))
        rows.append((f"{p.name} σ(90°)",    f"{p.sigma_90:.6f}"))
        rows.append((f"{p.name} σ(135°)",   f"{p.sigma_135:.6f}"))
        rows.append((f"{p.name} σ(180°)",   f"{p.sigma_180:.6f}"))
        rows.append((f"{p.name}是否异常",    str(p.anomaly)))

    # 汇总（序号25-30）
    rows.append(("E平均值",        f"{stat['avg_E']:.6f}"))
    rows.append(("F平均值",        f"{stat['avg_F']:.6f}"))
    rows.append(("异常点数",       str(stat['anomaly_count'])))
    rows.append(("正常点数",       str(stat['normal_count'])))
    rows.append(("总点数",         str(stat['total_count'])))
    rows.append(("点位平均方位角φ_E", f"{stat['avg_phi_E']:.4f}"))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,说明,计算结果\n")
        for i, (label, value) in enumerate(rows, 1):
            f.write(f"{i},{label},{value}\n")
