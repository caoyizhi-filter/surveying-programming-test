# calculator.py
# 遥感影像最大似然法分类 — 核心计算模块
# 仅使用 Python 标准库 math

import math


# ══════════════════════════════════════════════════════════════
#  4×4 矩阵工具（纯标准库，禁止 numpy）
# ══════════════════════════════════════════════════════════════

def _mat_det(M):
    """4×4 矩阵行列式（Gauss 消元法）"""
    n = 4
    A = [row[:] for row in M]
    det = 1.0
    for i in range(n):
        # 部分主元
        pivot = i
        for r in range(i + 1, n):
            if abs(A[r][i]) > abs(A[pivot][i]):
                pivot = r
        if abs(A[pivot][i]) < 1e-16:
            return 0.0
        if pivot != i:
            A[i], A[pivot] = A[pivot], A[i]
            det = -det
        det *= A[i][i]
        for r in range(i + 1, n):
            factor = A[r][i] / A[i][i]
            for c in range(i, n):
                A[r][c] -= factor * A[i][c]
    return det


def _mat_inv(M):
    """4×4 矩阵求逆（Gauss–Jordan 消元，增广矩阵法）"""
    n = 4
    A = [row[:] for row in M]
    I = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for col in range(n):
        pivot = col
        for r in range(col + 1, n):
            if abs(A[r][col]) > abs(A[pivot][col]):
                pivot = r
        if abs(A[pivot][col]) < 1e-16:
            raise ValueError("协方差矩阵奇异，无法求逆")
        if pivot != col:
            A[col], A[pivot] = A[pivot], A[col]
            I[col], I[pivot] = I[pivot], I[col]
        piv_val = A[col][col]
        for c in range(n):
            A[col][c] /= piv_val
            I[col][c] /= piv_val
        for r in range(n):
            if r == col:
                continue
            factor = A[r][col]
            for c in range(n):
                A[r][c] -= factor * A[col][c]
                I[r][c] -= factor * I[col][c]
    return I


def _vec_sub(a, b):
    return [a[i] - b[i] for i in range(len(a))]


# ══════════════════════════════════════════════════════════════
#  数据结构
# ══════════════════════════════════════════════════════════════

class ClassStats:
    """某一类别的统计量"""
    def __init__(self, class_id):
        self.class_id   = class_id
        self.count      = 0
        self.mean       = [0.0, 0.0, 0.0, 0.0]
        self.cov        = [[0.0]*4 for _ in range(4)]
        self.inv_cov    = [[0.0]*4 for _ in range(4)]
        self.log_det    = 0.0     # ln(|Σ|)


class PixelResult:
    """单个像元的分类结果"""
    def __init__(self, idx, values):
        self.idx       = idx
        self.values    = values        # 原始光谱 [b1,b2,b3,b4]
        self.likelihoods = {}          # {class_id: discriminant_value}
        self.pred_class = 0


class ConfusionMatrix:
    def __init__(self, class_ids):
        self.class_ids = class_ids
        self.matrix = {c: {d: 0 for d in class_ids} for c in class_ids}
        self.total  = 0


# ══════════════════════════════════════════════════════════════
#  训练样本统计
# ══════════════════════════════════════════════════════════════

def compute_class_stats(samples_by_class):
    """
    对每类样本计算均值向量和协方差矩阵。
    samples_by_class: {class_id: [[b1,b2,b3,b4], ...]}
    返回: {class_id: ClassStats}
    """
    stats_map = {}
    for cls_id, samples in samples_by_class.items():
        n = len(samples)
        if n < 2:
            continue
        st = ClassStats(cls_id)
        st.count = n

        # 均值向量
        for band in range(4):
            st.mean[band] = sum(s[band] for s in samples) / n

        # 协方差矩阵（无偏估计）
        for band_i in range(4):
            for band_j in range(4):
                s = 0.0
                for k in range(n):
                    s += (samples[k][band_i] - st.mean[band_i]) * \
                         (samples[k][band_j] - st.mean[band_j])
                st.cov[band_i][band_j] = s / (n - 1)

        # 协方差逆矩阵 + ln 行列式
        det = _mat_det(st.cov)
        if det < 1e-14:
            det = 1e-14
        st.log_det = math.log(det)
        st.inv_cov = _mat_inv(st.cov)
        stats_map[cls_id] = st

    return stats_map


# ══════════════════════════════════════════════════════════════
#  判别函数（对数似然）
# ══════════════════════════════════════════════════════════════

def compute_discriminant(pixel_values, stats: ClassStats):
    """
    d(x) = ln|Σ| + (x-μ)^T Σ^{-1} (x-μ)
    距离形式的判别函数（值越小越可能属于该类）
    与标准对数似然 g(x) = -0.5*d(x) 等价（d 越小 ⟺ g 越大）
    """
    d = _vec_sub(pixel_values, stats.mean)
    maha_sq = 0.0
    for i in range(4):
        row_sum = 0.0
        for j in range(4):
            row_sum += d[j] * stats.inv_cov[i][j]
        maha_sq += d[i] * row_sum
    return stats.log_det + maha_sq


def classify_pixel(pixel_values, stats_map):
    """
    对待分类像元计算各类判别值，返回 (pred_class, {class_id: discriminant})
    距离形式：选取判别函数值最小的类别
    """
    disc = {}
    best_cls = None
    best_val = float('inf')
    for cls_id, st in stats_map.items():
        g = compute_discriminant(pixel_values, st)
        disc[cls_id] = g
        if g < best_val:
            best_val = g
            best_cls = cls_id
    return best_cls, disc


# ══════════════════════════════════════════════════════════════
#  精度评估
# ══════════════════════════════════════════════════════════════

def build_confusion_matrix(verify_samples, stats_map, class_ids):
    """
    verify_samples: [(true_class, [b1,b2,b3,b4]), ...]
    返回 ConfusionMatrix
    """
    cm = ConfusionMatrix(class_ids)
    for true_cls, values in verify_samples:
        pred_cls, _ = classify_pixel(values, stats_map)
        cm.matrix[true_cls][pred_cls] += 1
        cm.total += 1
    return cm


def compute_oa(cm: ConfusionMatrix):
    """总体分类精度 = 对角线之和 / 总数"""
    correct = sum(cm.matrix[c][c] for c in cm.class_ids)
    return correct / cm.total if cm.total else 0.0


def compute_kappa(cm: ConfusionMatrix):
    """Kappa 系数"""
    if cm.total == 0:
        return 0.0
    correct = sum(cm.matrix[c][c] for c in cm.class_ids)
    oa = correct / cm.total

    # P_e = Σ (row_sum_i × col_sum_i) / N²
    pe = 0.0
    for c in cm.class_ids:
        row_sum = sum(cm.matrix[c][d] for d in cm.class_ids)
        col_sum = sum(cm.matrix[d][c] for d in cm.class_ids)
        pe += row_sum * col_sum
    pe /= (cm.total * cm.total)

    if abs(1.0 - pe) < 1e-14:
        return 1.0 if abs(oa - 1.0) < 1e-10 else 0.0
    return (oa - pe) / (1.0 - pe)


# ══════════════════════════════════════════════════════════════
#  最大似然分类器
# ══════════════════════════════════════════════════════════════

class MLClassifier:

    def __init__(self):
        self.train_samples  : dict = {}  # {class_id: [[b1..b4],...]}
        self.pixels         : list = []  # list[(idx, [b1..b4])]
        self.verify_samples : list = []  # list[(true_class, [b1..b4])]
        self.stats_map      : dict = {}
        self.results        : list = []  # list[PixelResult]
        self.cm             = None

    def add_train(self, class_id, values):
        self.train_samples.setdefault(class_id, []).append(values)

    def add_pixel(self, idx, values):
        self.pixels.append((idx, values))

    def add_verify(self, class_id, values):
        self.verify_samples.append((class_id, values))

    def compute(self):
        class_ids = sorted(self.train_samples.keys())
        self.stats_map = compute_class_stats(self.train_samples)

        self.results = []
        for idx, vals in self.pixels:
            pr = PixelResult(idx, vals)
            pr.pred_class, pr.likelihoods = classify_pixel(vals, self.stats_map)
            self.results.append(pr)

        if self.verify_samples:
            self.cm = build_confusion_matrix(self.verify_samples,
                                              self.stats_map, class_ids)
