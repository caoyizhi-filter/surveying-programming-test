# app.py
# 地形图图幅编号计算系统 — 主程序

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from main_window_ui import Ui_MainWindow
from calculator import TopoCalculator, decimal_to_dms
import file_io


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._calc = None

        self._setup_table()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开 map.txt")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_table(self):
        t = self.ui.tableResult
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["序号", "说明", "计算结果"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.setFont(QFont("Consolas", 10))

    def _connect_signals(self):
        self.ui.actionOpen.triggered.connect(self.slot_open)
        self.ui.actionCalc.triggered.connect(self.slot_calc)
        self.ui.actionSave.triggered.connect(self.slot_save)
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
            self._calc = file_io.read_input(path)
            self.ui.tableResult.setRowCount(0)
            self.statusBar().showMessage(
                f"已加载：{path}  |  共{len(self._calc.points)}个点  请点击「计算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_calc(self):
        if not self._calc:
            QMessageBox.warning(self, "提示", "请先打开 map.txt")
            return
        try:
            self._calc.compute()
            self._fill_table()
            self.statusBar().showMessage("计算完成  |  共30项结果")
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_save(self):
        if not self._calc or not self._calc.result.points:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "map_result.txt", "文本文件 (*.txt)"
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
        self.ui.tableResult.setRowCount(0)
        self.statusBar().showMessage("已清除")

    # ── 填充30项结果表格（坐标转为度分秒）──────────────────────

    def _fill_table(self):
        res = self._calc.result
        if len(res.points) < 2:
            QMessageBox.warning(self, "提示", "结果中至少需要2个点")
            return
        p1  = res.points[0]
        p2  = res.points[1]

        # 转换函数
        def fmt(deg): return decimal_to_dms(deg)
        def fmt_sw(deg): return decimal_to_dms(deg)   # 西南角同样转度分秒

        rows = [
            ("1",  "Point1 纬度B",           fmt(p1.B)),
            ("2",  "Point1 经度L",           fmt(p1.L)),
            ("3",  "Point1  1:100万 老编号",  p1.old_codes["100万"]),
            ("4",  "Point1  1:100万 新编号",  p1.new_codes["100万"]),
            ("5",  "Point1  1:50万  老编号",  p1.old_codes["50万"]),
            ("6",  "Point1  1:50万  新编号",  p1.new_codes["50万"]),
            ("7",  "Point1  1:25万  老编号",  p1.old_codes["25万"]),
            ("8",  "Point1  1:25万  新编号",  p1.new_codes["25万"]),
            ("9",  "Point1  1:10万  老编号",  p1.old_codes["10万"]),
            ("10", "Point1  1:10万  新编号",  p1.new_codes["10万"]),
            ("11", "Point1  1:5万   老编号",  p1.old_codes["5万"]),
            ("12", "Point1  1:5万   新编号",  p1.new_codes["5万"]),
            ("13", "Point1  1:1万   老编号",  p1.old_codes["1万"]),
            ("14", "Point1  1:1万   新编号",  p1.new_codes["1万"]),
            ("15", "Point1  图幅西南角纬度",  fmt_sw(p1.sw_lat_10w)),
            ("16", "Point1  图幅西南角经度",  fmt_sw(p1.sw_lon_10w)),
            ("17", "Point2 纬度B",           fmt(p2.B)),
            ("18", "Point2 经度L",           fmt(p2.L)),
            ("19", "Point2  1:100万 老编号",  p2.old_codes["100万"]),
            ("20", "Point2  1:100万 新编号",  p2.new_codes["100万"]),
            ("21", "Point2  1:50万  老编号",  p2.old_codes["50万"]),
            ("22", "Point2  1:50万  新编号",  p2.new_codes["50万"]),
            ("23", "Point2  1:25万  老编号",  p2.old_codes["25万"]),
            ("24", "Point2  1:25万  新编号",  p2.new_codes["25万"]),
            ("25", "Point2  1:10万  老编号",  p2.old_codes["10万"]),
            ("26", "Point2  1:10万  新编号",  p2.new_codes["10万"]),
            ("27", "Point2  1:5万   老编号",  p2.old_codes["5万"]),
            ("28", "Point2  1:5万   新编号",  p2.new_codes["5万"]),
            ("29", "Point2  1:1万   老编号",  p2.old_codes["1万"]),
            ("30", "Point2  1:1万   新编号",  p2.new_codes["1万"]),
        ]

        t = self.ui.tableResult
        t.setRowCount(len(rows))

        # 颜色分组
        def bg(no):
            n = int(no)
            if n <= 16:                        # Point1区
                if n % 2 == 1:                 # 老编号行
                    return QColor(220, 235, 255)
                else:                          # 新编号行
                    return QColor(235, 245, 255)
            else:                              # Point2区
                if n % 2 == 1:
                    return QColor(220, 255, 230)
                else:
                    return QColor(235, 255, 240)

        for row, (no, label, val) in enumerate(rows):
            for col, text in enumerate([no, label, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg(no))
                t.setItem(row, col, item)


# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())