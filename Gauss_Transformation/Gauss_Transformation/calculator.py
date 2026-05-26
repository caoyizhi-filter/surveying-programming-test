import math

class GaussCalculator:
    # 常用参考椭球参数: (半长轴 a, 扁率倒数 1/f)
    ELLIPSOIDS = {
        "CGCS2000": (6378137.0, 298.257222101),
        "WGS84": (6378137.0, 298.257223563),
        "Xi'an 80": (6378140.0, 298.257),
        "Beijing 54": (6378245.0, 298.3)
    }

    def __init__(self, ellipsoid_name="CGCS2000"):
        self.set_ellipsoid(ellipsoid_name)

    def set_ellipsoid(self, name):
        if name not in self.ELLIPSOIDS:
            name = "CGCS2000"
        self.ellipsoid_name = name
        a, inv_f = self.ELLIPSOIDS[name]
        self.a = a
        self.f = 1.0 / inv_f
        self.e2 = 2 * self.f - self.f ** 2  # 第一偏心率平方
        self.ep2 = self.e2 / (1.0 - self.e2)  # 第二偏心率平方

    def compute_meridian_arc(self, B_rad):
        """严格计算自赤道起的子午线弧长 X"""
        a, e2 = self.a, self.e2
        m0 = a * (1 - e2)
        m2 = 1.5 * e2 * m0
        m4 = 1.25 * e2 * m2
        m6 = (7.0 / 6.0) * e2 * m4
        m8 = (9.0 / 8.0) * e2 * m6

        a0 = m0 + 0.5 * m2 + 0.375 * m4 + 0.3125 * m6 + (35.0 / 128.0) * m8
        a2 = 0.5 * m2 + 0.5 * m4 + (15.0 / 32.0) * m6 + (7.0 / 16.0) * m8
        a4 = 0.125 * m4 + (3.0 / 16.0) * m6 + (7.0 / 32.0) * m8
        a6 = (1.0 / 32.0) * m6 + (1.0 / 16.0) * m8
        a8 = (1.0 / 128.0) * m8

        X = (a0 * B_rad 
             - 0.5 * a2 * math.sin(2 * B_rad) 
             + 0.25 * a4 * math.sin(4 * B_rad) 
             - (1.0 / 6.0) * a6 * math.sin(6 * B_rad) 
             + 0.125 * a8 * math.sin(8 * B_rad))
        return X

    def compute_foot_latitude(self, X_target, tolerance=1e-11, max_iter=100):
        """由子午线弧长反求垂足纬度 Bf"""
        a, e2 = self.a, self.e2
        m0 = a * (1 - e2)
        m2 = 1.5 * e2 * m0
        m4 = 1.25 * e2 * m2
        m6 = (7.0 / 6.0) * e2 * m4
        m8 = (9.0 / 8.0) * e2 * m6

        a0 = m0 + 0.5 * m2 + 0.375 * m4 + 0.3125 * m6 + (35.0 / 128.0) * m8
        a2 = 0.5 * m2 + 0.5 * m4 + (15.0 / 32.0) * m6 + (7.0 / 16.0) * m8
        a4 = 0.125 * m4 + (3.0 / 16.0) * m6 + (7.0 / 32.0) * m8
        a6 = (1.0 / 32.0) * m6 + (1.0 / 16.0) * m8
        a8 = (1.0 / 128.0) * m8

        Bf = X_target / a0
        for _ in range(max_iter):
            numerator = (X_target 
                         + 0.5 * a2 * math.sin(2 * Bf) 
                         - 0.25 * a4 * math.sin(4 * Bf) 
                         + (1.0 / 6.0) * a6 * math.sin(6 * Bf) 
                         - 0.125 * a8 * math.sin(8 * Bf))
            Bf_new = numerator / a0
            if abs(Bf_new - Bf) < tolerance:
                return Bf_new
            Bf = Bf_new
        return Bf

    def forward(self, B_deg, L_deg, L0_deg):
        """
        高斯正算简化公式实现：
        x = X + N/2 * sinB * cosB * l^2
        y = N * cosB * l + N/6 * cos^3B * l^3
        """
        B = math.radians(B_deg)
        L = math.radians(L_deg)
        L0 = math.radians(L0_deg)
        l = L - L0

        X = self.compute_meridian_arc(B)
        N = self.a / math.sqrt(1.0 - self.e2 * (math.sin(B) ** 2))

        x = X + (N / 2.0) * math.sin(B) * math.cos(B) * (l ** 2)
        y = N * math.cos(B) * l + (N / 6.0) * (math.cos(B) ** 3) * (l ** 3)

        return x, y, l

    def inverse(self, x, y, L0_deg, tolerance=1e-11, max_iter=100):
        """
        高斯反算迭代公式实现：
        B = Bf - y^2 / (2 * N^2) * cotB
        l_new = y / (N * cosB) - 1/6 * cos^2B * l^3
        """
        Bf = self.compute_foot_latitude(x)

        # 迭代求解 B
        B = Bf
        for _ in range(max_iter):
            if abs(B) < 1e-12:
                break
            N = self.a / math.sqrt(1.0 - self.e2 * (math.sin(B) ** 2))
            cotB = 1.0 / math.tan(B)
            B_new = Bf - (y ** 2 / (2.0 * N ** 2)) * cotB
            if abs(B_new - B) < tolerance:
                B = B_new
                break
            B = B_new

        # 迭代求解经差 l
        N = self.a / math.sqrt(1.0 - self.e2 * (math.sin(B) ** 2))
        cosB = math.cos(B)
        if abs(cosB) < 1e-12:
            l = 0.0
        else:
            l_term = y / (N * cosB)
            l = l_term
            for _ in range(max_iter):
                l_new = l_term - (1.0 / 6.0) * (cosB ** 2) * (l ** 3)
                if abs(l_new - l) < tolerance:
                    l = l_new
                    break
                l = l_new

        B_deg = math.degrees(B)
        L_deg = L0_deg + math.degrees(l)
        return B_deg, L_deg

    @staticmethod
    def get_zone_number(L_deg):
        """6° 带带号计算公式"""
        return int(math.floor(L_deg / 6.0) + 1)

    @staticmethod
    def get_central_meridian(n):
        """中央子午线计算公式"""
        return 6 * n - 3