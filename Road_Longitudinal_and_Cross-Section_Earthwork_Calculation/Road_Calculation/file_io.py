# file_io.py
from calculator import Section, parse_stake

def read_input_file(filepath):
    """
    根据给定的行文本结构读取断面输入数据文件。
    """
    sections = []
    query_stake = None

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('//') or line.startswith('#'):
            i += 1
            continue

        # 解析到最后剩余一个有效实数行，则为查询里程
        if len(sections) == 2:
            query_stake = parse_stake(line)
            break

        parts = line.split()
        if len(parts) >= 3:
            stake_str = parts[0]
            design_elev = float(parts[1])
            point_count = int(parts[2])

            points = []
            points_read = 0
            i += 1
            while i < len(lines) and points_read < point_count:
                pt_line = lines[i].strip()
                if not pt_line or pt_line.startswith('//') or pt_line.startswith('#'):
                    i += 1
                    continue
                pt_parts = pt_line.split()
                if len(pt_parts) >= 2:
                    d = float(pt_parts[0])
                    dev = float(pt_parts[1])
                    points.append((d, dev))
                    points_read += 1
                i += 1
            sections.append(Section(stake_str, design_elev, point_count, points))
        else:
            i += 1

    return sections, query_stake


def write_result_file(filepath, results):
    """
    将计算结果按输出规范格式写入结果文件。
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("序号,说明,计算结果\n")
        f.write(f"1,断面 1 高程,{results['sec1_ground_elev']:.2f}\n")
        f.write(f"2,断面 2 高程,{results['sec2_ground_elev']:.2f}\n")
        f.write(f"3,断面 1 面积,{results['sec1_area']:.2f}\n")
        f.write(f"4,断面 2 面积,{results['sec2_area']:.2f}\n")
        f.write(f"5,间距,{int(results['distance'])}\n")
        f.write(f"6,土方总量,{results['total_volume']:.2f}\n")
        f.write(f"7,测点总数,{int(results['sec1_points_count'])}\n")
        f.write(f"8,设计高程,{results['query_design_elev']:.2f}\n")