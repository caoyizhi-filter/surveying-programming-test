# 导入系统内置数学库，用于自然对数ln计算，无任何第三方库
import math

# ===================== 第一部分：底层向量、矩阵基础运算工具 =====================
def vec_sub(v1, v2):
    """
    函数功能：实现两个向量相减 v1 - v2
    输入参数：
        v1：被减向量（列表存储，如[41.92,45.67,48.84,44.31]）
        v2：减数向量（维度必须和v1完全一致）
    返回值：相减后的新向量
    数学用途：计算偏差 dx = x - μ
    """
    res = [v1[i] - v2[i] for i in range(len(v1))]
    # ===== 推荐在本行左侧行号处点击红点设置断点 =====
    return res


def vec_dot(v1, v2):
    """
    函数功能：两个同维度向量求内积（点积）
    输入：两个长度完全相等的一维向量
    返回：标量浮点数，内积计算结果
    数学用途：二次型最后一步 dx.T @ invΣ @ dx 最终标量求解
    """
    sum_result = 0.0
    for a, b in zip(v1, v2):
        sum_result += a * b
    return sum_result


def vec_mul_T(v):
    """
    函数功能：列向量 乘以 自身转置行向量，生成外积方阵 v @ v.T
    输入：一维向量v
    返回：n×n二维矩阵（n为波段数，本题4波段，输出4×4矩阵）
    数学用途：协方差计算核心：(x-μ)(x-μ)^T
    """
    n_dim = len(v)
    outer_matrix = [[0.0] * n_dim for _ in range(n_dim)]
    for i in range(n_dim):
        for j in range(n_dim):
            outer_matrix[i][j] = v[i] * v[j]
    return outer_matrix


def mat_add(m1, m2):
    """
    函数功能：两个同阶矩阵对应位置相加
    输入：两个行列数完全相同的二维矩阵
    返回：相加后的新矩阵
    数学用途：所有样本外积矩阵累加求和
    """
    # 获取矩阵阶数（4×4矩阵，n=4）
    n = len(m1)
    # 创建空结果矩阵，全部初始化为0
    res_mat = [[0.0] * n for _ in range(n)]
    # 遍历每一行
    for i in range(n):
        # 遍历该行每一列
        for j in range(n):
            # 修复：m1[i][j] 取出对应位置标量
            res_mat[i][j] = m1[i][j] + m2[i][j]
    # ===== 推荐在此行左侧设置断点 =====
    return res_mat


def mat_scalar(mat, k):
    """
    函数功能：矩阵整体乘以一个常数（数乘）
    输入：mat原始矩阵，k常数浮点数
    返回：每个元素都乘以k的新矩阵
    数学用途：协方差无偏估计，求和矩阵除以N-1（即乘以1/(N-1)）
    """
    n = len(mat)
    res_mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            res_mat[i][j] = mat[i][j] * k
    return res_mat


def mat_vec_mul(mat, vec):
    """
    函数功能：矩阵 × 列向量
    输入：n×n矩阵，长度n一维向量
    返回：新一维向量
    """
    n = len(mat)
    res_vec = [0.0] * n
    for i in range(n):
        row_sum = 0.0
        for j in range(n):
            row_sum += mat[i] * vec[j]
        res_vec[i] = row_sum
    return res_vec


def vec_mat_mul(vec, mat):
    """
    函数功能：行向量 × 矩阵
    输入：一维行向量，n×n矩阵
    返回：新一维行向量
    数学用途：dx.T @ invΣ 中间计算步骤
    """
    n = len(vec)
    res_vec = [0.0] * n
    for j in range(n):
        col_sum = 0.0
        for i in range(n):
            col_sum += vec[i] * mat[i][j]
        res_vec[j] = col_sum
    return res_vec

# ===================== 第二部分：矩阵高级运算（行列式、求逆） =====================
def mat_det(mat):
    """
    函数功能：高斯消元法计算方阵行列式
    输入：n阶方阵（本题4阶协方差矩阵）
    返回：行列式浮点数值
    异常逻辑：主接近0，矩阵奇异，行列式直接返回0
    数学用途：对数似然公式 ln|Σ|，必须先求协方差行列式
    """
    n = len(mat)
    m_copy = [[mat[i][j] for j in range(n)] for i in range(n)]
    det_val = 1.0

    for col in range(n):
        pivot_row = col
        for r in range(col, n):
            if abs(m_copy[r][col]) > abs(m_copy[pivot_row][col]):
                pivot_row = r
        if abs(m_copy[pivot_row][col]) < 1e-12:
            return 0.0
        if pivot_row != col:
            m_copy[col], m_copy[pivot_row] = m_copy[pivot_row], m_copy[col]
            det_val *= -1
        div_factor = m_copy[col][col]
        det_val *= div_factor
        for j in range(col, n):
            m_copy[col][j] /= div_factor
        for r in range(col + 1, n):
            factor = m_copy[r][col]
            for j in range(col, n):
                m_copy[r][j] -= factor * m_copy[col][j]
    return det_val


def mat_inv(mat):
    """
    函数功能：高斯增广矩阵法求方阵逆矩阵
    输入：可逆方阵
    返回：原矩阵的逆矩阵
    抛出异常：矩阵奇异（无法求逆），程序终止提示
    数学用途：判别式需要协方差逆矩阵 Σ⁻¹
    """
    n = len(mat)
    aug_mat = [[0.0] * (2 * n) for _ in range(n)]
    for i in range(n):
        for j in range(n):
            aug_mat[i][j] = mat[i][j]
        aug_mat[i][i + n] = 1.0

    for col in range(n):
        pivot_row = col
        for r in range(col, n):
            if abs(aug_mat[r][col]) > abs(aug_mat[pivot_row][col]):
                pivot_row = r
        if abs(aug_mat[pivot_row][col]) < 1e-12:
            raise Exception("错误：协方差矩阵奇异，无法求逆，样本不可分")
        aug_mat[col], aug_mat[pivot_row] = aug_mat[pivot_row], aug_mat[col]
        div = aug_mat[col][col]
        for j in range(col, 2 * n):
            aug_mat[col][j] /= div
        for r in range(n):
            if r != col and abs(aug_mat[r][col]) > 1e-12:
                fac = aug_mat[r][col]
                for j in range(col, 2 * n):
                    aug_mat[r][j] -= fac * aug_mat[col][j]
    inv_result = [[aug_mat[i][j + n] for j in range(n)] for i in range(n)]
    return inv_result

# ===================== 第三部分：文件读取函数 =====================
def read_train(filepath):
    """
    函数功能：读取训练样本train.txt
    返回：字典 {类别数字: [该类别所有样本向量]}
    """
    class_group = {}
    with open(filepath, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        for line in all_lines:
            line = line.strip()
            if not line:
                continue
            parts = list(map(float, line.split(",")))
            class_id = int(parts[0])
            sample_vec = parts[1:]
            if class_id not in class_group:
                class_group[class_id] = []
            class_group[class_id].append(sample_vec)
    return class_group


def read_pixel(filepath):
    """读取待分类像元pixel.txt"""
    pixel_list = []
    with open(filepath, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        for line in all_lines:
            line = line.strip()
            if not line:
                continue
            pixel_vec = list(map(float, line.split(",")))
            pixel_list.append(pixel_vec)
    return pixel_list


def read_verify(filepath):
    """读取精度验证样本verify.txt"""
    verify_data = []
    with open(filepath, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        for line in all_lines:
            line = line.strip()
            if not line:
                continue
            parts = list(map(float, line.split(",")))
            true_class = int(parts[0])
            spec_vec = parts[1:]
            verify_data.append((true_class, spec_vec))
    return verify_data

# ===================== 第四部分：均值、协方差计算 =====================
def calc_mean(sample_list):
    """计算一类样本均值向量μ"""
    band_num = len(sample_list[0])
    sum_band = [0.0] * band_num
    for vec in sample_list:
        for i in range(band_num):
            sum_band[i] += vec[i]
    sample_count = len(sample_list)
    mean_vec = [s / sample_count for s in sum_band]
    return mean_vec


def calc_cov_unbiased(sample_list, mean_vec):
    """无偏协方差矩阵计算（分母N-1）"""
    N = len(sample_list)
    n_dim = len(mean_vec)
    total_outer_mat = [[0.0] * n_dim for _ in range(n_dim)]
    for vec in sample_list:
        dx = vec_sub(vec, mean_vec)
        outer = vec_mul_T(dx)
        total_outer_mat = mat_add(total_outer_mat, outer)
    cov_matrix = mat_scalar(total_outer_mat, 1.0 / (N - 1))
    return cov_matrix

# ===================== 第五部分：对数似然计算 =====================
def calc_g(x, mu, cov):
    """计算单像元对数似然判别值g(x)"""
    det_sigma = mat_det(cov)
    if det_sigma <= 1e-12:
        raise Exception("协方差矩阵奇异，无法完成分类")
    inv_sigma = mat_inv(cov)
    dx = vec_sub(x, mu)
    temp_vec = vec_mat_mul(dx, inv_sigma)
    quad_term = vec_dot(temp_vec, dx)
    log_det = math.log(det_sigma)
    g_val = log_det + quad_term
    return g_val, det_sigma, inv_sigma

# ===================== 第六部分：混淆矩阵、OA、Kappa =====================
def build_confusion(verify_data, class_mean_dict, class_cov_dict):
    """
    函数功能：遍历验证样本生成混淆矩阵
    输入：验证集、各类均值、各类协方差
    返回：混淆矩阵、类别下标映射
    """
    class_list = sorted(class_mean_dict.keys())
    class_num = len(class_list)
    idx_map = {cid:i for i,cid in enumerate(class_list)}
    # 修复：range 参数使用 class_num（整数）
    confusion = [[0] * class_num for _ in range(class_num)]

    for true_class, spec_vec in verify_data:
        g_record = {}
        for c in class_list:
            g, _, _ = calc_g(spec_vec, class_mean_dict[c], class_cov_dict[c])
            g_record[c] = g
        pred_class = min(g_record, key=g_record.get)
        row = idx_map[true_class]
        col = idx_map[pred_class]
        confusion[row][col] += 1
    return confusion, idx_map


def calc_oa_kappa(conf_mat):
    """计算总体精度OA、Kappa系数"""
    total_sample = 0
    correct_sample = 0
    n_class = len(conf_mat)
    row_sum = [0] * n_class
    col_sum = [0] * n_class
    for i in range(n_class):
        for j in range(n_class):
            val = conf_mat[i][j]
            total_sample += val
            row_sum[i] += val
            col_sum[j] += val
            if i == j:
                correct_sample += val
    OA = correct_sample / total_sample if total_sample != 0 else 0.0
    pe_numerator = 0.0
    for i in range(n_class):
        pe_numerator += row_sum[i] * col_sum[i]
    Pe = pe_numerator / (total_sample ** 2) if total_sample != 0 else 0.0
    if abs(1 - Pe) < 1e-12:
        Kappa = 0.0
    else:
        Kappa = (OA - Pe) / (1 - Pe)
    return correct_sample, total_sample, OA, Kappa


def run_all(train_path="train.txt", pixel_path="pixel.txt",
            verify_path="verify.txt", output_path="mlc_result.txt"):
    """
    执行完整最大似然分类流程，返回结果字典。
    可从命令行直接运行，也可被 GUI 调用。
    """
    # 读取三份数据文件
    train_data = read_train(train_path)
    pixel_data = read_pixel(pixel_path)
    verify_data = read_verify(verify_path)
    class_list = sorted(train_data.keys())
    c1 = class_list[0]
    c2 = class_list[1]
    num1 = len(train_data[c1])
    num2 = len(train_data[c2])

    # 计算两类均值
    mu1 = calc_mean(train_data[c1])
    mu2 = calc_mean(train_data[c2])

    # 计算两类协方差矩阵
    cov1 = calc_cov_unbiased(train_data[c1], mu1)
    cov2 = calc_cov_unbiased(train_data[c2], mu2)

    det1 = mat_det(cov1)
    det2 = mat_det(cov2)

    # 批量分类所有像元
    count_cls1 = 0
    count_cls2 = 0
    first_g1 = 0.0
    first_g2 = 0.0
    first_pred = 0
    for idx, px in enumerate(pixel_data):
        g1, _, _ = calc_g(px, mu1, cov1)
        g2, _, _ = calc_g(px, mu2, cov2)
        if g1 < g2:
            pred = 1
            count_cls1 += 1
        else:
            pred = 2
            count_cls2 += 1
        if idx == 0:
            first_g1 = g1
            first_g2 = g2
            first_pred = pred

    # 精度验证
    conf, _ = build_confusion(verify_data, {1: mu1, 2: mu2}, {1: cov1, 2: cov2})
    corr, total_v, OA, KAP = calc_oa_kappa(conf)

    # 组装输出文本
    output = []
    output.append(f"1,类别 1 训练样本总数,{num1}")
    output.append(f"2,类别 1 波段 1 均值,{mu1[0]:.4f}")
    output.append(f"3,类别 1 波段 2 均值,{mu1[1]:.4f}")
    output.append(f"4,类别 1 协方差矩阵行列式,{det1:.6f}")
    output.append(f"5,类别 2 训练样本总数,{num2}")
    output.append(f"6,类别 2 波段 1 均值,{mu2[0]:.4f}")
    output.append(f"7,类别 2 波段 2 均值,{mu2[1]:.4f}")
    output.append(f"8,类别 2 协方差矩阵行列式,{det2:.6f}")
    output.append(f"9,第 1 个待分类像元类别 1 对数似然值,{first_g1:.6f}")
    output.append(f"10,第 1 个待分类像元类别 2 对数似然值,{first_g2:.6f}")
    output.append(f"11,第 1 个待分类像元最终分类类别,{first_pred}")
    output.append(f"12,验证样本总数量,{total_v}")
    output.append(f"13,混淆矩阵对角线正确样本总数,{corr}")
    output.append(f"14,总体分类精度 OA,{OA:.4f}")
    output.append(f"15,分类 Kappa 系数,{KAP:.4f}")
    output.append(f"16,所有待分类像元中类别 1 总个数,{count_cls1}")
    output.append(f"17,所有待分类像元中类别 2 总个数,{count_cls2}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    return {
        "train_data": train_data,
        "pixel_data": pixel_data,
        "verify_data": verify_data,
        "num1": num1, "num2": num2,
        "mu1": mu1, "mu2": mu2,
        "cov1": cov1, "cov2": cov2,
        "det1": det1, "det2": det2,
        "count_cls1": count_cls1, "count_cls2": count_cls2,
        "first_g1": first_g1, "first_g2": first_g2, "first_pred": first_pred,
        "confusion": conf, "corr": corr, "total_v": total_v,
        "OA": OA, "KAP": KAP,
    }


if __name__ == "__main__":
    run_all()
