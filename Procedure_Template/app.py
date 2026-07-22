# app.py
# 主程序 — 连接界面 + 算法 + 文件读写
# ============================================================
# 【使用说明】
#   框架内嵌两套完整可运行示例（均已注释）：
#   示例A: 道路曲线（简单，13项输出）
#   示例B: 激光点云（复杂，43项输出，含多阶段计算）
#   做你的题目时: 取消最接近的示例注释 → 跑通 → 替换
# ============================================================

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

# 由 pyuic5 从 main_window.ui 自动生成
from main_window_ui import Ui_MainWindow

# 手写模块
from calculator import Calculator    # <FILL: 你的类名>
import file_io


# ============================================================
#  可选：辅助函数
# ============================================================

# 示例A: 桩号格式化 1326.480 → "K1+326.480"
# def format_stake(v: float) -> str:
#     km = int(v / 1000); m = v - km*1000
#     return f"K{km}+{m:.3f}"

# 示例B: 坐标极值（也可放在 calculator.py 中）
# def compute_stats(points):
#     xs = [p.x for p in points]
#     ys = [p.y for p in points]
#     zs = [p.z for p in points]
#     return {"xmin":min(xs),"xmax":max(xs),"ymin":min(ys),"ymax":max(ys),"zmin":min(zs),"zmax":max(zs)}


# ============================================================
#  App 主窗口
# ============================================================

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()       # 界面类（pyuic5生成）
        self.ui.setupUi(self)           # 安装界面

        self._data = None               # 原始输入
        self._results = None            # 计算结果

        self._setup_table()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开输入文件")

    # ============================================================
    #  表格设置 — 所有题目照抄，不动
    # ============================================================

    def _setup_table(self):
        t = self.ui.tableResult
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["序号", "说明", "计算结果"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.setFont(QFont("Consolas", 10))

    # ============================================================
    #  信号连接 — 所有题目照抄，不动
    # ============================================================

    def _connect_signals(self):
        self.ui.actionOpen.triggered.connect(self.slot_open)
        self.ui.actionCalc.triggered.connect(self.slot_calc)
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ============================================================
    #  slot_open — 响应"打开"
    # ============================================================

    def slot_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开输入文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._data = file_io.parse_input(path)
            self._results = None
            self.ui.tableResult.setRowCount(0)

            # ===== 更新左侧信息 QLabel =====
            # 对照 main_window.ui 中每个 QLabel 的 objectName

            # --- 示例A: 道路曲线 ---
            # c = self._data
            # self.ui.labelFile.setText(
            #     f"文件: {path.split('/')[-1]}\n"
            #     f"JD={c.JD_stake:.3f}  R={c.R:.0f}m\n"
            #     f"α={c.alpha_deg_raw}°{c.alpha_min_raw}'{c.alpha_sec_raw}\""
            # )
            # self.ui.labelStatus.setText("已加载  |  请点击「计算」")
            # # 也可以把数据填到 QLineEdit 中（如果有手动输入框）
            # self.ui.edit_jd.setText(str(c.JD_stake))
            # self.ui.edit_r.setText(str(int(c.R)))
            # self.ui.edit_deg.setText(str(int(c.alpha_deg_raw)))
            # self.ui.edit_min.setText(str(int(c.alpha_min_raw)))
            # self.ui.edit_sec.setText(str(c.alpha_sec_raw))

            # --- 示例B: 激光点云 ---
            # points = self._data   # [Point, ...]
            # from calculator import Point    # 如果类在 calculator 中
            # xs = [p.x for p in points]
            # ys = [p.y for p in points]
            # zs = [p.z for p in points]
            # self.ui.labelFile.setText(
            #     f"文件: {path.split('/')[-1]}\n"
            #     f"点云数量: {len(points)}"
            # )
            # self.ui.labelStatus.setText(
            #     f"坐标范围:\n"
            #     f"x: {min(xs):.3f} ~ {max(xs):.3f}\n"
            #     f"y: {min(ys):.3f} ~ {max(ys):.3f}\n"
            #     f"z: {min(zs):.3f} ~ {max(zs):.3f}"
            # )

            # <FILL: 更新你的 QLabel>

            self.statusBar().showMessage(f"已加载: {path}  |  请点击「计算」")
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    # ============================================================
    #  slot_calc — 响应"计算"
    # ============================================================

    def slot_calc(self):
        if not self._data:
            QMessageBox.warning(self, "提示", "请先打开输入文件")
            return
        try:
            self.statusBar().showMessage("计算中，请稍候...")
            QApplication.processEvents()

            # ===== 执行计算 =====

            # --- 示例A: 道路曲线（单对象，compute_all）---
            # curve = self._data
            # # 如果界面有手动输入框，也可以从 QLineEdit 读取:
            # # curve = Calculator(
            # #     float(self.ui.edit_jd.text()),
            # #     float(self.ui.edit_r.text()),
            # #     float(self.ui.edit_deg.text()),
            # #     float(self.ui.edit_min.text()),
            # #     float(self.ui.edit_sec.text()),
            # # )
            # stake_text = self.ui.edit_stake.text().strip()
            # curve.compute_all(float(stake_text) if stake_text else None)
            # self._results = curve

            # --- 示例B: 激光点云（多阶段，run 方法）---
            # from calculator import Calculator_B
            # proc = Calculator_B(self._data)     # self._data = [Point, ...]
            # proc.run()
            # self._results = proc

            # --- 示例: 大地主题（多组任务循环）---
            # results = []
            # for task in self._data['tasks']:
            #     calc = Calculator(...)
            #     calc.compute_all()
            #     results.append(calc)
            # self._results = results

            # <FILL: 你的计算逻辑>

            self._fill_table()
            self.statusBar().showMessage("计算完成")
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    # ============================================================
    #  slot_save — 响应"保存"
    # ============================================================

    def slot_save(self):
        if not self._results:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "result.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            # --- 示例A: 道路曲线（单个对象直接传入）---
            # file_io.write_result(path, self._results)

            # --- 示例B: 激光点云（处理器对象直接传入）---
            # file_io.write_result(path, self._results)

            # --- 示例: 大地主题（循环多个结果）---
            # for r in self._results:
            #     file_io.write_result(path, r)

            # <FILL: file_io.write_result(path, self._results)>
            file_io.write_result(path, self._results)

            self.statusBar().showMessage(f"结果已保存: {path}")
            QMessageBox.information(self, "保存成功", f"文件已保存:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    # ============================================================
    #  slot_clear — 响应"清除"
    # ============================================================

    def slot_clear(self):
        self._data = None
        self._results = None
        self.ui.tableResult.setRowCount(0)

        # --- 示例A: 道路曲线（复原 QLabel + QLineEdit）---
        # self.ui.labelFile.setText("未加载数据")
        # self.ui.labelStatus.setText("请打开输入文件")
        # self.ui.edit_jd.setText("")
        # self.ui.edit_r.setText("")
        # self.ui.edit_deg.setText("")
        # self.ui.edit_min.setText("")
        # self.ui.edit_sec.setText("")
        # self.ui.edit_stake.setText("")

        # --- 示例B: 激光点云（只复原 QLabel）---
        # self.ui.labelFile.setText("未加载数据")
        # self.ui.labelStatus.setText("点云数量: -\n坐标范围:\nx: - ~ -\ny: - ~ -\nz: - ~ -")

        # <FILL: 复位你的 QLabel>

        self.statusBar().showMessage("已清除")

    # ============================================================
    #  _fill_table — 填表（评分关键! 名称必须与试题册逐字一致）
    # ============================================================

    def _fill_table(self):
        rows = []

        # ============================================================
        #  示例A: 道路曲线 — 13项
        # ============================================================
        # c = self._results
        # # 桩号格式化辅助
        # def fs(v): km=int(v/1000); return f"K{km}+{v-km*1000:.3f}"
        # rows = [
        #     ("1",  "JD原始里程",          f"{c.JD_stake:.3f}"),
        #     ("2",  "圆曲线半径R",         f"{c.R:.0f}"),
        #     ("3",  "路偏角α(十进制度)",   f"{c.alpha_deg:.4f}"),
        #     ("4",  "切线长T",             f"{c.T:.3f}"),
        #     ("5",  "曲线总长L",           f"{c.L:.3f}"),
        #     ("6",  "外距E",               f"{c.E:.3f}"),
        #     ("7",  "校差值D",             f"{c.D:.3f}"),
        #     ("8",  "直圆点ZY里程",        fs(c.ZY)),
        #     ("9",  "曲中点QZ里程",        fs(c.QZ)),
        #     ("10", "圆直点YZ里程",        fs(c.YZ)),
        #     ("11", "校核JD里程",          f"{c.JD_check:.3f}"),
        #     ("12", "指定桩号距ZY弧长l",   f"{c.l:.3f}" if c.l else "（未指定）"),
        #     ("13", "指定桩号局部坐标(x,y)",
        #      f"{c.x:.3f}, {c.y:.3f}" if c.l else "（未指定）"),
        # ]

        # ============================================================
        #  示例B: 激光点云 — 43项（篇幅原因只展示结构，完整版见原项目 app.py）
        # ============================================================
        # p = self._results
        # p5 = p.points[4]; s = p.stats; s1 = p.plane_S1
        # j1 = p.plane_J1; j2 = p.plane_J2
        # rows = [
        #     # 1-9: 基本统计
        #     ("1", "P5的坐标分量x",            f"{p5.x:.3f}"),
        #     ("2", "P5的坐标分量y",            f"{p5.y:.3f}"),
        #     ("3", "P5的坐标分量z",            f"{p5.z:.3f}"),
        #     ("4", "坐标分量x的最小值xmin",     f"{s['xmin']:.3f}"),
        #     ("5", "坐标分量x的最大值xmax",     f"{s['xmax']:.3f}"),
        #     ("6", "坐标分量y的最小值ymin",     f"{s['ymin']:.3f}"),
        #     ("7", "坐标分量y的最大值ymax",     f"{s['ymax']:.3f}"),
        #     ("8", "坐标分量z的最小值zmin",     f"{s['zmin']:.3f}"),
        #     ("9", "坐标分量z的最大值zmax",     f"{s['zmax']:.3f}"),
        #     # 10-16: 栅格C（7项）
        #     # ... 根据试题册要求逐项填充
        #     # 17-25: S1平面（9项）
        #     # ...
        #     # 26-31: J1分割平面（6项）
        #     # ...
        #     # 32-37: J2分割平面（6项）
        #     # ...
        #     # 38-43: 投影坐标（6项）
        #     ("38", "P5到J1的投影坐标xt",      f"{p.P5_proj_J1[0]:.3f}"),
        #     ("39", "P5到J1的投影坐标yt",      f"{p.P5_proj_J1[1]:.3f}"),
        #     ("40", "P5到J1的投影坐标zt",      f"{p.P5_proj_J1[2]:.3f}"),
        #     ("41", "P800到J2的投影坐标xt",    f"{p.P800_proj_J2[0]:.3f}"),
        #     ("42", "P800到J2的投影坐标yt",    f"{p.P800_proj_J2[1]:.3f}"),
        #     ("43", "P800到J2的投影坐标zt",    f"{p.P800_proj_J2[2]:.3f}"),
        # ]

        # ============================================================
        #  示例: 大地主题 — 多组逐组拼装
        # ============================================================
        # for i, r in enumerate(self._results):
        #     n = i * 9 + 1
        #     rows.append((f"{n}",   "计算模式标志",      f"{r['mode']}"))
        #     rows.append((f"{n+1}", "起点纬度B1",        f"{r['B1']:.6f}"))
        #     rows.append((f"{n+2}", "起点经度L1",        f"{r['L1']:.6f}"))
        #     # ...

        # <FILL: 取消上面适合你题目的示例，替换 rows 定义>

        # ---- 填表（照抄，不动）----
        t = self.ui.tableResult
        t.setRowCount(len(rows))          # 必须先设行数
        colors = [QColor(230, 245, 255), QColor(255, 255, 255)]

        for row, (no, label, val) in enumerate(rows):
            bg = colors[row % 2]
            for col, text in enumerate([no, label, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)


# ============================================================
#  程序入口 — 所有题目照抄
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
