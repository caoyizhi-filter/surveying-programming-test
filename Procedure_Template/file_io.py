# file_io.py
# 文件读写模块 — 读取输入文件，写出结果文件
# ============================================================
# 【使用说明】
#   框架内嵌两套完整可运行示例（均已注释）：
#   示例A: 道路曲线 — 单行制表符分隔
#   示例B: 激光点云 — 多行逗号分隔 + 数据类
#   做你的题目时: 取消最接近的示例注释 → 跑通 → 替换
# ============================================================

from calculator import Calculator      # 主计算器类
# from calculator import Point         # 示例B需要: 取消注释


# ============================================================
#  读取输入文件
# ============================================================

def parse_input(filepath: str):
    """
    打开文件 → 解析 → 返回结构化数据

    参数: filepath = 文件路径（app.py 的文件对话框提供）
    返回: 根据题目而定（Calculator 对象 或 dict 或 list）

    ╔══════════════════════════════════════════════════════════╗
    ║  示例A: 道路曲线 — 单行，制表符+逗号                    ║
    ║  输入:  1\t1326.480,280,32,16,42                        ║
    ║  返回:  Calculator 对象                                  ║
    ╚══════════════════════════════════════════════════════════╝
    """
    # ---- 步骤1-2: 读所有非空行 ----
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # ---- 步骤3: 检查空文件 ----
    if not lines:
        raise ValueError("输入文件为空")

    # ============================================================
    # 示例A: 道路曲线
    #   raw = lines[0]                     # "1\t1326.480,280,32,16,42"
    #   parts = raw.split("\t")            # ["1", "1326.480,280,32,16,42"]
    #   if len(parts) >= 2:
    #       data = parts[1].split(",")     # ["1326.480", "280", "32", "16", "42"]
    #   else:
    #       data = parts[0].split(",")     # 兼容无序号格式
    #   JD_stake  = float(data[0])
    #   R         = float(data[1])
    #   alpha_deg = float(data[2])
    #   alpha_min = float(data[3])
    #   alpha_sec = float(data[4])
    #   return Calculator(JD_stake, R, alpha_deg, alpha_min, alpha_sec)
    # ============================================================

    # ============================================================
    # 示例B: 激光点云
    #   count = int(lines[0].strip())      # 第1行: 点数量
    #   points = []
    #   for line in lines[1:]:
    #       parts = line.split(",")        # "P1,1234.567,5678.901,12.345"
    #       name = parts[0].strip()
    #       x = float(parts[1])
    #       y = float(parts[2])
    #       z = float(parts[3])
    #       points.append(Point(name, x, y, z))
    #   if len(points) != count:
    #       raise ValueError(f"点数不匹配: 期望{count}, 实际{len(points)}")
    #   return points
    # ============================================================

    # ============================================================
    # 备用示例: 大地主题 — 多行+字符标记+模式自动识别
    #   ell_parts = lines[0].split(',')
    #   ellipsoid = (float(ell_parts[0]), float(ell_parts[1]))
    #   tasks = []
    #   for line in lines[1:]:
    #       tokens = line.split(',')
    #       numbers = []
    #       for t in tokens:
    #           try:
    #               numbers.append(float(t))     # 能转 float = 数值
    #           except ValueError:
    #               pass                         # 不能转 = 字符标记(P1,P2)，跳过
    #       # 通过 P2 位置判断模式: P2在末尾 → 正算, P2在中间 → 反算
    #       p2_idx = next((i for i,t in enumerate(tokens) if t.strip().upper()=='P2'), -1)
    #       mode = 1 if p2_idx >= 5 else 2
    #       tasks.append({'mode': mode, 'params': numbers})
    #   return {'ellipsoid': ellipsoid, 'tasks': tasks}
    # ============================================================

    # <FILL: 取消上面适合你题目的示例，按需修改>
    pass


# ============================================================
#  写出结果文件
# ============================================================

def write_result(filepath: str, result):
    """
    按试题册格式写出计算结果。
    格式: 序号,指标名称,计算结果

    【小数位数】角度 .6f / 长度 .3f / 面积 .3f / 坐标 .3f / 整数无f
    """
    rows = []

    # ============================================================
    # 示例A: 道路曲线 — 13项固定输出
    #   c = result   # Calculator 实例
    #   rows = [
    #       (1,  "JD原始里程",          f"{c.JD_stake:.3f}"),
    #       (2,  "圆曲线半径R",         f"{c.R:.0f}"),
    #       (3,  "路偏角α(十进制度)",   f"{c.alpha_deg:.4f}"),
    #       (4,  "切线长T",             f"{c.T:.3f}"),
    #       (5,  "曲线总长L",           f"{c.L:.3f}"),
    #       (6,  "外距E",               f"{c.E:.3f}"),
    #       (7,  "校差值D",             f"{c.D:.3f}"),
    #       (8,  "直圆点ZY里程",        f"{c.ZY:.3f}"),
    #       (9,  "曲中点QZ里程",        f"{c.QZ:.3f}"),
    #       (10, "圆直点YZ里程",        f"{c.YZ:.3f}"),
    #       (11, "校核JD里程",          f"{c.JD_check:.3f}"),
    #       (12, "指定桩号距ZY弧长l",   f"{c.l:.3f}" if c.l else "（未指定）"),
    #       (13, "指定桩号局部坐标(x,y)", f"{c.x:.3f},{c.y:.3f}" if c.l else "（未指定）"),
    #   ]
    # ============================================================

    # ============================================================
    # 示例B: 激光点云 — 43项固定输出（篇幅原因只列前9+后6，完整43项见原项目 app.py）
    #   p = result    # Calculator_B 实例
    #   p5 = p.points[4]
    #   s = p.stats
    #   rows = [
    #       ("1",  "P5的坐标分量x",             f"{p5.x:.3f}"),
    #       ("2",  "P5的坐标分量y",             f"{p5.y:.3f}"),
    #       ("3",  "P5的坐标分量z",             f"{p5.z:.3f}"),
    #       ("4",  "坐标分量x的最小值xmin",     f"{s['xmin']:.3f}"),
    #       ("5",  "坐标分量x的最大值xmax",     f"{s['xmax']:.3f}"),
    #       ("6",  "坐标分量y的最小值ymin",     f"{s['ymin']:.3f}"),
    #       ("7",  "坐标分量y的最大值ymax",     f"{s['ymax']:.3f}"),
    #       ("8",  "坐标分量z的最小值zmin",     f"{s['zmin']:.3f}"),
    #       ("9",  "坐标分量z的最大值zmax",     f"{s['zmax']:.3f}"),
    #       # ... 10-37: 栅格统计(7项) + S1平面(9项) + J1平面(6项) + J2平面(6项)
    #       # ... 38-43: 投影坐标(6项)
    #       ("38", "P5到J1的投影坐标xt",        f"{p.P5_proj_J1[0]:.3f}"),
    #       ("39", "P5到J1的投影坐标yt",        f"{p.P5_proj_J1[1]:.3f}"),
    #       ("40", "P5到J1的投影坐标zt",        f"{p.P5_proj_J1[2]:.3f}"),
    #       ("41", "P800到J2的投影坐标xt",      f"{p.P800_proj_J2[0]:.3f}"),
    #       ("42", "P800到J2的投影坐标yt",      f"{p.P800_proj_J2[1]:.3f}"),
    #       ("43", "P800到J2的投影坐标zt",      f"{p.P800_proj_J2[2]:.3f}"),
    #   ]
    # ============================================================

    # ============================================================
    # 备用示例: 大地主题 — 多组逐个拼装 + 全点输出
    #   for i, r in enumerate(all_results):
    #       n = i * 9 + 1
    #       rows.append((f"{n}",   "计算模式标志",    f"{r['mode']}"))
    #       rows.append((f"{n+1}", "起点纬度B1",      f"{r['B1']:.6f}"))
    #       # ...
    # ============================================================

    # ============================================================
    # 备用示例: 点云标签文件 — 每点一行
    #   with open(filepath, "w", encoding="utf-8") as f:
    #       f.write("点名,X,Y,Z,标识\n")
    #       for pt in proc.points:
    #           f.write(f"{pt.name},{pt.x:.3f},{pt.y:.3f},{pt.z:.3f},{proc.get_label(pt)}\n")
    #       return   # 提前返回，不执行下面的通用表头写法
    # ============================================================

    # <FILL: 取消上面适合你题目的 rows，按需修改>

    # ---- 通用写入（照抄）----
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("序号,指标名称,计算结果\n")
        for no, label, val in rows:
            f.write(f"{no},{label},{val}\n")
