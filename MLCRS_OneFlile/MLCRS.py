# ============================================================
# 导入模块
# ============================================================
import math    # 自然对数 math.log()
import sys     # 命令行参数 sys.argv、程序退出 sys.exit()
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTableWidgetItem,
                              QHeaderView, QAction, QStatusBar, QSplitter,
                              QGroupBox, QVBoxLayout, QTableWidget, QLabel)
from PyQt5.QtCore import Qt   # 文本居中 AlignCenter、水平方向 Horizontal


# ============================================================
# 第一部分：底层向量、矩阵基础运算（6个函数，纯 Python 无第三方依赖）
# ============================================================
# 说明：这些函数是线性代数底层工具，与具体题目完全无关。
#       换任何一道竞赛题，这部分都不需要修改。
#       每步运算对应最大似然公式中的一个环节，见各函数注释。
# ============================================================

def vec_sub(v1, v2):
    """向量减法 v1-v2，对应元素相减。数学作用：计算偏差 dx = x-μ"""
    # 列表推导式：对每个索引 i，计算 v1[i] - v2[i]
    res = [v1[i] - v2[i] for i in range(len(v1))]
    return res


def vec_dot(v1, v2):
    """向量内积（点积）v1·v2 = Σ(v1[i]×v2[i])。数学作用：二次型的最后一步标量化"""
    # 累加器初始化为浮点数，保证精度
    sum_result = 0.0
    # zip 将两个向量逐对配对
    for a, b in zip(v1, v2):
        sum_result += a * b   # 对应元素相乘后累加
    return sum_result


def vec_mul_T(v):
    """列向量 × 自身转置 v@vᵀ，生成外积方阵。数学作用：协方差累加核心 (x-μ)(x-μ)ᵀ"""
    # n_dim = 波段数，本题为 2
    n_dim = len(v)
    # 创建 n×n 全零矩阵
    outer_matrix = [[0.0] * n_dim for _ in range(n_dim)]
    for i in range(n_dim):          # 行
        for j in range(n_dim):      # 列
            outer_matrix[i][j] = v[i] * v[j]   # 外积公式：v_i × v_j
    return outer_matrix


def mat_add(m1, m2):
    """矩阵加法，对应位置相加。数学作用：累加所有训练样本的外积矩阵"""
    n = len(m1)                      # 方阵阶数
    res_mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            res_mat[i][j] = m1[i][j] + m2[i][j]
    return res_mat


def mat_scalar(mat, k):
    """矩阵数乘，每个元素×常数 k。数学作用：外积总和 ÷ (N-1) = 无偏协方差估计"""
    n = len(mat)
    res_mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            res_mat[i][j] = mat[i][j] * k
    return res_mat


def vec_mat_mul(vec, mat):
    """行向量 × 矩阵 vecᵀ@mat。数学作用：计算 dxᵀ@Σ⁻¹ 中间结果"""
    n = len(vec)
    res_vec = [0.0] * n
    for j in range(n):              # 结果向量第 j 个元素
        col_sum = 0.0
        for i in range(n):
            col_sum += vec[i] * mat[i][j]   # 行向量与第 j 列逐元素乘加
        res_vec[j] = col_sum
    return res_vec


# ============================================================
# 第二部分：矩阵高级运算 —— 高斯消元法
# ============================================================
# 说明：实现行列式 |Σ| 和逆矩阵 Σ⁻¹ 的手工计算。
#       不依赖 numpy，完全用 Python 原生 list + for 循环实现。
#       时间复杂度 O(n³)，对竞赛题中的小矩阵（n≤4）绰绰有余。
#       换任何一道竞赛题，这部分都不需要修改。
# ============================================================

def mat_det(mat):
    """
    高斯消元法求方阵行列式 |Σ|
    策略：消元过程中追踪 det 变化（行交换 ×(-1)，主元归一化 ×主元值）
    边界：主元 < 1e-12 判定矩阵奇异，直接返回 0.0
    """
    n = len(mat)
    # 深拷贝原矩阵，消元操作不污染原始数据
    m_copy = [[mat[i][j] for j in range(n)] for i in range(n)]
    det_val = 1.0                     # 行列式累乘器

    for col in range(n):
        # ---- 列选主元：找当前列绝对值最大的行 ----
        pivot_row = col
        for r in range(col, n):
            if abs(m_copy[r][col]) > abs(m_copy[pivot_row][col]):
                pivot_row = r

        # ---- 奇异性判断 ----
        if abs(m_copy[pivot_row][col]) < 1e-12:
            return 0.0                # 矩阵退化，行列式为 0

        # ---- 行交换：行列式变号 ----
        if pivot_row != col:
            m_copy[col], m_copy[pivot_row] = m_copy[pivot_row], m_copy[col]
            det_val *= -1

        # ---- 主元归一化：整行除以主元，det 乘以主元值 ----
        div_factor = m_copy[col][col]
        det_val *= div_factor
        for j in range(col, n):
            m_copy[col][j] /= div_factor

        # ---- 消去下方行：下方每行减去主元行的倍数 ----
        for r in range(col + 1, n):
            factor = m_copy[r][col]    # 该行当前列待消去的值
            for j in range(col, n):
                m_copy[r][j] -= factor * m_copy[col][j]

    return det_val


def mat_inv(mat):
    """
    高斯-约当增广矩阵法求逆矩阵 Σ⁻¹
    算法：[原矩阵 | 单位阵] → 行变换使左侧变单位阵 → 右侧即为逆矩阵
    异常：主元 < 1e-12 抛出异常，提示样本不可分
    """
    n = len(mat)
    # 创建 n × 2n 增广矩阵，左侧原矩阵，右侧单位阵
    aug_mat = [[0.0] * (2 * n) for _ in range(n)]
    for i in range(n):
        for j in range(n):
            aug_mat[i][j] = mat[i][j]     # 左侧：复制原矩阵
        aug_mat[i][i + n] = 1.0           # 右侧：对角线为 1

    for col in range(n):
        # ---- 列选主元 ----
        pivot_row = col
        for r in range(col, n):
            if abs(aug_mat[r][col]) > abs(aug_mat[pivot_row][col]):
                pivot_row = r

        # ---- 奇异性检查 ----
        if abs(aug_mat[pivot_row][col]) < 1e-12:
            raise Exception("错误：协方差矩阵奇异，无法求逆，样本不可分")

        # ---- 行交换 ----
        aug_mat[col], aug_mat[pivot_row] = aug_mat[pivot_row], aug_mat[col]

        # ---- 主元归一化：整行除以主元 ----
        div = aug_mat[col][col]
        for j in range(col, 2 * n):
            aug_mat[col][j] /= div

        # ---- 消去所有非主元行（上方和下方都消，一次性完成约当消元） ----
        for r in range(n):
            if r != col and abs(aug_mat[r][col]) > 1e-12:
                fac = aug_mat[r][col]
                for j in range(col, 2 * n):
                    aug_mat[r][j] -= fac * aug_mat[col][j]

    # 提取右半部分 = 逆矩阵
    inv_result = [[aug_mat[i][j + n] for j in range(n)] for i in range(n)]
    return inv_result


# ============================================================
# 第三部分：文件读取函数
# ============================================================
# 【竞赛题切换点】如果新题目的数据文件格式不同（分隔符、列含义等），
#                修改以下三个函数的解析逻辑。当前格式：
#                  train.txt  : 类别ID,波段1,波段2
#                  pixel.txt  : 波段1,波段2
#                  verify.txt : 真实类别,波段1,波段2
# ============================================================

def read_train(filepath):
    """
    读取训练样本文件
    当前格式：每行 "类别ID,波段1值,波段2值"（逗号分隔）
    返回：{类别ID: [样本向量列表]}  例：{1: [[41.9,45.7], ...], 2: [[42.5,44.8], ...]}
    【竞赛题切换点】如果波段数不是 2，或分隔符不是逗号，修改 split 和切片逻辑
    """
    class_group = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()                        # 去除首尾空白和换行符
            if not line:                               # 跳过空行
                continue
            parts = list(map(float, line.split(",")))  # 逗号分割 → 转浮点数
            class_id = int(parts[0])                   # 第 1 列 = 类别编号
            sample_vec = parts[1:]                     # 第 2 列起 = 波段值（波段数 = len(parts)-1）
            if class_id not in class_group:
                class_group[class_id] = []
            class_group[class_id].append(sample_vec)
    return class_group


def read_pixel(filepath):
    """
    读取待分类像元文件
    当前格式：每行 "波段1值,波段2值"（无类别ID，因为待分类）
    返回：所有像元向量的 list
    【竞赛题切换点】格式和 read_train 类似，随波段数变化调整
    """
    pixel_list = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pixel_list.append(list(map(float, line.split(","))))
    return pixel_list


def read_verify(filepath):
    """
    读取精度验证样本文件
    当前格式：每行 "真实类别ID,波段1值,波段2值"
    返回：[(真实类别ID, 特征向量), ...]
    【竞赛题切换点】同 read_train，随波段数变化调整
    """
    verify_data = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = list(map(float, line.split(",")))
            true_class = int(parts[0])                 # 真实类别（已知标签，用于对比验证）
            verify_data.append((true_class, parts[1:]))
    return verify_data


# ============================================================
# 第四部分：均值向量 μ 与协方差矩阵 Σ
# ============================================================
# 说明：每个类别独立计算自己的 (μ, Σ)，作为该类的概率分布参数。
#       这些函数的输入只是样本列表，与题目无关，无需修改。
# ============================================================

def calc_mean(sample_list):
    """
    计算样本均值向量 μ = (1/N) × Σxⱼ
    参数：sample_list 该类别所有样本的 list
    返回：长度 = 波段数的均值向量
    示例：[[1,2],[3,4]] → [2.0, 3.0]
    """
    band_num = len(sample_list[0])          # 波段数 = 每个样本向量的长度
    sum_band = [0.0] * band_num             # 各波段累加器，初始化为 0.0
    for vec in sample_list:                 # 遍历该类别每个样本
        for i in range(band_num):
            sum_band[i] += vec[i]           # 累加第 i 个波段的值
    return [s / len(sample_list) for s in sum_band]  # 总和除以样本数


def calc_cov_unbiased(sample_list, mean_vec):
    """
    无偏协方差矩阵 Σ = 1/(N-1) × Σ(x-μ)(x-μ)ᵀ
    用 N-1 而非 N 是贝塞尔校正，得到总体方差的无偏估计
    """
    N = len(sample_list)                    # 样本数
    n_dim = len(mean_vec)                   # 矩阵阶数 = 波段数
    total_outer_mat = [[0.0] * n_dim for _ in range(n_dim)]  # 外积累加器
    for vec in sample_list:
        dx = vec_sub(vec, mean_vec)         # 偏差 x-μ（调用第一部分）
        outer = vec_mul_T(dx)               # 外积 (x-μ)(x-μ)ᵀ
        total_outer_mat = mat_add(total_outer_mat, outer)    # 累加
    return mat_scalar(total_outer_mat, 1.0 / (N - 1))       # ×(1/(N-1))


# ============================================================
# 第五部分：对数似然判别值 g(x)（最大似然法核心公式）
# ============================================================
# 公式：gᵢ(x) = ln|Σᵢ| + (x-μᵢ)ᵀ Σᵢ⁻¹ (x-μᵢ)
# 解释：
#   - 第一项 ln|Σᵢ|：协方差矩阵的"体积"，衡量该类样本的离散程度
#   - 第二项 二次型：马氏距离的平方，衡量像元到类别中心的"远近"
#   - g 值越小 → 该像元属于该类的概率越大 → 分类时取 g 最小的类别
# ============================================================

def calc_g(x, mu, cov):
    """
    计算像元 x 对某一类的判别值 g(x)
    参数：x 像元特征向量, mu 该类均值, cov 该类协方差矩阵
    返回：g_val 浮点数（越小越可能属于该类）
    """
    det_sigma = mat_det(cov)               # |Σ| 行列式
    if det_sigma <= 1e-12:                 # 奇异矩阵 → 不可分类
        raise Exception("协方差矩阵奇异，无法完成分类")
    inv_sigma = mat_inv(cov)               # Σ⁻¹ 逆矩阵（调用第二部分）
    dx = vec_sub(x, mu)                    # x-μ 偏差向量
    temp_vec = vec_mat_mul(dx, inv_sigma)  # (x-μ)ᵀ Σ⁻¹
    quad_term = vec_dot(temp_vec, dx)      # (x-μ)ᵀ Σ⁻¹ (x-μ) 马氏距离平方
    log_det = math.log(det_sigma)          # ln|Σ|
    return log_det + quad_term             # g(x) = ln|Σ| + 二次型


# ============================================================
# 第六部分：精度评估 + 主流程
# ============================================================
# 【竞赛题切换点】这是最需要改动的部分：
#   - build_confusion 和 calc_oa_kappa 是通用方法，无需修改
#   - run_all() 函数体是题目特定的：类别数、波段数、输出项都在这里定义
#     换一道竞赛题，重写 run_all() 即可，但保持返回格式不变
#
#   GUI 依赖的返回格式（不可改变）：
#     { "table_rows": [(序号, 指标名, 值), ...], ... }
#   table_rows 是 GUI 表格的直接数据源，只要这个格式不变，
#   第七部分的 GUI 代码就完全不用动。
# ============================================================

def build_confusion(verify_data, class_mean_dict, class_cov_dict):
    """
    构建混淆矩阵（通用方法，换题无需修改）
    参数：verify_data 验证集, class_mean_dict 各类均值, class_cov_dict 各类协方差
    返回：(混淆矩阵2D-list, 类别ID→索引映射)
    算法：对每个验证样本用最大似然法预测，与真实标签对比
    """
    class_list = sorted(class_mean_dict.keys())       # 所有类别ID排序
    class_num = len(class_list)
    idx_map = {cid: i for i, cid in enumerate(class_list)}  # 类别ID → 矩阵行列号
    confusion = [[0] * class_num for _ in range(class_num)]  # 全零混淆矩阵
    for true_class, spec_vec in verify_data:
        g_record = {}                                  # 存储该样本对各类的 g 值
        for c in class_list:
            g_record[c] = calc_g(spec_vec, class_mean_dict[c], class_cov_dict[c])
        pred_class = min(g_record, key=g_record.get)   # g 最小 → 概率最大 → 预测类别
        confusion[idx_map[true_class]][idx_map[pred_class]] += 1  # 混淆矩阵对应格 +1
    return confusion, idx_map


def calc_oa_kappa(conf_mat):
    """
    计算 OA（总体精度）和 Kappa 系数（通用方法，换题无需修改）
    OA = 对角线之和 / 总数
    Kappa = (OA - Pe) / (1 - Pe)，其中 Pe 是随机期望一致率
    """
    total_sample = 0
    correct_sample = 0
    n_class = len(conf_mat)
    row_sum = [0] * n_class       # 每行之和 = 各类别真实样本数
    col_sum = [0] * n_class       # 每列之和 = 各类别预测样本数
    for i in range(n_class):
        for j in range(n_class):
            val = conf_mat[i][j]
            total_sample += val
            row_sum[i] += val
            col_sum[j] += val
            if i == j:
                correct_sample += val         # 对角线 → 正确分类
    OA = correct_sample / total_sample if total_sample != 0 else 0.0
    # Pe = Σ(第i类真实占比 × 第i类预测占比)
    Pe = sum(row_sum[i] * col_sum[i] for i in range(n_class))
    Pe = Pe / (total_sample ** 2) if total_sample != 0 else 0.0
    if abs(1 - Pe) < 1e-12:                    # 防止除零
        Kappa = 0.0
    else:
        Kappa = (OA - Pe) / (1 - Pe)
    return correct_sample, total_sample, OA, Kappa


def run_all(train_path="train.txt", pixel_path="pixel.txt",
            verify_path="verify.txt", output_path="mlc_result.txt"):
    """
    ===== 完整最大似然分类主流程（无 GUI 可直接调用） =====
    【竞赛题切换点】换一道题目时，重写这个函数。保持返回 dict 格式不变：
      返回 {"table_rows": [(序号, 指标名, 值), ...], ... }
      table_rows 格式是 GUI 的唯一数据契约，格式不变则 GUI 零改动。
    """
    # ===== 步骤1：读取数据 =====
    train_data = read_train(train_path)
    pixel_data = read_pixel(pixel_path)
    verify_data = read_verify(verify_path)
    # 取前两个类别（【竞赛题切换点】如果类别数不是2，调整此处逻辑）
    class_list = sorted(train_data.keys())
    c1, c2 = class_list[0], class_list[1]
    num1, num2 = len(train_data[c1]), len(train_data[c2])

    # ===== 步骤2：计算各类均值 μ 和协方差 Σ =====
    mu1 = calc_mean(train_data[c1])
    mu2 = calc_mean(train_data[c2])
    cov1 = calc_cov_unbiased(train_data[c1], mu1)
    cov2 = calc_cov_unbiased(train_data[c2], mu2)
    det1 = mat_det(cov1)                      # |Σ₁| 行列式
    det2 = mat_det(cov2)                      # |Σ₂| 行列式

    # ===== 步骤3：批量分类所有待分类像元 =====
    count_cls1 = 0                            # 分为类别1 的像元计数
    count_cls2 = 0                            # 分为类别2 的像元计数
    first_g1 = first_g2 = first_pred = 0.0    # 第一个像元的详细信息（试题经常要求展示）
    for idx, px in enumerate(pixel_data):
        g1 = calc_g(px, mu1, cov1)            # 对类别1 的判别值
        g2 = calc_g(px, mu2, cov2)            # 对类别2 的判别值
        if g1 < g2:                           # g 更小 → 概率更大
            count_cls1 += 1
            pred = 1
        else:
            count_cls2 += 1
            pred = 2
        if idx == 0:                          # 记录第一个像元的信息
            first_g1, first_g2, first_pred = g1, g2, pred

    # ===== 步骤4：精度验证 =====
    conf, _ = build_confusion(verify_data, {1: mu1, 2: mu2}, {1: cov1, 2: cov2})
    corr, total_v, OA, KAP = calc_oa_kappa(conf)

    # ===== 步骤5：组装输出 =====
    # 【竞赛题切换点】table_rows 定义了 GUI 表格中显示的每一行。
    #   格式：(序号, 指标名称, 计算结果字符串)
    #   换题时按新题目的需求增删改 item，但保持三元组格式不变。
    #   GUI 只遍历这个 list 填表，完全不关心具体内容。
    table_rows = [
        (1, "类别 1 训练样本总数", str(num1)),
        (2, "类别 1 波段 1 均值", f"{mu1[0]:.4f}"),
        (3, "类别 1 波段 2 均值", f"{mu1[1]:.4f}"),
        (4, "类别 1 协方差矩阵行列式", f"{det1:.6f}"),
        (5, "类别 2 训练样本总数", str(num2)),
        (6, "类别 2 波段 1 均值", f"{mu2[0]:.4f}"),
        (7, "类别 2 波段 2 均值", f"{mu2[1]:.4f}"),
        (8, "类别 2 协方差矩阵行列式", f"{det2:.6f}"),
        (9, "第 1 个待分类像元类别 1 对数似然值", f"{first_g1:.6f}"),
        (10, "第 1 个待分类像元类别 2 对数似然值", f"{first_g2:.6f}"),
        (11, "第 1 个待分类像元最终分类类别", str(first_pred)),
        (12, "验证样本总数量", str(total_v)),
        (13, "混淆矩阵对角线正确样本总数", str(corr)),
        (14, "总体分类精度 OA", f"{OA:.4f}"),
        (15, "分类 Kappa 系数", f"{KAP:.4f}"),
        (16, "所有待分类像元中类别 1 总个数", str(count_cls1)),
        (17, "所有待分类像元中类别 2 总个数", str(count_cls2)),
    ]
    # 写结果文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(f"{no},{label},{val}" for no, label, val in table_rows))

    # 返回字典：table_rows 供 GUI 渲染，其余字段供状态栏等使用
    return {
        "table_rows": table_rows,
        "count_cls1": count_cls1, "count_cls2": count_cls2,
        "OA": OA, "KAP": KAP,
    }


# ============================================================
# 第七部分：GUI 界面（通用型，换竞赛题只需改本部分最前面的配置）
# ============================================================
# 设计原则：
#   1. GUI 完全不接触计算逻辑，只调用 run_all() 获取 table_rows
#   2. 文件选择器由 FILE_CONFIG 配置驱动，增删文件类型只需改配置列表
#   3. 结果表格完全数据驱动，table_rows 有多少行就显示多少行
#   4. 换一道竞赛题，修改本部分标注了【竞赛题切换点】的位置即可
#
# 【竞赛题切换点汇总 - 第七部分共 4 处】
#   A. FILE_CONFIG —— 输入文件配置
#   B. OUTPUT_FILE  —— 默认输出文件名
#   C. 窗口标题      —— self.setWindowTitle()
#   D. 状态栏字段    —— _calc() 中 showMessage() 的参数
#
# 前两部分（第1-6部分）的切换点在 run_all() 函数体中已标注。
# ============================================================

# 【竞赛题切换点 A】输入文件配置。
#   每个元素为 (内部key, 界面显示名, 默认文件名)
#   换题时：增删改这里的条目即可，菜单/工具栏/文件对话框全部自动适配。
#   例如某题只有两个文件，改成：
#     FILE_CONFIG = [("data", "样本数据", "data.txt"), ("test", "测试数据", "test.txt")]
FILE_CONFIG = [
    ("train",  "训练样本",   "train.txt"),
    ("pixels", "待分类像元", "pixel.txt"),
    ("verify", "验证样本",   "verify.txt"),
]

# 【竞赛题切换点 B】默认输出文件名
OUTPUT_FILE = "mlc_result.txt"


class App(QMainWindow):
    """遥感影像最大似然法分类系统 —— 主窗口"""

    def __init__(self):
        super().__init__()
        # 【竞赛题切换点 C】窗口标题
        self.setWindowTitle("遥感影像最大似然法分类系统")
        self.resize(1100, 720)                # 初始窗口大小（宽×高）

        # 根据 FILE_CONFIG 初始化文件路径字典 {"train":"train.txt", ...}
        self._paths = {key: default for key, _, default in FILE_CONFIG}
        # 存放 run_all() 的 table_rows，None=尚未计算
        self._table_rows = None

        # 搭建界面五大组件
        self._setup_actions()      # 创建 QAction 对象
        self._setup_menubar()      # 菜单栏
        self._setup_toolbar()      # 工具栏
        self._setup_central()      # 中央区域（左侧信息+右侧表格）
        self.setStatusBar(QStatusBar())  # 底部状态栏

    # ==================== 界面搭建 ====================

    def _setup_actions(self):
        """创建所有动作对象并绑定信号-槽（通用：由 FILE_CONFIG 驱动）"""
        a = self
        # 文件选择动作 —— 由 FILE_CONFIG 动态生成
        self._file_acts = {}       # {key: QAction}，供菜单栏和工具栏引用
        for key, label, _ in FILE_CONFIG:
            act = QAction(label, a)
            # lambda 闭包使用默认参数 k=key 捕获当前 key 值（Python闭包经典陷阱）
            act.triggered.connect(lambda checked, k=key: self._open(k))
            self._file_acts[key] = act

        # 通用操作 —— 不随题目变化
        a.actCalc = QAction("计算", a)
        a.actCalc.triggered.connect(self._calc)
        a.actSave = QAction("导出", a)
        a.actSave.triggered.connect(self._save)
        a.actClear = QAction("清空", a)
        a.actClear.triggered.connect(self._clear)
        a.actExit = QAction("退出", a)
        a.actExit.triggered.connect(self.close)

    def _setup_menubar(self):
        """菜单栏：文件(&F) + 计算(&C)（通用：文件项由 FILE_CONFIG 驱动）"""
        mb = self.menuBar()
        a = self
        # 文件菜单
        menuF = mb.addMenu("文件(&F)")
        for key, label, _ in FILE_CONFIG:
            menuF.addAction(self._file_acts[key])  # 添加 FILE_CONFIG 中定义的文件项
        menuF.addSeparator()                       # ─── 分隔线 ───
        menuF.addAction(a.actSave)
        menuF.addSeparator()
        menuF.addAction(a.actClear)
        menuF.addSeparator()
        menuF.addAction(a.actExit)
        # 计算菜单
        mb.addMenu("计算(&C)").addAction(a.actCalc)

    def _setup_toolbar(self):
        """工具栏（通用：文件项由 FILE_CONFIG 驱动）"""
        tb = self.addToolBar("工具栏")
        a = self
        for key, label, _ in FILE_CONFIG:
            tb.addAction(self._file_acts[key])
        tb.addSeparator()
        tb.addAction(a.actCalc)
        tb.addSeparator()
        tb.addAction(a.actSave)
        tb.addAction(a.actClear)

    def _setup_central(self):
        """中央区域：左侧文件状态面板 + 右侧结果表格，用 QSplitter 可拖拽分割"""
        # ---- 左侧面板 ----
        self.labelFile = QLabel("未加载数据")    # 显示当前加载的文件信息
        gb = QGroupBox("输入参数")               # 分组框
        gb.setMinimumSize(220, 0)                # 最小宽度防挤压
        lay = QVBoxLayout(gb)                    # 垂直布局
        lay.addWidget(self.labelFile)

        # ---- 右侧表格 ----
        self.tableResult = QTableWidget()
        self.tableResult.setColumnCount(3)       # 序号 | 说明 | 计算结果
        self.tableResult.setHorizontalHeaderLabels(["序号", "说明", "计算结果"])
        h = self.tableResult.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 序号列自适应
        h.setSectionResizeMode(1, QHeaderView.Stretch)           # 说明列自动拉伸占满
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 结果列自适应

        # ---- 分割器 ----
        splitter = QSplitter(Qt.Horizontal)      # 水平分割（左右布局）
        splitter.addWidget(gb)                   # 左侧
        splitter.addWidget(self.tableResult)     # 右侧
        self.setCentralWidget(splitter)

    # ==================== 槽函数（用户操作响应） ====================

    def _open(self, kind):
        """
        通用文件打开对话框（零改动：从 FILE_CONFIG 获取当前文件信息）
        参数 kind 对应 FILE_CONFIG 中的 key
        """
        path, _ = QFileDialog.getOpenFileName(self, "", "", "文本文件 (*.txt);;所有文件 (*)")
        if not path:                             # 用户取消选择
            return
        self._paths[kind] = path                 # 更新该类型文件的路径
        # 动态生成文件状态文本（遍历 FILE_CONFIG，只显示文件名不含完整路径）
        lines = []
        for key, label, _ in FILE_CONFIG:
            filename = self._paths[key].split('/')[-1]
            lines.append(f"{label}: {filename}")
        self.labelFile.setText("\n".join(lines))

    def _calc(self):
        """
        执行计算并刷新表格（通用逻辑，只改动标注处）
        """
        # 【竞赛题切换点 D-1】run_all() 的调用。
        #   参数个数和顺序必须与当前 run_all() 签名一致。
        #   如果换题后 run_all 签名变了，修改此处的传参。
        r = run_all(self._paths["train"], self._paths["pixels"],
                    self._paths["verify"], OUTPUT_FILE)

        # 以下为通用表格渲染逻辑 —— run_all 返回什么就显示什么，零改动
        self._table_rows = r["table_rows"]       # 取表格数据
        t = self.tableResult
        t.setRowCount(len(self._table_rows))     # 行数 = 数据条数
        for i, (no, lb, val) in enumerate(self._table_rows):
            for j, text in enumerate([str(no), lb, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)  # 居中显示
                t.setItem(i, j, item)

        # 【竞赛题切换点 D-2】状态栏显示内容。
        #   如果换题后 run_all 返回的字段名变了，修改此处的 f-string。
        self.statusBar().showMessage(
            f"完成 | 类别1={r['count_cls1']} 类别2={r['count_cls2']} | OA={r['OA']:.4f} Kappa={r['KAP']:.4f}")

    def _save(self):
        """导出结果为 CSV 文件（通用逻辑，零改动）"""
        if not self._table_rows:                 # 还没算过，不导出
            return
        path, _ = QFileDialog.getSaveFileName(self, "", OUTPUT_FILE, "文本文件 (*.txt)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("序号,指标名称,计算结果\n")    # CSV 表头
            for no, lb, val in self._table_rows:
                f.write(f"{no},{lb},{val}\n")

    def _clear(self):
        """清空所有状态，恢复到初始界面（通用逻辑，零改动）"""
        self._paths = {key: default for key, _, default in FILE_CONFIG}  # 恢复默认路径
        self._table_rows = None
        self.tableResult.setRowCount(0)          # 清空表格
        self.labelFile.setText("未加载数据")


# ============================================================
# 程序入口（两套入口，使用时只保留一套，注释掉另一套）
# ============================================================

# --- 入口A：纯计算模式（无GUI，直接运行出结果）---
# if __name__ == "__main__":
#     r = run_all()
#     print("计算完成，结果已写入 mlc_result.txt")
#     print(f"类别1像元数={r['count_cls1']}  类别2像元数={r['count_cls2']}")
#     print(f"OA={r['OA']:.4f}  Kappa={r['KAP']:.4f}")

# --- 入口B：GUI界面模式（需要PyQt5）---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
