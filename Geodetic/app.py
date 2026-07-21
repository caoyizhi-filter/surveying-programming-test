# app.py
# 大地主题正反算 — 主程序

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from main_window_ui import Ui_MainWindow
from calculator import Ellipsoid, GeodeticSolver
import file_io


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._data_direct = None     # 正算数据
        self._data_inverse = None    # 反算数据
        self._results_direct = []    # 正算结果
        self._results_inverse = []   # 反算结果

        self._setup_tables()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开正算或反算文件")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_tables(self):
        for t in [self.ui.tableDirect, self.ui.tableInverse]:
            t.setColumnCount(3)
            t.setHorizontalHeaderLabels(["序号", "指标名称", "计算结果"])
            t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            t.setFont(QFont("Consolas", 10))

    def _connect_signals(self):
        self.ui.actionOpenDirect.triggered.connect(self.slot_open_direct)
        self.ui.actionOpenInverse.triggered.connect(self.slot_open_inverse)
        self.ui.actionCalc.triggered.connect(self.slot_calc)
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open_direct(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开正算文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._data_direct = file_io.parse_input(path)
            self._results_direct = []
            self.ui.tableDirect.setRowCount(0)

            ell = self._data_direct['ellipsoid']
            tasks = self._data_direct['tasks']

            self.ui.labelEll.setText(
                f"a = {ell[0]:.0f} m    1/f = {ell[1]:.1f}    "
                f"e² = {2.0/ell[1] - 1.0/(ell[1]*ell[1]):.6f}"
            )
            self.ui.labelFileInfo.setText(f"正算文件: {path.split('/')[-1]}  ({len(tasks)} 组数据)")

            lines = []
            for i, t in enumerate(tasks):
                p = t['params']
                lines.append(
                    f"第{i+1}组: B1={p[0]:.6f}°  L1={p[1]:.6f}°  "
                    f"A12={p[2]:.6f}°  S={p[3]:.3f} m")
            self.ui.labelDirectInput.setText("\n".join(lines))

            self.ui.tabWidget.setCurrentIndex(0)
            self.ui.labelIterInfo.setText("迭代信息: 待计算")
            self.statusBar().showMessage(
                f"已加载正算文件: {len(tasks)} 组数据  |  请点击「执行计算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_open_inverse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开反算文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._data_inverse = file_io.parse_input(path)
            self._results_inverse = []
            self.ui.tableInverse.setRowCount(0)

            ell = self._data_inverse['ellipsoid']
            tasks = self._data_inverse['tasks']

            self.ui.labelEll.setText(
                f"a = {ell[0]:.0f} m    1/f = {ell[1]:.1f}    "
                f"e² = {2.0/ell[1] - 1.0/(ell[1]*ell[1]):.6f}"
            )
            self.ui.labelFileInfo.setText(f"反算文件: {path.split('/')[-1]}  ({len(tasks)} 组数据)")

            lines = []
            for i, t in enumerate(tasks):
                p = t['params']
                lines.append(
                    f"第{i+1}组: B1={p[0]:.6f}°  L1={p[1]:.6f}°  "
                    f"B2={p[2]:.6f}°  L2={p[3]:.6f}°")
            self.ui.labelInverseInput.setText("\n".join(lines))

            self.ui.tabWidget.setCurrentIndex(1)
            self.ui.labelIterInfo.setText("迭代信息: 待计算")
            self.statusBar().showMessage(
                f"已加载反算文件: {len(tasks)} 组数据  |  请点击「执行计算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_calc(self):
        has_direct = self._data_direct is not None
        has_inverse = self._data_inverse is not None

        if not has_direct and not has_inverse:
            QMessageBox.warning(self, "提示", "请先打开数据文件")
            return

        try:
            self.statusBar().showMessage("计算中，请稍候...")
            QApplication.processEvents()

            iter_summary = []

            # ── 正算 ──
            if has_direct:
                ell = Ellipsoid(*self._data_direct['ellipsoid'])
                solver = GeodeticSolver(ell)
                self._results_direct = []

                for task in self._data_direct['tasks']:
                    p = task['params']
                    B2, L2, A21, it = solver.solve_direct(p[0], p[1], p[2], p[3])
                    self._results_direct.append({
                        'B1': p[0], 'L1': p[1], 'A12': p[2], 'S': p[3],
                        'B2': B2, 'L2': L2, 'A21': A21, 'iter': it
                    })

                self._fill_direct_table()
                for i, r in enumerate(self._results_direct):
                    iter_summary.append(f"正算第{i+1}组: {r['iter']} 次迭代")

            # ── 反算 ──
            if has_inverse:
                ell = Ellipsoid(*self._data_inverse['ellipsoid'])
                solver = GeodeticSolver(ell)
                self._results_inverse = []

                for task in self._data_inverse['tasks']:
                    p = task['params']
                    S, A12, A21, it = solver.solve_inverse(p[0], p[1], p[2], p[3])
                    self._results_inverse.append({
                        'B1': p[0], 'L1': p[1], 'B2': p[2], 'L2': p[3],
                        'S': S, 'A12': A12, 'A21': A21, 'iter': it
                    })

                self._fill_inverse_table()
                for i, r in enumerate(self._results_inverse):
                    iter_summary.append(f"反算第{i+1}组: {r['iter']} 次迭代")

            self.ui.labelIterInfo.setText("迭代信息: " + "  |  ".join(iter_summary))

            total = len(self._results_direct) + len(self._results_inverse)
            self.statusBar().showMessage(f"计算完成  |  {total} 组结果")
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_save(self):
        all_results = self._results_direct + self._results_inverse
        if not all_results:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "geodetic_result.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("序号,指标名称,计算结果\n")
                offset = 0
                for r in self._results_direct:
                    rows = [
                        (1, "计算模式标志", "1"),
                        (2, "起点纬度B1", f"{r['B1']:.6f}"),
                        (3, "起点经度L1", f"{r['L1']:.6f}"),
                        (4, "起始大地方位角A12", f"{r['A12']:.6f}"),
                        (5, "大地线长度S", f"{r['S']:.3f}"),
                        (6, "终点纬度B2", f"{r['B2']:.6f}"),
                        (7, "终点经度L2", f"{r['L2']:.6f}"),
                        (8, "终点反方位角A21", f"{r['A21']:.6f}"),
                        (9, "迭代总次数", f"{r['iter']}"),
                    ]
                    for no, label, val in rows:
                        f.write(f"{no + offset},{label},{val}\n")
                    offset += 9
                for r in self._results_inverse:
                    rows = [
                        (1, "计算模式标志", "2"),
                        (2, "起点纬度B1", f"{r['B1']:.6f}"),
                        (3, "起点经度L1", f"{r['L1']:.6f}"),
                        (4, "终点纬度B2", f"{r['B2']:.6f}"),
                        (5, "终点经度L2", f"{r['L2']:.6f}"),
                        (6, "大地线长度S", f"{r['S']:.3f}"),
                        (7, "正方位角A12", f"{r['A12']:.6f}"),
                        (8, "反方位角A21", f"{r['A21']:.6f}"),
                        (9, "迭代总次数", f"{r['iter']}"),
                    ]
                    for no, label, val in rows:
                        f.write(f"{no + offset},{label},{val}\n")
                    offset += 9
            self.statusBar().showMessage(f"结果已保存: {path}")
            QMessageBox.information(self, "保存成功", f"文件已保存:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def slot_clear(self):
        self._data_direct = None
        self._data_inverse = None
        self._results_direct = []
        self._results_inverse = []
        self.ui.tableDirect.setRowCount(0)
        self.ui.tableInverse.setRowCount(0)
        self.ui.labelEll.setText("椭球参数: 未加载")
        self.ui.labelFileInfo.setText("")
        self.ui.labelDirectInput.setText("输入数据: 请读取正算文件")
        self.ui.labelInverseInput.setText("输入数据: 请读取反算文件")
        self.ui.labelIterInfo.setText("迭代信息: -")
        self.statusBar().showMessage("已清除")

    # ── 填充正算表格 ──────────────────────────────────────────

    def _fill_direct_table(self):
        rows = []
        for ri, r in enumerate(self._results_direct):
            rows.extend([
                (f"{ri*9+1}", "计算模式标志", "1"),
                (f"{ri*9+2}", "起点纬度 B1", f"{r['B1']:.6f}"),
                (f"{ri*9+3}", "起点经度 L1", f"{r['L1']:.6f}"),
                (f"{ri*9+4}", "起始大地方位角 A12", f"{r['A12']:.6f}"),
                (f"{ri*9+5}", "大地线长度 S", f"{r['S']:.3f}"),
                (f"{ri*9+6}", "终点纬度 B2", f"{r['B2']:.6f}"),
                (f"{ri*9+7}", "终点经度 L2", f"{r['L2']:.6f}"),
                (f"{ri*9+8}", "终点反方位角 A21", f"{r['A21']:.6f}"),
                (f"{ri*9+9}", "迭代总次数", f"{r['iter']}"),
            ])
        t = self.ui.tableDirect
        t.setRowCount(len(rows))
        colors = [QColor(230, 245, 255), QColor(255, 255, 255)]
        for row, (no, label, val) in enumerate(rows):
            bg = colors[row % 2]
            for col, text in enumerate([no, label, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)

    # ── 填充反算表格 ──────────────────────────────────────────

    def _fill_inverse_table(self):
        rows = []
        for ri, r in enumerate(self._results_inverse):
            rows.extend([
                (f"{ri*9+1}", "计算模式标志", "2"),
                (f"{ri*9+2}", "起点纬度 B1", f"{r['B1']:.6f}"),
                (f"{ri*9+3}", "起点经度 L1", f"{r['L1']:.6f}"),
                (f"{ri*9+4}", "终点纬度 B2", f"{r['B2']:.6f}"),
                (f"{ri*9+5}", "终点经度 L2", f"{r['L2']:.6f}"),
                (f"{ri*9+6}", "大地线长度 S", f"{r['S']:.3f}"),
                (f"{ri*9+7}", "正方位角 A12", f"{r['A12']:.6f}"),
                (f"{ri*9+8}", "反方位角 A21", f"{r['A21']:.6f}"),
                (f"{ri*9+9}", "迭代总次数", f"{r['iter']}"),
            ])
        t = self.ui.tableInverse
        t.setRowCount(len(rows))
        colors = [QColor(255, 240, 230), QColor(255, 255, 255)]
        for row, (no, label, val) in enumerate(rows):
            bg = colors[row % 2]
            for col, text in enumerate([no, label, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)


# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
