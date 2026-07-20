# file_io.py
# 读取 ransac_3dline.txt，输出 ransac_3d_result.txt（24项）
# 支持两种格式：
#   格式A（原始）：x,y,z
#   格式B（新）：  点号,x,y,z

from calculator import Point3D, RANSACCalculator


def read_input(filepath: str) -> RANSACCalculator:
    """
    读取 ransac_3dline.txt，自动识别格式：
      格式A：x,y,z         （3列数字）
      格式B：P1,x,y,z      （4列，第1列为点号）
    跳过 # 注释行和空行。
    """
    calc = RANSACCalculator()
    idx  = 1
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")

            # 格式B：4列，第1列为点号（如 P1）
            if len(parts) == 4:
                try:
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    z = float(parts[3].strip())
                except ValueError:
                    continue

            # 格式A：3列纯数字
            elif len(parts) == 3:
                try:
                    x = float(parts[0].strip())
                    y = float(parts[1].strip())
                    z = float(parts[2].strip())
                except ValueError:
                    continue

            else:
                continue

            calc.points.append(Point3D(idx, x, y, z))
            idx += 1

    if not calc.points:
        raise ValueError("文件为空或格式错误，支持 x,y,z 或 点号,x,y,z 两种格式")
    return calc


def write_result(filepath: str, calc: RANSACCalculator):
    """
    输出 ransac_3d_result.txt（24项）
    """
    res = calc.result
    rows = [
        (1,  "三维观测点总数量",           str(res.total_pts)),
        (2,  "距离阈值T",                  f"{calc.T:.4f}"),
        (3,  "最大迭代次数Kmax",            str(calc.K_MAX)),
        (4,  "最优直线基准点x0",            f"{res.x0:.4f}"),
        (5,  "最优直线基准点y0",            f"{res.y0:.4f}"),
        (6,  "最优直线基准点z0",            f"{res.z0:.4f}"),
        (7,  "最优直线方向向量ux",          f"{res.ux:.4f}"),
        (8,  "最优直线方向向量uy",          f"{res.uy:.4f}"),
        (9,  "最优直线方向向量uz",          f"{res.uz:.4f}"),
        (10, "最优模型内点总数",            str(res.inlier_count)),
        (11, "粗差外点总个数",              str(res.outlier_count)),
        (12, "1号点到最优直线距离",         f"{res.dist_pt1:.4f}"),
        (13, "7号粗差点到最优直线距离",     f"{res.dist_pt7:.4f}"),
        (14, "最优内点集x坐标平均值",       f"{res.inlier_x_mean:.4f}"),
        (15, "最优内点集y坐标平均值",       f"{res.inlier_y_mean:.4f}"),
        (16, "最优内点集z坐标平均值",       f"{res.inlier_z_mean:.4f}"),
        (17, "全部粗差点编号集合",          res.outlier_ids),
        (18, "最优模型对应迭代轮次",        str(res.best_iter)),
        (19, "内点x坐标最小值",             f"{res.inlier_x_min:.4f}"),
        (20, "内点z坐标最大值",             f"{res.inlier_z_max:.4f}"),
        (21, "第一次抽样直线方向向量ux",    f"{res.first_ux:.4f}"),
        (22, "第一次抽样得到的内点数量",    str(res.first_inlier_count)),
        (23, "所有粗差点三维坐标均值",      res.outlier_xyz_mean),
        (24, "内点占全部三维测点比例",      f"{res.inlier_ratio:.4f}"),
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,指标名称,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
