# calculator.py
# 基于统计滤波的点云去噪核心算法
# 仅使用 Python 标准库 math

import math


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class Point:
    """单个点云点"""
    def __init__(self, idx, x, y, z):
        self.idx  = idx   # 从1开始的序号
        self.x    = x
        self.y    = y
        self.z    = z
        # 计算结果
        self.gi   = 0     # 网格索引 i
        self.gj   = 0     # 网格索引 j
        self.gk   = 0     # 网格索引 k
        self.candidates  = 0     # 候选点总数
        self.neighbors   = []    # 6邻近点序号列表
        self.mean_dist   = 0.0   # 邻域平均距离
        self.std_dist    = 0.0   # 邻域距离标准差
        self.is_noise    = 0     # 1=噪声 0=正常


# ══════════════════════════════════════════════════════════════
#  主计算类
# ══════════════════════════════════════════════════════════════

class PointCloudProcessor:
    """
    统计滤波点云去噪处理器
    按试题册流程：
      Step1  读入点云
      Step2  格网划分
      Step3  k邻近搜索 (k=6)
      Step4  统计特征计算
      Step5  噪声判断
    """

    GRID_SIZE = 3     # 格网边长（米）
    K         = 6     # 邻近点数

    def __init__(self):
        self.points   : list  = []   # list[Point]
        self.grid_size = self.GRID_SIZE

        # 边界
        self.xmin = self.ymin = self.zmin = 0.0
        self.xmax = self.ymax = self.zmax = 0.0
        self.xmax1= self.ymax1= self.zmax1= 0.0

        # 格网字典  (i,j,k) → [Point, ...]
        self.grid : dict = {}

        # 全局统计
        self.global_mean = 0.0
        self.global_std  = 0.0

        # 汇总
        self.noise_count  = 0
        self.clean_count  = 0

    # ── Step1：载入点云 ───────────────────────────────────────
    def load(self, points: list):
        self.points = points

    # ── Step2：格网划分 ───────────────────────────────────────
    def build_grid(self):
        pts = self.points
        e   = self.grid_size

        # 边界
        self.xmin = min(p.x for p in pts)
        self.ymin = min(p.y for p in pts)
        self.zmin = min(p.z for p in pts)
        self.xmax = max(p.x for p in pts)
        self.ymax = max(p.y for p in pts)
        self.zmax = max(p.z for p in pts)

        # 扩展最大值至整格
        def ceil_grid(val_min, val_max, e):
            span = val_max - val_min
            return math.floor(span / e + 1) * e + val_min

        self.xmax1 = ceil_grid(self.xmin, self.xmax, e)
        self.ymax1 = ceil_grid(self.ymin, self.ymax, e)
        self.zmax1 = ceil_grid(self.zmin, self.zmax, e)

        # 分配格网
        self.grid = {}
        for p in pts:
            i = int(math.floor((p.x - self.xmin) / e))
            j = int(math.floor((p.y - self.ymin) / e))
            k = int(math.floor((p.z - self.zmin) / e))
            p.gi, p.gj, p.gk = i, j, k
            key = (i, j, k)
            if key not in self.grid:
                self.grid[key] = []
            self.grid[key].append(p)

    # ── Step3：k邻近搜索 ──────────────────────────────────────
    def knn_search(self):
        """对每个点搜索27个相邻格网内的候选点，取距离最近的k个"""
        for p in self.points:
            candidates = []
            # 遍历3×3×3邻域格网
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    for dk in [-1, 0, 1]:
                        key = (p.gi + di, p.gj + dj, p.gk + dk)
                        if key in self.grid:
                            for q in self.grid[key]:
                                if q.idx != p.idx:
                                    candidates.append(q)

            p.candidates = len(candidates)

            # 计算欧氏距离并排序
            dists = []
            for q in candidates:
                d = math.sqrt(
                    (p.x - q.x)**2 +
                    (p.y - q.y)**2 +
                    (p.z - q.z)**2
                )
                dists.append((d, q.idx))

            dists.sort(key=lambda t: t[0])
            top_k = dists[:self.K]

            p.neighbors  = [idx for _, idx in top_k]
            # 保存距离供统计用
            p._knn_dists = [d for d, _ in top_k]

    # ── Step4：统计特征计算 ───────────────────────────────────
    def compute_stats(self):
        """计算每个点邻域平均距离和标准差，再求全局均值和标准差"""
        for p in self.points:
            dists = p._knn_dists
            if not dists:
                p.mean_dist = 0.0
                p.std_dist  = 0.0
                continue
            n = len(dists)
            mu = sum(dists) / n
            p.mean_dist = mu
            variance = sum((d - mu)**2 for d in dists) / n
            p.std_dist = math.sqrt(variance)

        # 全局：所有点的 mean_dist 的均值和标准差
        all_means = [p.mean_dist for p in self.points]
        n = len(all_means)
        self.global_mean = sum(all_means) / n
        gm = self.global_mean
        self.global_std = math.sqrt(sum((v - gm)**2 for v in all_means) / n)

    # ── Step5：噪声判断 ───────────────────────────────────────
    def filter_noise(self):
        """uᵢ > μ + 2σ → 噪声点"""
        threshold = self.global_mean + 2 * self.global_std
        for p in self.points:
            p.is_noise = 1 if p.mean_dist > threshold else 0

        self.noise_count = sum(p.is_noise for p in self.points)
        self.clean_count = len(self.points) - self.noise_count

    # ── 一键运行全流程 ────────────────────────────────────────
    def run(self):
        self.build_grid()
        self.knn_search()
        self.compute_stats()
        self.filter_noise()
