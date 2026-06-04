# app.py
# 地形图图幅编号计算系统 — 主程序

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView, QVBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from main_window_ui import Ui_MainWindow
from calculator import TopoCalculator, dec_to_dms
from draw_widget import DrawWidget
import file_io


# 比例尺列表
SCALE_LIST = ["100万", "50万", "25万", "10万", "5万", "2.5万", "1万", "5千"]


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._calc   = None
        self._canvas = DrawWidget()

        # 嵌入绘图区
        QVBoxLayout(self.ui.widget_canvas).addWidget(self._canvas)

        # 比例尺下拉
        self.ui.comboScale.addItems(SCALE_LIST)
        self.ui.comboScale.setCurrentText("10万")
        self.ui.comboScale.currentTextChanged.connect(self._on_scale_changed)

        self._setup_table()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开 topo_map.txt")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_table(self):
        t = self.ui.tableResult
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["序号", "说明", "计算结果"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.setFont(QFont("Consolas", 9))

    def _connect_signals(self):
        self.ui.actionOpen.triggered.connect(self.slot_open)
        self.ui.actionCalc.triggered.connect(self.slot_calc)
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionDraw.triggered.connect(self.slot_draw)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开数据文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            calc = file_io.read_input(path)
            self._calc = calc
            self.ui.tableResult.setRowCount(0)
            self._canvas.clear()
            self.statusBar().showMessage(
                f"已加载：{path}  |  共 {len(calc.points)} 个点  请点击「计算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_calc(self):
        if not self._calc:
            QMessageBox.warning(self, "提示", "请先打开 topo_map.txt")
            return
        try:
            self._calc.compute()
            self._fill_table()
            res = self._calc.result
            self.statusBar().showMessage(
                f"计算完成  |  总点数:{res.total_points}  "
                f"跨图幅:{res.cross_points}  "
                f"1:10万图幅数:{res.count_10w}"
            )
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_save(self):
        if not self._calc or not self._calc.result.points:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "topo_result.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            file_io.write_result(path, self._calc)
            self.statusBar().showMessage(f"结果已保存：{path}")
            QMessageBox.information(self, "保存成功", f"文件已保存：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def slot_draw(self):
        if not self._calc or not self._calc.result.points:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        scale = self.ui.comboScale.currentText()
        self._canvas.set_data(self._calc.result.points, scale)
        self.statusBar().showMessage(f"绘图完成  |  比例尺：1:{scale}")

    def slot_clear(self):
        self._calc = None
        self.ui.tableResult.setRowCount(0)
        self._canvas.clear()
        self.statusBar().showMessage("已清除")

    def _on_scale_changed(self, scale: str):
        """比例尺切换自动刷新绘图"""
        if self._calc and self._calc.result.points:
            self._canvas.set_data(self._calc.result.points, scale)

    # ── 填充30项结果表格 ──────────────────────────────────────

    def _fill_table(self):
        res = self._calc.result
        p1  = res.points[0]
        p2  = res.points[1]
        bnd = p1.boundary_10w

        rows = [
            ("1",  "Point1十进制度纬度",         f"{p1.B:.4f}"),
            ("2",  "Point1十进制度经度",         f"{p1.L:.4f}"),
            ("3",  "Point1 1:100万图幅编号",     p1.codes["100万"]),
            ("4",  "Point1 1:50万图幅编号",      p1.codes["50万"]),
            ("5",  "Point1 1:25万图幅编号",      p1.codes["25万"]),
            ("6",  "Point1 1:10万图幅编号",      p1.codes["10万"]),
            ("7",  "Point1 1:5万图幅编号",       p1.codes["5万"]),
            ("8",  "Point1 1:2.5万图幅编号",     p1.codes["2.5万"]),
            ("9",  "Point1 1:1万图幅编号",       p1.codes["1万"]),
            ("10", "Point1 1:5千图幅编号",       p1.codes["5千"]),
            ("11", "Point1所在1:10万图幅北界",   dec_to_dms(bnd["北"])),
            ("12", "Point1所在1:10万图幅南界",   dec_to_dms(bnd["南"])),
            ("13", "Point1所在1:10万图幅东界",   dec_to_dms(bnd["东"])),
            ("14", "Point1所在1:10万图幅西界",   dec_to_dms(bnd["西"])),
            ("15", "Point2 1:10万图幅编号",      p2.codes["10万"]),
            ("16", "Point2 1:5万图幅编号",       p2.codes["5万"]),
            ("17", "Point2 1:1万图幅编号",       p2.codes["1万"]),
            ("18", "Point2所在图幅中心点纬度",   f"{p2.center_5w[0]:.4f}"),
            ("19", "Point2所在图幅中心点经度",   f"{p2.center_5w[1]:.4f}"),
            ("20", "1:10万图幅总数",             str(res.count_10w)),
            ("21", "1:5万图幅总数",              str(res.count_5w)),
            ("22", "1:1万图幅总数",              str(res.count_1w)),
            ("23", "平均纬度值",                 f"{res.avg_B:.4f}"),
            ("24", "平均经度值",                 f"{res.avg_L:.4f}"),
            ("25", "最北点纬度",                 dec_to_dms(res.max_B_pt.B)),
            ("26", "最南点纬度",                 dec_to_dms(res.min_B_pt.B)),
            ("27", "最东点经度",                 dec_to_dms(res.max_L_pt.L)),
            ("28", "最西点经度",                 dec_to_dms(res.min_L_pt.L)),
            ("29", "总点数",                     str(res.total_points)),
            ("30", "跨图幅点数",                 str(res.cross_points)),
        ]

        t = self.ui.tableResult
        t.setRowCount(len(rows))

        # 颜色分组：编号类=蓝、四至类=绿、统计类=橙
        def row_color(no):
            n = int(no)
            if 3  <= n <= 10: return QColor(220, 235, 255)
            if 11 <= n <= 14: return QColor(220, 255, 220)
            if 20 <= n <= 22: return QColor(255, 245, 220)
            if 25 <= n <= 28: return QColor(240, 220, 255)
            return QColor(248, 248, 248)

        for row, (no, label, val) in enumerate(rows):
            bg = row_color(no)
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
