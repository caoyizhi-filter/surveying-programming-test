# app.py
# 流程：miaoda_code.py(算法) → Qt Designer(.ui) → pyuic5(_ui.py) → 本文件

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from main_window_ui import Ui_MainWindow
import miaoda_code as algo

LABELS = [
    (1, "类别 1 训练样本总数"),         (2, "类别 1 波段 1 均值"),
    (3, "类别 1 波段 2 均值"),          (4, "类别 1 协方差矩阵行列式"),
    (5, "类别 2 训练样本总数"),         (6, "类别 2 波段 1 均值"),
    (7, "类别 2 波段 2 均值"),          (8, "类别 2 协方差矩阵行列式"),
    (9, "第 1 个待分类像元类别 1 对数似然值"),
    (10, "第 1 个待分类像元类别 2 对数似然值"),
    (11, "第 1 个待分类像元最终分类类别"),
    (12, "验证样本总数量"),             (13, "混淆矩阵对角线正确样本总数"),
    (14, "总体分类精度 OA"),            (15, "分类 Kappa 系数"),
    (16, "所有待分类像元中类别 1 总个数"),
    (17, "所有待分类像元中类别 2 总个数"),
]

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._paths = {"train": "train.txt", "pixels": "pixel.txt", "verify": "verify.txt"}
        self._r = None
        self._vals = None

        t = self.ui.tableResult
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["序号", "说明", "计算结果"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        t.setFont(QFont("Consolas", 10))

        a = self.ui
        a.actionOpenTrain.triggered.connect(lambda: self._open("train"))
        a.actionOpenPixels.triggered.connect(lambda: self._open("pixels"))
        a.actionOpenVerify.triggered.connect(lambda: self._open("verify"))
        a.actionCalc.triggered.connect(self._calc)
        a.actionSave.triggered.connect(self._save)
        a.actionClear.triggered.connect(self._clear)
        a.actionExit.triggered.connect(self.close)

    def _open(self, kind):
        path, _ = QFileDialog.getOpenFileName(self, "", "", "文本文件 (*.txt);;所有文件 (*)")
        if not path: return
        self._paths[kind] = path
        self._r = None
        self.ui.labelFile.setText(
            f"训练: {self._paths['train'].split('/')[-1]}\n"
            f"像元: {self._paths['pixels'].split('/')[-1]}\n"
            f"验证: {self._paths['verify'].split('/')[-1]}")

    def _calc(self):
        self._r = algo.run_all(self._paths["train"], self._paths["pixels"],
                               self._paths["verify"], "mlc_result.txt")
        r = self._r
        self._vals = [
            str(r["num1"]),
            f"{r['mu1'][0]:.4f}", f"{r['mu1'][1]:.4f}", f"{r['det1']:.6f}",
            str(r["num2"]),
            f"{r['mu2'][0]:.4f}", f"{r['mu2'][1]:.4f}", f"{r['det2']:.6f}",
            f"{r['first_g1']:.6f}", f"{r['first_g2']:.6f}", str(r["first_pred"]),
            str(r["total_v"]), str(r["corr"]),
            f"{r['OA']:.4f}", f"{r['KAP']:.4f}",
            str(r["count_cls1"]), str(r["count_cls2"]),
        ]
        t = self.ui.tableResult
        t.setRowCount(len(LABELS))
        c1, c2 = QColor(230, 245, 255), QColor(255, 255, 255)
        for i, ((no, lb), val) in enumerate(zip(LABELS, self._vals)):
            bg = c1 if i % 2 == 0 else c2
            for j, text in enumerate([str(no), lb, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(i, j, item)
        self.statusBar().showMessage(
            f"完成 | 类别1={r['count_cls1']} 类别2={r['count_cls2']} | OA={r['OA']:.4f} Kappa={r['KAP']:.4f}")

    def _save(self):
        if not self._vals: return
        path, _ = QFileDialog.getSaveFileName(self, "", "mlc_result.txt", "文本文件 (*.txt)")
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            f.write("序号,指标名称,计算结果\n")
            for (no, lb), val in zip(LABELS, self._vals):
                f.write(f"{no},{lb},{val}\n")

    def _clear(self):
        self._paths = {"train": "train.txt", "pixels": "pixel.txt", "verify": "verify.txt"}
        self._r = None
        self._vals = None
        self.ui.tableResult.setRowCount(0)
        self.ui.labelFile.setText("未加载数据")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
