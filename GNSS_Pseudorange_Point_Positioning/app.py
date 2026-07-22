# app.py
# 主程序 — 连接界面 + 算法 + 文件读写
# ============================================================

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from main_window_ui import Ui_MainWindow
from calculator import GNSSSolver
import file_io


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._data = None          # (satellites, approx_position, light_speed)
        self._results = None       # GNSSSolver 实例

        self._setup_table()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开输入文件")

    # ============================================================
    #  表格设置
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
    #  信号连接
    # ============================================================

    def _connect_signals(self):
        self.ui.actionOpen.triggered.connect(self.slot_open)
        self.ui.actionCalc.triggered.connect(self.slot_calc)
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ============================================================
    #  slot_open — 打开输入文件
    # ============================================================

    def slot_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开输入文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            satellites, approx_position, light_speed = file_io.parse_input(path)
            self._data = (satellites, approx_position, light_speed)
            self._results = None
            self.ui.tableResult.setRowCount(0)

            # 统计历元数
            epochs = set()
            for s in satellites:
                epochs.add(s.epoch)
            epoch_list = sorted(epochs)

            filename = path.replace("\\", "/").split("/")[-1]
            self.ui.labelFile.setText(
                f"文件: {filename}\n"
                f"观测总数: {len(satellites)}\n"
                f"历元数: {len(epoch_list)}\n"
                f"近似坐标: ({approx_position[0]:.3f},\n"
                f"  {approx_position[1]:.3f},\n"
                f"  {approx_position[2]:.3f})\n"
                f"光速: {light_speed:.0f} m/s"
            )
            self.ui.labelStatus.setText(
                f"{len(epoch_list)} 个历元, {len(satellites)} 个观测  |  请点击「计算」"
            )

            # 在 textSatData 中显示卫星数据摘要
            lines = ["历元(GPS时间)           卫星数"]
            for ep in epoch_list:
                count = sum(1 for s in satellites if s.epoch == ep)
                lines.append(f"  {ep:>8.0f}                {count}")
            lines.append("")
            lines.append("PRN       X(m)            Y(m)            Z(m)")
            lines.append("-" * 65)
            for s in satellites[:30]:  # 前30颗星
                lines.append(
                    f"{s.prn:4s} {s.x:>14.2f} {s.y:>14.2f} {s.z:>14.2f}"
                )
            if len(satellites) > 30:
                lines.append(f"... 共 {len(satellites)} 条观测，仅显示前30条")
            self.ui.textSatData.setText("\n".join(lines))

            self.statusBar().showMessage(f"已加载: {path}  |  请点击「计算」")
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    # ============================================================
    #  slot_calc — 执行计算
    # ============================================================

    def slot_calc(self):
        if not self._data:
            QMessageBox.warning(self, "提示", "请先打开输入文件")
            return
        try:
            self.statusBar().showMessage("计算中，请稍候...")
            QApplication.processEvents()

            satellites, approx_position, light_speed = self._data
            solver = GNSSSolver(satellites, approx_position, light_speed)
            solver.solve()
            self._results = solver

            self._fill_table()
            self.statusBar().showMessage(
                f"计算完成  |  迭代 {solver.iterations} 次  |  "
                f"{(solver.Xr, solver.Yr, solver.Zr)}"
            )
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    # ============================================================
    #  slot_save — 保存结果
    # ============================================================

    def slot_save(self):
        if not self._results:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "result5.txt",
            "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            file_io.write_result(path, self._results)
            self.statusBar().showMessage(f"结果已保存: {path}")
            QMessageBox.information(self, "保存成功", f"文件已保存:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    # ============================================================
    #  slot_clear — 清除
    # ============================================================

    def slot_clear(self):
        self._data = None
        self._results = None
        self.ui.tableResult.setRowCount(0)
        self.ui.labelFile.setText("未加载数据")
        self.ui.labelStatus.setText("请打开输入文件")
        self.ui.textSatData.clear()
        self.statusBar().showMessage("已清除")

    # ============================================================
    #  _fill_table — 填表（6项结果）
    # ============================================================

    def _fill_table(self):
        r = self._results
        rows = [
            ("1", "接收机X",        f"{r.Xr:.3f}"),
            ("2", "接收机Y",        f"{r.Yr:.3f}"),
            ("3", "接收机Z",        f"{r.Zr:.3f}"),
            ("4", "迭代次数",       str(r.iterations)),
            ("5", "单位权方差",     f"{r.unit_variance:.6f}"),
            ("6", "PDOP值",         f"{r.PDOP:.6f}"),
        ]

        t = self.ui.tableResult
        t.setRowCount(len(rows))
        colors = [QColor(230, 245, 255), QColor(255, 255, 255)]

        for row_idx, (no, label, val) in enumerate(rows):
            bg = colors[row_idx % 2]
            for col, text in enumerate([no, label, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row_idx, col, item)


# ============================================================
#  程序入口
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
