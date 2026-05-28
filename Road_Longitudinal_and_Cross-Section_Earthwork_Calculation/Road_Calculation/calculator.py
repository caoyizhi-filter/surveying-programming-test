# calculator.py

def parse_stake(stake_str):
    """
    解析桩号字符串（如 '0+100'、'0+000' 或 '44.000'），将其转换为浮点数。
    """
    stake_str = stake_str.strip()
    if '+' in stake_str:
        parts = stake_str.split('+')
        return float(parts[0]) * 1000 + float(parts[1])
    else:
        return float(stake_str)

class Section:
    def __init__(self, stake_str, design_elev, point_count, points):
        self.stake_str = stake_str
        self.stake = parse_stake(stake_str)
        self.design_elev = design_elev
        self.point_count = point_count
        # 将断面测点按距离d从小到大进行排序，以确保梯形法计算的顺序正确
        self.points = sorted(points, key=lambda x: x[0])

    def calculate_ground_elevation_at_center(self):
        """
        计算中桩（d = 0）处的地面高程。
        如果点集中不正好包含 d = 0，则通过其左右相邻两个测量点线性插值计算高程偏差。
        """
        if not self.points:
            return self.design_elev

        # 检查是否有正好在 0 位置的测点
        for d, dev in self.points:
            if abs(d) < 1e-6:
                return self.design_elev + dev

        # 线性插值计算 d = 0 处的高程偏差
        for i in range(len(self.points) - 1):
            d1, dev1 = self.points[i]
            d2, dev2 = self.points[i+1]
            if d1 <= 0.0 <= d2:
                dev0 = dev1 + (0.0 - d1) / (d2 - d1) * (dev2 - dev1)
                return self.design_elev + dev0

        # 如果所有测点在同侧，作为备用方案取距离 0 最近的点偏差
        closest_point = min(self.points, key=lambda x: abs(x[0]))
        return self.design_elev + closest_point[1]

    def calculate_fill_area(self):
        """
        利用横断面面积梯形公式计算横断面填方面积。
        计算公式：A = ∑ [ (h_i + h_{i+1}) * (d_{i+1} - d_i) / 2 ]
        对于填方，高程偏差为负，对应的填高 h_i = |dev_i|。
        """
        area = 0.0
        for i in range(len(self.points) - 1):
            d1, dev1 = self.points[i]
            d2, dev2 = self.points[i+1]
            h1 = abs(dev1)
            h2 = abs(dev2)
            area += (h1 + h2) * (d2 - d1) / 2.0
        return area


def calculate_earthwork(sections, query_stake):
    """
    区间土方计算逻辑核心。
    计算并输出地面高程、填方面积、两断面间距、区间土方总量、第一断面测点总数、以及插值出的设计高程。
    """
    if len(sections) < 2:
        raise ValueError("输入数据无法构成至少两个断面的有效计算区间。")

    sec1 = sections[0]
    sec2 = sections[1]

    # 1 & 2. 断面地面高程
    sec1_ground = sec1.calculate_ground_elevation_at_center()
    sec2_ground = sec2.calculate_ground_elevation_at_center()

    # 3 & 4. 断面填方面积
    sec1_area = sec1.calculate_fill_area()
    sec2_area = sec2.calculate_fill_area()

    # 5. 两断面间距
    distance = abs(sec2.stake - sec1.stake)

    # 6. 区间土方总量（平均断面法公式）
    total_volume = ((sec1_area + sec2_area) / 2.0) * distance

    # 7. 断面1测点总数
    sec1_points_count = sec1.point_count

    # 8. 插值计算查询里程处的设计路面高程
    if distance > 0:
        query_design_elev = sec1.design_elev + (query_stake - sec1.stake) / (sec2.stake - sec1.stake) * (sec2.design_elev - sec1.design_elev)
    else:
        query_design_elev = sec1.design_elev

    return {
        'sec1_ground_elev': sec1_ground,
        'sec2_ground_elev': sec2_ground,
        'sec1_area': sec1_area,
        'sec2_area': sec2_area,
        'distance': distance,
        'total_volume': total_volume,
        'sec1_points_count': sec1_points_count,
        'query_design_elev': query_design_elev
    }