# calculator.py
# GNSS伪距单点定位(高程角定权) — 核心算法模块
# 使用加权高斯-牛顿迭代最小二乘法求解接收机三维坐标
# ============================================================
# 观测方程: CL_i + SatClock_i - TropDelay_i = ρ_i + b_r + v_i
#   即: 改正后伪距 = 几何距离 + 接收机钟差等效距离
#   其中 ρ_i = sqrt((X_i-Xu)² + (Y_i-Yu)² + (Z_i-Zu)²)
#   b_r = c·δt_r (接收机钟差等效距离, 米)
# 权阵: p_i = sin²(E_i),  P = diag(p_1, ..., p_n)
# 未知数: Xu, Yu, Zu, b_r (4个, 单位均为米)
# ============================================================

import math


# ============================================================
#  矩阵运算（纯 Python，不用 numpy）
# ============================================================

def mat_transpose(A):
    rows = len(A)
    cols = len(A[0]) if rows > 0 else 0
    return [[A[r][c] for r in range(rows)] for c in range(cols)]


def mat_mul(A, B):
    m = len(A)
    n = len(A[0])
    p = len(B[0])
    C = [[0.0] * p for _ in range(m)]
    for i in range(m):
        for k in range(n):
            aik = A[i][k]
            if aik != 0.0:
                for j in range(p):
                    C[i][j] += aik * B[k][j]
    return C


def mat_inverse_4x4(A):
    n = 4
    aug = [[0.0] * (2 * n) for _ in range(n)]
    for i in range(n):
        for j in range(n):
            aug[i][j] = A[i][j]
        aug[i][i + n] = 1.0

    for col in range(n):
        pivot = col
        max_val = abs(aug[col][col])
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                pivot = row
        if max_val < 1e-20:
            raise ValueError("法矩阵奇异，无法求逆")

        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        pivot_val = aug[col][col]
        for j in range(2 * n):
            aug[col][j] /= pivot_val

        for row in range(n):
            if row != col:
                factor = aug[row][col]
                for j in range(2 * n):
                    aug[row][j] -= factor * aug[col][j]

    inv = [[aug[i][j + n] for j in range(n)] for i in range(n)]
    return inv


def solve_4x4(A, b):
    """
    解 4×4 线性方程组 A·x = b
    b 格式: [[b0],[b1],[b2],[b3]] (列向量)
    返回: [x0, x1, x2, x3]
    """
    n = 4
    aug = [[0.0] * (n + 1) for _ in range(n)]
    for i in range(n):
        for j in range(n):
            aug[i][j] = A[i][j]
        aug[i][n] = b[i][0]

    for col in range(n):
        pivot = col
        max_val = abs(aug[col][col])
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                pivot = row
        if max_val < 1e-20:
            raise ValueError("法矩阵奇异，无法求解")

        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        pivot_val = aug[col][col]
        for j in range(n + 1):
            aug[col][j] /= pivot_val

        for row in range(n):
            if row != col:
                factor = aug[row][col]
                for j in range(n + 1):
                    aug[row][j] -= factor * aug[col][j]

    return [aug[i][n] for i in range(n)]


# ============================================================
#  数据类
# ============================================================

class Satellite:
    """单颗卫星一次观测数据"""
    def __init__(self, prn: str, x: float, y: float, z: float,
                 sat_clock: float, elevation: float,
                 cl: float, trop_delay: float, epoch: float = 0.0):
        self.prn = prn
        self.x = x
        self.y = y
        self.z = z
        self.sat_clock = sat_clock      # 卫星钟差 c·δt_s (m)
        self.elevation = elevation       # 高度角 (度)
        self.cl = cl                     # 码观测值 (m)
        self.trop_delay = trop_delay     # 对流层延迟 (m)
        self.epoch = epoch               # GPS时间 (s)


# ============================================================
#  主计算器
# ============================================================

class GNSSSolver:
    """
    GNSS伪距单点定位计算器（高程角定权）

    用法:
        solver = GNSSSolver(satellites, approx_position, light_speed)
        solver.solve()
        # 读取: solver.Xr, solver.Yr, solver.Zr, solver.dt,
        #       solver.iterations, solver.unit_variance, solver.PDOP
    """

    def __init__(self, satellites: list, approx_position: tuple, light_speed: float):
        self.satellites = satellites
        self.c = light_speed
        self.n = len(satellites)

        # 近似坐标 (试题册指定)
        self.X0 = approx_position[0]
        self.Y0 = approx_position[1]
        self.Z0 = approx_position[2]

        # 输出属性
        self.Xr = 0.0
        self.Yr = 0.0
        self.Zr = 0.0
        self.dt = 0.0            # 接收机钟差 (秒), = b / c
        self.iterations = 0
        self.unit_variance = 0.0 # 单位权方差 σ₀² = VᵀPV/(n-4)
        self.PDOP = 0.0

    def solve(self, max_iter=20, threshold=1e-6):
        """
        加权迭代最小二乘求解

        观测方程: CL_i + SatClock_i - TropDelay_i = ρ_i + b_r
        改正后伪距: l_obs_i = CL_i + SatClock_i - TropDelay_i
        模型预测:   l_pre_i = ρ_i + b_r
        残差:       v_i = l_obs_i - l_pre_i

        设计矩阵 B (n×4):
          ∂P/∂X = -(X_i-X₀)/ρ₀, ∂P/∂Y = -(Y_i-Y₀)/ρ₀,
          ∂P/∂Z = -(Z_i-Z₀)/ρ₀, ∂P/∂b = 1

        权阵 P = diag(p_1, ..., p_n),  p_i = sin²(E_i)

        法方程: N = BᵀPB, U = BᵀPl
        改正数: Δx = N⁻¹U

        收敛判据: sqrt(ΔX²+ΔY²+ΔZ²+Δb²) < 1e-6 m
        """
        sats = self.satellites
        n = self.n

        # ── 初始近似 ──
        X = self.X0
        Y = self.Y0
        Z = self.Z0
        b = 0.0   # c·δt_r 等效距离 (米)

        # ── 预计算权重 p_i = sin²(E_i) ──
        weights = []
        for s in sats:
            e_rad = math.radians(s.elevation)
            weights.append(math.sin(e_rad) ** 2)

        N = None  # 保存最后一次迭代的法矩阵

        # ── 迭代 ──
        for iteration in range(1, max_iter + 1):
            # 计算近似几何距离 r̂_i
            rho0 = []
            for s in sats:
                dx = s.x - X
                dy = s.y - Y
                dz = s.z - Z
                r = math.sqrt(dx * dx + dy * dy + dz * dz)
                rho0.append((r, dx, dy, dz))

            # 组建加权法方程 N = BᵀPB (4×4), U = BᵀPl (4×1)
            N = [[0.0] * 4 for _ in range(4)]
            U = [[0.0] for _ in range(4)]

            for i in range(n):
                r, dx, dy, dz = rho0[i]
                p = weights[i]

                # 设计矩阵第 i 行
                b0 = -dx / r
                b1 = -dy / r
                b2 = -dz / r
                b3 = 1.0

                # 观测值残差: l_i = (CL + SatClock - TropDelay) - (r + b)
                li = sats[i].cl + sats[i].sat_clock - sats[i].trop_delay - r - b

                # N += p_i * B_iᵀ · B_i  (加权外积)
                N[0][0] += p * b0 * b0
                N[0][1] += p * b0 * b1
                N[0][2] += p * b0 * b2
                N[0][3] += p * b0 * b3
                N[1][1] += p * b1 * b1
                N[1][2] += p * b1 * b2
                N[1][3] += p * b1 * b3
                N[2][2] += p * b2 * b2
                N[2][3] += p * b2 * b3
                N[3][3] += p * b3 * b3

                # U += p_i * B_iᵀ · l_i
                wli = p * li
                U[0][0] += wli * b0
                U[1][0] += wli * b1
                U[2][0] += wli * b2
                U[3][0] += wli * b3

            # 对称化 N
            N[1][0] = N[0][1]
            N[2][0] = N[0][2]
            N[2][1] = N[1][2]
            N[3][0] = N[0][3]
            N[3][1] = N[1][3]
            N[3][2] = N[2][3]

            # 求解 Δx = N⁻¹U
            dx_vec = solve_4x4(N, U)

            dX = dx_vec[0]
            dY = dx_vec[1]
            dZ = dx_vec[2]
            db = dx_vec[3]

            # 更新
            X += dX
            Y += dY
            Z += dZ
            b += db

            # 收敛判断
            pos_change = math.sqrt(dX * dX + dY * dY + dZ * dZ + db * db)
            if pos_change < threshold:
                break

        self.iterations = iteration
        self.Xr = X
        self.Yr = Y
        self.Zr = Z
        self.dt = b / self.c

        # ── 统计量 ──
        # PDOP 从最终法矩阵的逆 Q = N⁻¹
        Q = mat_inverse_4x4(N)
        self.PDOP = math.sqrt(Q[0][0] + Q[1][1] + Q[2][2])

        # 单位权方差 σ₀² = VᵀPV / (n-4)
        vtpv = 0.0
        for i in range(n):
            dx = sats[i].x - X
            dy = sats[i].y - Y
            dz = sats[i].z - Z
            rho = math.sqrt(dx * dx + dy * dy + dz * dz)
            # 残差: v_i = (CL + SatClock - TropDelay) - (ρ + b)
            vi = sats[i].cl + sats[i].sat_clock - sats[i].trop_delay - rho - b
            vtpv += weights[i] * vi * vi

        dof = n - 4
        if dof > 0:
            self.unit_variance = vtpv / dof
        else:
            self.unit_variance = 0.0
