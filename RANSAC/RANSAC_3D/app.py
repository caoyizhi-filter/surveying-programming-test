# app.py
# RANSAC 三维直线参数估计系统 — 主程序

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from main_window_ui import Ui_MainWindow
from calculator import RANSACCalculator
import file_io

# 颜色常量
C_INLIER  = QColor(200, 220, 255)   # 蓝：内点
C_OUTLIER = QColor(255, 200, 200)   # 红：粗差
C_ALT1    = QColor(235, 245, 255)
C_ALT2    = QColor(248, 248, 248)


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._calc = None

        self._setup_tables()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开 ransac_3dline.txt")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_tables(self):
        # 测点表格
        tp = self.ui.tablePoints
        tp.setColumnCount(4)
        tp.setHorizontalHeaderLabels(["编号", "x (m)", "y (m)", "z (m)"])
        tp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tp.setFont(QFont("Consolas", 9))

        # 结果表格
        tr = self.ui.tableResult
        tr.setColumnCount(3)
        tr.setHorizontalHeaderLabels(["序号", "指标", "计算结果"])
        tr.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tr.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tr.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tr.setFont(QFont("Consolas", 9))

    def _connect_signals(self):
        self.ui.actionOpen.triggered.connect(self.slot_open)
        self.ui.actionRun.triggered.connect(self.slot_run)
        self.ui.actionExport.triggered.connect(self.slot_export)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开三维数据文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._calc = file_io.read_input(path)
            self._fill_points_table(colored=False)
            self.ui.tableResult.setRowCount(0)
            self.statusBar().showMessage(
                f"已加载：{path}  |  共{len(self._calc.points)}个测点  请点击「RANSAC三维解算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_run(self):
        if not self._calc:
            QMessageBox.warning(self, "提示", "请先打开 ransac_3dline.txt")
            return
        try:
            self._calc.compute()
            res = self._calc.result
            self._fill_points_table(colored=True)
            self._fill_result_table()
            self.statusBar().showMessage(
                f"RANSAC解算完成  |  "
                f"总点数:{res.total_pts}  "
                f"内点:{res.inlier_count}  "
                f"粗差:{res.outlier_count}  "
                f"最优迭代轮次:{res.best_iter}  "
                f"基准点:({res.x0:.4f},{res.y0:.4f},{res.z0:.4f})  "
                f"方向向量:({res.ux:.4f},{res.uy:.4f},{res.uz:.4f})"
            )
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_export(self):
        if not self._calc or not self._calc.result.total_pts:
            QMessageBox.warning(self, "提示", "请先完成RANSAC解算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出结果文件", "ransac_3d_result.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            file_io.write_result(path, self._calc)
            self.statusBar().showMessage(f"结果已保存：{path}")
            QMessageBox.information(self, "导出成功", f"文件已保存：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def slot_clear(self):
        self._calc = None
        self.ui.tablePoints.setRowCount(0)
        self.ui.tableResult.setRowCount(0)
        self.statusBar().showMessage("已清空")

    # ── 填充测点表格 ──────────────────────────────────────────

    def _fill_points_table(self, colored: bool):
        pts = self._calc.points
        t   = self.ui.tablePoints
        t.setRowCount(len(pts))
        for row, p in enumerate(pts):
            bg = (C_INLIER if p.is_inlier else C_OUTLIER) if colored else QColor(248, 248, 248)
            vals = [str(p.idx), f"{p.x:.2f}", f"{p.y:.2f}", f"{p.z:.2f}"]
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)

    # ── 填充24项结果表格 ──────────────────────────────────────

    def _fill_result_table(self):
        res  = self._calc.result
        calc = self._calc
        rows = [
            ("1",  "三维观测点总数量",           str(res.total_pts)),
            ("2",  "距离阈值T",                  f"{calc.T:.4f}"),
            ("3",  "最大迭代次数Kmax",            str(calc.K_MAX)),
            ("4",  "最优直线基准点x0",            f"{res.x0:.4f}"),
            ("5",  "最优直线基准点y0",            f"{res.y0:.4f}"),
            ("6",  "最优直线基准点z0",            f"{res.z0:.4f}"),
            ("7",  "最优直线方向向量ux",          f"{res.ux:.4f}"),
            ("8",  "最优直线方向向量uy",          f"{res.uy:.4f}"),
            ("9",  "最优直线方向向量uz",          f"{res.uz:.4f}"),
            ("10", "最优模型内点总数",            str(res.inlier_count)),
            ("11", "粗差外点总个数",              str(res.outlier_count)),
            ("12", "1号点到最优直线距离",         f"{res.dist_pt1:.4f}"),
            ("13", "7号粗差点到最优直线距离",     f"{res.dist_pt7:.4f}"),
            ("14", "最优内点集x坐标平均值",       f"{res.inlier_x_mean:.4f}"),
            ("15", "最优内点集y坐标平均值",       f"{res.inlier_y_mean:.4f}"),
            ("16", "最优内点集z坐标平均值",       f"{res.inlier_z_mean:.4f}"),
            ("17", "全部粗差点编号集合",          res.outlier_ids),
            ("18", "最优模型对应迭代轮次",        str(res.best_iter)),
            ("19", "内点x坐标最小值",             f"{res.inlier_x_min:.4f}"),
            ("20", "内点z坐标最大值",             f"{res.inlier_z_max:.4f}"),
            ("21", "第一次抽样直线方向向量ux",    f"{res.first_ux:.4f}"),
            ("22", "第一次抽样得到的内点数量",    str(res.first_inlier_count)),
            ("23", "所有粗差点三维坐标均值",      res.outlier_xyz_mean),
            ("24", "内点占全部三维测点比例",      f"{res.inlier_ratio:.4f}"),
        ]

        t = self.ui.tableResult
        t.setRowCount(len(rows))
        for row, (no, label, val) in enumerate(rows):
            bg = C_ALT1 if row % 2 == 0 else C_ALT2
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
