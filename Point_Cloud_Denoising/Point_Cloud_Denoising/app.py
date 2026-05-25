# app.py
# 主程序 — 运行此文件启动界面

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView, QVBoxLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from main_window_ui import Ui_MainWindow
import file_io
from calculator import PointCloudProcessor


# ══════════════════════════════════════════════════════════════
#  后台计算线程（防止界面卡死）
# ══════════════════════════════════════════════════════════════

class WorkerThread(QThread):
    finished = pyqtSignal(object)   # 计算完成，传回 processor
    error    = pyqtSignal(str)

    def __init__(self, points):
        super().__init__()
        self._points = points

    def run(self):
        try:
            proc = PointCloudProcessor()
            proc.load(self._points)
            proc.run()
            self.finished.emit(proc)
        except Exception as e:
            self.error.emit(str(e))


# ══════════════════════════════════════════════════════════════
#  主控制器
# ══════════════════════════════════════════════════════════════

class App(QMainWindow):

    # 结果表格列定义
    HEADERS = [
        "序号", "说明", "计算结果"
    ]

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._points = []     # list[Point]
        self._proc   = None   # PointCloudProcessor
        self._worker = None

        self._setup_table()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开 point.txt")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_table(self):
        t = self.ui.tableResult
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(self.HEADERS)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.setFont(QFont("Consolas", 9))

    def _connect_signals(self):
        self.ui.actionOpen.triggered.connect(self.slot_open)
        self.ui.actionRun.triggered.connect(self.slot_run)
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open(self):
        """打开 point.txt"""
        path, _ = QFileDialog.getOpenFileName(
            self, "打开点云文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._points = file_io.read_points(path)
            self._proc   = None
            self.ui.tableResult.setRowCount(0)
            self.ui.textSummary.clear()
            n = len(self._points)
            self.statusBar().showMessage(
                f"已加载：{path}    共 {n} 个点    请点击「运行去噪」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_run(self):
        """后台运行统计滤波去噪"""
        if not self._points:
            QMessageBox.warning(self, "提示", "请先打开 point.txt")
            return

        # 禁用按钮，显示进度条
        self.ui.actionRun.setEnabled(False)
        self.ui.progressBar.setVisible(True)
        self.ui.progressBar.setRange(0, 0)   # 不确定模式（滚动条）
        self.statusBar().showMessage("正在计算，请稍候...")

        self._worker = WorkerThread(self._points)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, proc: PointCloudProcessor):
        """计算完成回调"""
        self._proc = proc
        self.ui.progressBar.setVisible(False)
        self.ui.actionRun.setEnabled(True)

        self._fill_table()
        self._fill_summary()
        self.statusBar().showMessage(
            f"计算完成  |  总点数 {len(self._points)}  "
            f"噪声点 {proc.noise_count}  "
            f"保留 {proc.clean_count}  "
            f"μ={proc.global_mean:.3f}  σ={proc.global_std:.3f}"
        )

    def _on_error(self, msg: str):
        self.ui.progressBar.setVisible(False)
        self.ui.actionRun.setEnabled(True)
        QMessageBox.critical(self, "计算失败", msg)

    def slot_save(self):
        """保存 result.txt"""
        if not self._proc:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "result.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            file_io.write_result(path, self._proc, self._points)
            self.statusBar().showMessage(f"结果已保存：{path}")
            QMessageBox.information(self, "保存成功", f"文件已保存：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def slot_clear(self):
        self._points = []
        self._proc   = None
        self.ui.tableResult.setRowCount(0)
        self.ui.textSummary.clear()
        self.statusBar().showMessage("已清除")

    # ── 填充表格（29项结果）──────────────────────────────────

    def _fill_table(self):
        proc   = self._proc
        points = self._points
        p1     = points[0]
        p6     = points[5]
        p789   = points[788]
        g000   = len(proc.grid.get((0, 0, 0), []))

        rows = [
            ("1",  "点P1的x坐标",                   f"{p1.x:.3f}"),
            ("2",  "点P6的y坐标",                   f"{p6.y:.3f}"),
            ("3",  "点P789的z坐标",                 f"{p789.z:.3f}"),
            ("4",  "原始点云总点数",                 str(len(points))),
            ("5",  "点云数据x最大值",                f"{proc.xmax:.3f}"),
            ("6",  "点云数据y最大值",                f"{proc.ymax:.3f}"),
            ("7",  "点云数据z最大值",                f"{proc.zmax:.3f}"),
            ("8",  "格网xmin",                      f"{proc.xmin:.3f}"),
            ("9",  "格网xmax1",                     f"{proc.xmax1:.3f}"),
            ("10", "格网ymin",                      f"{proc.ymin:.3f}"),
            ("11", "格网ymax1",                     f"{proc.ymax1:.3f}"),
            ("12", "格网zmin",                      f"{proc.zmin:.3f}"),
            ("13", "格网zmax1",                     f"{proc.zmax1:.3f}"),
            ("14", "网格(0,0,0)内的点个数",          str(g000)),
            ("15", "点P1的网格索引i分量",            str(p1.gi)),
            ("16", "点P6的网格索引j分量",            str(p6.gj)),
            ("17", "点P1的候选点总数",              str(p1.candidates)),
            ("18", "点P6的候选点总数",              str(p6.candidates)),
            ("19", "点P1的6个邻近点序号最大值",      str(max(p1.neighbors))),
            ("20", "点P6的6个邻近点序号最大值",      str(max(p6.neighbors))),
            ("21", "点P1邻域平均距离u1",             f"{p1.mean_dist:.3f}"),
            ("22", "点P1邻域距离标准差σ1",           f"{p1.std_dist:.3f}"),
            ("23", "点P6邻域平均距离u6",             f"{p6.mean_dist:.3f}"),
            ("24", "点P6邻域距离标准差σ6",           f"{p6.std_dist:.3f}"),
            ("25", "全局平均距离均值μ",             f"{proc.global_mean:.3f}"),
            ("26", "全局距离标准差σ",              f"{proc.global_std:.3f}"),
            ("27", "点P1是否为噪声点(1=是,0=否)",   str(p1.is_noise)),
            ("28", "点P6是否为噪声点(1=是,0=否)",   str(p6.is_noise)),
            ("29", "去噪后保留的点云总数",           str(proc.clean_count)),
        ]

        t = self.ui.tableResult
        t.setRowCount(len(rows))

        for row, (no, label, val) in enumerate(rows):
            is_noise_row = (no in ("27", "28") and val == "1")
            bg = QColor(255, 210, 210) if is_noise_row else (
                QColor(240, 255, 240) if row % 2 == 0 else QColor(255, 255, 255)
            )
            for col, text in enumerate([no, label, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)

    # ── 填充右侧统计摘要 ──────────────────────────────────────

    def _fill_summary(self):
        proc = self._proc
        pts  = self._points
        p1   = pts[0]
        p6   = pts[5]

        text = f"""╔══════════════════════════════════════╗
║       点云去噪统计报告               ║
╚══════════════════════════════════════╝

【基本信息】
  原始点云总数  : {len(pts)}
  格网边长      : {proc.grid_size} m
  k邻近点数     : {proc.K}

【数据范围】
  X : {proc.xmin:.3f} ~ {proc.xmax:.3f}  (扩展至 {proc.xmax1:.3f})
  Y : {proc.ymin:.3f} ~ {proc.ymax:.3f}  (扩展至 {proc.ymax1:.3f})
  Z : {proc.zmin:.3f} ~ {proc.zmax:.3f}  (扩展至 {proc.zmax1:.3f})

【全局统计】
  全局均值 μ    : {proc.global_mean:.3f} m
  全局标准差 σ  : {proc.global_std:.3f} m
  判断阈值      : {proc.global_mean + 2*proc.global_std:.3f} m

【去噪结果】
  噪声点数      : {proc.noise_count}
  保留点数      : {proc.clean_count}
  噪声比例      : {proc.noise_count/len(pts)*100:.2f}%

【P1 详情】
  坐标          : ({p1.x:.3f}, {p1.y:.3f}, {p1.z:.3f})
  网格索引      : ({p1.gi}, {p1.gj}, {p1.gk})
  候选点数      : {p1.candidates}
  邻域均值 u1   : {p1.mean_dist:.3f} m
  邻域标准差 σ1 : {p1.std_dist:.3f} m
  是否噪声      : {'是 ⚠' if p1.is_noise else '否 ✓'}

【P6 详情】
  坐标          : ({p6.x:.3f}, {p6.y:.3f}, {p6.z:.3f})
  网格索引      : ({p6.gi}, {p6.gj}, {p6.gk})
  候选点数      : {p6.candidates}
  邻域均值 u6   : {p6.mean_dist:.3f} m
  邻域标准差 σ6 : {p6.std_dist:.3f} m
  是否噪声      : {'是 ⚠' if p6.is_noise else '否 ✓'}
"""
        self.ui.textSummary.setFont(QFont("Consolas", 9))
        self.ui.textSummary.setText(text)


# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
