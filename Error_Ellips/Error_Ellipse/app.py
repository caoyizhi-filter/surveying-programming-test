# app.py
# 主程序 —— 运行这个文件启动程序

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# 自动生成的 UI（由 PyUIC 从 main_window.ui 生成，不要手动改）
from main_window_ui import Ui_MainWindow

# 业务模块
import calculator
import file_io
from draw_widget import DrawWidget


class App(QMainWindow):
    """
    主控制器
    ① 加载 UI
    ② 把 widget_canvas 替换为 DrawWidget
    ③ 连接信号槽
    ④ 槽函数里调用 calculator / file_io
    """

    def __init__(self):
        super().__init__()

        # ── 加载 UI ──────────────────────────────────────────
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ── 用 DrawWidget 替换 widget_canvas ─────────────────
        # （如果用了 Qt Designer「提升」功能，下面两行不需要）
        self._canvas = DrawWidget(self)
        # 把 DrawWidget 放入 widget_canvas 的布局里
        from PyQt5.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(self.ui.widget_canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        # ── 数据 ─────────────────────────────────────────────
        self._points = []   # list[calculator.Point]
        self._stat   = {}   # 统计汇总

        # ── 初始化表格 & 连接信号 ─────────────────────────────
        self._setup_table()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开数据文件")

    # ════════════════════════════════════════════════════════
    #  初始化
    # ════════════════════════════════════════════════════════

    def _setup_table(self):
        """设置结果表格列头"""
        headers = [
            "点号",
            "σxx", "σyy", "σxy",
            "E(长轴)", "F(短轴)", "φ_E(°)",
            "σ(0°)", "σ(45°)", "σ(90°)", "σ(135°)", "σ(180°)",
            "是否异常"
        ]
        t = self.ui.tableWidget_result
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        t.horizontalHeader().setStretchLastSection(True)

    def _connect_signals(self):
        """把菜单/工具栏 Action 连接到槽函数"""
        self.ui.actionOpen.triggered.connect(self.slot_open)
        self.ui.actionCalculate.triggered.connect(self.slot_calculate)
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionDraw.triggered.connect(self.slot_draw)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ════════════════════════════════════════════════════════
    #  槽函数
    # ════════════════════════════════════════════════════════

    def slot_open(self):
        """打开 ellipse.txt"""
        path, _ = QFileDialog.getOpenFileName(
            self, "打开数据文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._points = file_io.read_input(path)
            self._stat   = {}
            self.ui.tableWidget_result.setRowCount(0)
            self._canvas.clear()
            self.statusBar().showMessage(
                f"已加载：{len(self._points)} 个点    请点击「计算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_calculate(self):
        """计算所有点，填入表格"""
        if not self._points:
            QMessageBox.warning(self, "提示", "请先打开数据文件")
            return

        self._stat = calculator.compute_all(self._points)
        self._fill_table()
        self.statusBar().showMessage(
            f"计算完成  |  总点数 {self._stat['total_count']}  "
            f"异常 {self._stat['anomaly_count']}  "
            f"E均值 {self._stat['avg_E']:.4f}  "
            f"F均值 {self._stat['avg_F']:.4f}"
        )

    def slot_save(self):
        """保存 ellipse_result.txt"""
        if not self._stat:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "ellipse_result.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            file_io.write_output(path, self._points, self._stat)
            self.statusBar().showMessage(f"结果已保存：{path}")
            QMessageBox.information(self, "保存成功", f"文件已保存到：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def slot_draw(self):
        """在绘图区绘制误差椭圆"""
        if not self._stat:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        self._canvas.set_points(self._points)
        self.statusBar().showMessage("绘图完成")

    def slot_clear(self):
        """清除所有数据"""
        self._points = []
        self._stat   = {}
        self.ui.tableWidget_result.setRowCount(0)
        self._canvas.clear()
        self.statusBar().showMessage("已清除")

    # ════════════════════════════════════════════════════════
    #  填充结果表格
    # ════════════════════════════════════════════════════════

    def _fill_table(self):
        t = self.ui.tableWidget_result
        t.setRowCount(len(self._points))

        for row, p in enumerate(self._points):
            values = [
                p.name,
                f"{p.sigma_xx:.6f}",
                f"{p.sigma_yy:.6f}",
                f"{p.sigma_xy:.6f}",
                f"{p.E:.6f}",
                f"{p.F:.6f}",
                f"{p.phi_E:.4f}",
                f"{p.sigma_0:.6f}",
                f"{p.sigma_45:.6f}",
                f"{p.sigma_90:.6f}",
                f"{p.sigma_135:.6f}",
                f"{p.sigma_180:.6f}",
                "异常" if p.anomaly else "正常",
            ]
            bg = QColor(255, 220, 220) if p.anomaly else QColor(240, 255, 240)

            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)


# ════════════════════════════════════════════════════════════
#  程序入口
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
