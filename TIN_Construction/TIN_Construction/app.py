# app.py
# TIN构建与填挖方体积计算系统 — 主程序

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from main_window_ui import Ui_MainWindow
from calculator import TINCalculator, Point3D
import file_io


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._calc = None   # TINCalculator

        self._setup_tables()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开地形点坐标.txt")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_tables(self):
        # 结果表格
        t = self.ui.tableResult
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["序号", "说明", "计算结果"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.setFont(QFont("Consolas", 10))

        # 输入点云表格
        ti = self.ui.tableInput
        ti.setColumnCount(3)
        ti.setHorizontalHeaderLabels(["x (m)", "y (m)", "z (m)"])
        ti.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 三角形详情表格
        tt = self.ui.tableTriangles
        tt.setColumnCount(6)
        tt.setHorizontalHeaderLabels(["编号", "顶点1", "顶点2", "顶点3",
                                      "面积(m²)", "体积(m³)"])
        tt.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tt.horizontalHeader().setStretchLastSection(True)
        tt.setFont(QFont("Consolas", 9))

    def _connect_signals(self):
        self.ui.actionOpen.triggered.connect(self.slot_open)
        self.ui.actionCalc.triggered.connect(self.slot_calc)
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open(self):
        """打开 input3.txt"""
        path, _ = QFileDialog.getOpenFileName(
            self, "打开数据文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            calc = file_io.read_input(path)
            self._calc = calc
            self._fill_input_table(calc)
            self.ui.tableResult.setRowCount(0)
            self.ui.tableTriangles.setRowCount(0)
            self.statusBar().showMessage(
                f"已加载：{path}  |  "
                f"Hd={calc.Hd}m  共{len(calc.points)}个点  "
                f"请点击「计算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_calc(self):
        """执行 TIN 构建与填挖方计算"""
        if not self._calc:
            QMessageBox.warning(self, "提示", "请先打开地形点坐标")
            return
        try:
            self._calc.compute()
            self._fill_result_table()
            self._fill_triangle_table()
            res = self._calc.result
            self.statusBar().showMessage(
                f"计算完成  |  "
                f"三角形数:{res.triangle_count}  "
                f"总面积:{res.total_area:.2f}m²  "
                f"填方:{res.fill_volume:.2f}m³  "
                f"挖方:{res.cut_volume:.2f}m³"
            )
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_save(self):
        """保存 result3.txt"""
        if not self._calc or not self._calc.result.triangle_count:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "result3.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            file_io.write_result(path, self._calc)
            self.statusBar().showMessage(f"结果已保存：{path}")
            QMessageBox.information(self, "保存成功", f"文件已保存：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def slot_clear(self):
        self._calc = None
        self.ui.editHd.clear()
        self.ui.tableInput.setRowCount(0)
        self.ui.tableResult.setRowCount(0)
        self.ui.tableTriangles.setRowCount(0)
        self.statusBar().showMessage("已清除")

    # ── 填充输入点云表格 ──────────────────────────────────────

    def _fill_input_table(self, calc: TINCalculator):
        self.ui.editHd.setText(str(calc.Hd))
        t = self.ui.tableInput
        pts = calc.points
        t.setRowCount(len(pts))
        for row, p in enumerate(pts):
            for col, val in enumerate([p.x, p.y, p.z]):
                item = QTableWidgetItem(f"{val:.3f}")
                item.setTextAlignment(Qt.AlignCenter)
                t.setItem(row, col, item)

    # ── 填充7项结果表格 ───────────────────────────────────────

    def _fill_result_table(self):
        res = self._calc.result
        rows = [
            ("1", "总点数",   str(res.total_points)),
            ("2", "z_min",   f"{res.z_min:.2f}"),
            ("3", "z_max",   f"{res.z_max:.2f}"),
            ("4", "总面积",   f"{res.total_area:.2f}"),
            ("5", "填方(m³)", f"{res.fill_volume:.2f}"),
            ("6", "挖方(m³)", f"{res.cut_volume:.2f}"),
            ("7", "三角形数", str(res.triangle_count)),
        ]

        t = self.ui.tableResult
        t.setRowCount(len(rows))
        c_fill = QColor(200, 230, 255)   # 蓝色 = 填方
        c_cut  = QColor(255, 220, 200)   # 橙色 = 挖方
        c_norm = QColor(240, 250, 240)

        color_map = {"5": c_fill, "6": c_cut}

        for row, (no, label, val) in enumerate(rows):
            bg = color_map.get(no, c_norm)
            for col, text in enumerate([no, label, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)

    # ── 填充三角形详情表格 ────────────────────────────────────

    def _fill_triangle_table(self):
        tris = self._calc.result.triangles
        t    = self.ui.tableTriangles
        t.setRowCount(len(tris))

        c_cut  = QColor(255, 235, 220)   # 挖方行
        c_fill = QColor(220, 235, 255)   # 填方行

        for row, tri in enumerate(tris):
            is_cut = tri.volume > 0
            bg = c_cut if is_cut else c_fill

            vals = [
                str(row + 1),
                f"P{tri.p1.idx}({tri.p1.x:.1f},{tri.p1.y:.1f},{tri.p1.z:.1f})",
                f"P{tri.p2.idx}({tri.p2.x:.1f},{tri.p2.y:.1f},{tri.p2.z:.1f})",
                f"P{tri.p3.idx}({tri.p3.x:.1f},{tri.p3.y:.1f},{tri.p3.z:.1f})",
                f"{tri.area:.2f}",
                f"{tri.volume:.2f}({'挖' if is_cut else '填'})",
            ]
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)

        t.resizeColumnsToContents()


# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
