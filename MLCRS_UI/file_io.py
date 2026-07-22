# file_io.py
# 读取 train.txt / pixel.txt / verify.txt
# 输出 mlc_result.txt（17项）

from calculator import MLClassifier, compute_oa, compute_kappa, _mat_det


def _parse_line(line: str):
    """解析逗号分隔的浮点数行，返回数值列表"""
    parts = line.strip().split(",")
    return [float(p.strip()) for p in parts if p.strip()]


def read_train(filepath: str, calc: MLClassifier):
    """
    读取 train.txt。
    格式：类别编号,波段1,波段2,波段3,波段4
    """
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            vals = _parse_line(line)
            if len(vals) < 5:
                continue
            cls_id = int(vals[0])
            calc.add_train(cls_id, vals[1:5])
            count += 1
    if count == 0:
        raise ValueError("train.txt 为空或格式错误")


def read_pixels(filepath: str, calc: MLClassifier):
    """
    读取 pixel.txt。
    格式：波段1,波段2,波段3,波段4
    """
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            vals = _parse_line(line)
            if len(vals) < 4:
                continue
            count += 1
            calc.add_pixel(count, vals[0:4])
    if count == 0:
        raise ValueError("pixel.txt 为空或格式错误")


def read_verify(filepath: str, calc: MLClassifier):
    """
    读取 verify.txt。
    格式同 train.txt：类别编号,波段1,波段2,波段3,波段4
    """
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            vals = _parse_line(line)
            if len(vals) < 5:
                continue
            cls_id = int(vals[0])
            calc.add_verify(cls_id, vals[1:5])
            count += 1
    return count


def write_result(filepath: str, calc: MLClassifier):
    """
    输出 mlc_result.txt（17项）。
    """
    st1 = calc.stats_map[1]
    st2 = calc.stats_map[2]
    det1 = _mat_det(st1.cov)
    det2 = _mat_det(st2.cov)
    r1 = calc.results[0]

    # 验证精度
    oa = compute_oa(calc.cm) if calc.cm else 0.0
    kappa = compute_kappa(calc.cm) if calc.cm else 0.0
    diag_sum = sum(calc.cm.matrix[c][c] for c in calc.cm.class_ids) if calc.cm else 0
    v_total = calc.cm.total if calc.cm else 0

    # 分类统计
    cls1_count = sum(1 for r in calc.results if r.pred_class == 1)
    cls2_count = sum(1 for r in calc.results if r.pred_class == 2)

    rows = [
        (1,  "类别1训练样本总数",              str(st1.count)),
        (2,  "类别1波段1均值",                 f"{st1.mean[0]:.4f}"),
        (3,  "类别1波段2均值",                 f"{st1.mean[1]:.4f}"),
        (4,  "类别1协方差矩阵行列式",          f"{det1:.6e}"),
        (5,  "类别2训练样本总数",              str(st2.count)),
        (6,  "类别2波段1均值",                 f"{st2.mean[0]:.4f}"),
        (7,  "类别2波段2均值",                 f"{st2.mean[1]:.4f}"),
        (8,  "类别2协方差矩阵行列式",          f"{det2:.6e}"),
        (9,  "第1个待分类像元类别1对数似然值", f"{r1.likelihoods.get(1, 0):.6f}"),
        (10, "第1个待分类像元类别2对数似然值", f"{r1.likelihoods.get(2, 0):.6f}"),
        (11, "第1个待分类像元最终分类类别",    str(r1.pred_class)),
        (12, "验证样本总数量",                 str(v_total)),
        (13, "混淆矩阵对角线正确样本总数",     str(diag_sum)),
        (14, "总体分类精度OA",                 f"{oa:.4f}"),
        (15, "分类Kappa系数",                  f"{kappa:.4f}"),
        (16, "所有待分类像元中类别1总个数",    str(cls1_count)),
        (17, "所有待分类像元中类别2总个数",    str(cls2_count)),
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,指标名称,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
