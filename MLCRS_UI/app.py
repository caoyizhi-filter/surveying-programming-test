
# app.py
# 遥感影像最大似然法分类系统 — 主程序

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView, QWidget
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
)

from main_window_ui import Ui_MainWindow
from calculator import MLClassifier, compute_oa, compute_kappa
import file_io

# 颜色常量
C_CLASS = {1: QColor(60, 140, 240), 2: QColor(240, 130, 50)}
C_BG    = QColor(245, 247, 250)
C_GRID  = QColor(210, 215, 225)
C_TEXT  = QColor(50, 55, 65)
C_AXIS  = QColor(120, 125, 140)
C_ALT1  = QColor(240, 246, 255)
C_ALT2  = QColor(250, 250, 252)
C_HEAT_LO = QColor(255, 255, 240)
C_HEAT_HI = QColor(220, 50, 50)


# ══════════════════════════════════════════════════════════════
#  绘图控件（光谱曲线 / 混淆矩阵热力图）
# ══════════════════════════════════════════════════════════════

class PlotWidget(QWidget):

    MODE_SPECTRAL = 0
    MODE_HEATMAP  = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = self.MODE_SPECTRAL
        self._stats_map : dict = {}
        self._cm = None
        self._has_data = False
        self.setMinimumSize(400, 350)

    def show_spectral(self, stats_map):
        self._mode = self.MODE_SPECTRAL
        self._stats_map = stats_map
        self._has_data = True
        self.update()

    def show_heatmap(self, cm):
        self._mode = self.MODE_HEATMAP
        self._cm = cm
        self._has_data = True
        self.update()

    def clear_data(self):
        self._has_data = False
        self._stats_map = {}
        self._cm = None
        self.update()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.fillRect(self.rect(), C_BG)

        if not self._has_data:
            qp.setPen(C_AXIS)
            qp.setFont(QFont("Microsoft YaHei", 12))
            qp.drawText(self.rect(), Qt.AlignCenter,
                        "请加载数据并执行分类")
            return

        if self._mode == self.MODE_SPECTRAL:
            self._draw_spectral(qp)
        else:
            self._draw_heatmap(qp)

    # ── 光谱均值曲线 ──────────────────────────────────────────

    def _draw_spectral(self, qp):
        if not self._stats_map:
            return
        w, h = self.width(), self.height()
        margin_l, margin_r = 70, 30
        margin_t, margin_b = 35, 50

        # 坐标范围
        all_vals = []
        for st in self._stats_map.values():
            all_vals.extend(st.mean)
        vmin, vmax = min(all_vals), max(all_vals)
        pad = (vmax - vmin) * 0.15 or 5.0
        vmin -= pad
        vmax += pad

        px = margin_l
        pw = w - margin_l - margin_r
        py = margin_t
        ph = h - margin_t - margin_b

        # 网格 + 轴
        qp.setPen(QPen(C_GRID, 0.5))
        for i in range(5):
            yy = py + ph * i / 4
            qp.drawLine(QPointF(px, yy), QPointF(px + pw, yy))
        for band in range(4):
            xx = px + pw * band / 3
            qp.drawLine(QPointF(xx, py), QPointF(xx, py + ph))

        # 轴标签
        qp.setPen(C_TEXT)
        qp.setFont(QFont("Consolas", 8))
        for band in range(4):
            xx = px + pw * band / 3
            qp.drawText(QRectF(xx - 20, py + ph + 5, 40, 20),
                        Qt.AlignCenter, f"波段{band+1}")

        # Y 轴刻度
        for i in range(5):
            val = vmax - (vmax - vmin) * i / 4
            yy = py + ph * i / 4
            qp.drawText(QRectF(0, yy - 10, margin_l - 8, 20),
                        Qt.AlignRight | Qt.AlignVCenter, f"{val:.1f}")

        # 各类别曲线
        for cls_id, st in sorted(self._stats_map.items()):
            color = C_CLASS.get(cls_id, QColor(100, 100, 100))
            pen = QPen(color, 2.5)
            qp.setPen(pen)
            pts = []
            for band in range(4):
                xx = px + pw * band / 3
                yy = py + ph * (1.0 - (st.mean[band] - vmin) / (vmax - vmin))
                pts.append(QPointF(xx, yy))
            for i in range(len(pts) - 1):
                qp.drawLine(pts[i], pts[i + 1])

            # 散点标记
            qp.setBrush(QBrush(color.lighter(130)))
            qp.setPen(QPen(color.darker(120), 1.5))
            for pt in pts:
                qp.drawEllipse(pt, 5, 5)

            # 图例
            bx = w - 130
            by = py + 18 * (cls_id - 1) + 8
            qp.setBrush(QBrush(color))
            qp.setPen(Qt.NoPen)
            qp.drawRect(QRectF(bx, by, 14, 14))
            qp.setPen(C_TEXT)
            qp.setFont(QFont("Microsoft YaHei", 9))
            qp.drawText(QPointF(bx + 20, by + 12), f"类别 {cls_id}")

        # 标题
        qp.setPen(C_TEXT)
        qp.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        qp.drawText(QRectF(0, 4, w, 24), Qt.AlignCenter, "各类地物光谱均值曲线")

    # ── 混淆矩阵热力图 ────────────────────────────────────────

    def _draw_heatmap(self, qp):
        cm = self._cm
        if cm is None or cm.total == 0:
            return
        w, h = self.width(), self.height()
        cell = min((w - 120) / 3, (h - 120) / 3, 110)
        ox = (w - cell * 2) / 2
        oy = (h - cell * 2) / 2 + 15

        cls_ids = sorted(cm.class_ids)

        # 找出最大值做颜色映射
        max_val = max(cm.matrix[r][c] for r in cls_ids for c in cls_ids) or 1

        for ri, true_c in enumerate(cls_ids):
            for ci, pred_c in enumerate(cls_ids):
                val = cm.matrix[true_c][pred_c]
                ratio = val / max_val
                r = int(C_HEAT_LO.red() + (C_HEAT_HI.red() - C_HEAT_LO.red()) * ratio)
                g = int(C_HEAT_LO.green() + (C_HEAT_HI.green() - C_HEAT_LO.green()) * ratio)
                b = int(C_HEAT_LO.blue() + (C_HEAT_HI.blue() - C_HEAT_LO.blue()) * ratio)
                color = QColor(r, g, b)
                qp.setBrush(QBrush(color))
                qp.setPen(QPen(color.darker(130), 1.5))
                qp.drawRect(QRectF(ox + ci * cell, oy + ri * cell, cell, cell))

                # 数值
                qp.setPen(Qt.white if ratio > 0.5 else Qt.black)
                qp.setFont(QFont("Consolas", 11, QFont.Bold))
                qp.drawText(QRectF(ox + ci * cell, oy + ri * cell, cell, cell),
                            Qt.AlignCenter, str(val))

        # 行列标签
        qp.setPen(C_TEXT)
        qp.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        labels = ["真实 类别1", "真实 类别2"]
        for ri, true_c in enumerate(cls_ids):
            qp.drawText(QRectF(ox - 90, oy + ri * cell, 85, cell),
                        Qt.AlignRight | Qt.AlignVCenter, labels[ri])
        plabels = ["预测 类别1", "预测 类别2"]
        for ci, pred_c in enumerate(cls_ids):
            qp.drawText(QRectF(ox + ci * cell, oy - 30, cell, 25),
                        Qt.AlignCenter, plabels[ci])

        # 精度信息
        oa = compute_oa(cm)
        kp = compute_kappa(cm)
        diag = sum(cm.matrix[c][c] for c in cls_ids)
        qp.setFont(QFont("Consolas", 9))
        info_y = oy + cell * 2 + 30
        qp.drawText(QRectF(ox, info_y, cell * 2, 22),
                    Qt.AlignCenter,
                    f"OA = {oa:.4f}    Kappa = {kp:.4f}    对角线 = {diag}")

        # 标题
        qp.setPen(C_TEXT)
        qp.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        qp.drawText(QRectF(0, 4, w, 24), Qt.AlignCenter, "混淆矩阵热力图")


# ══════════════════════════════════════════════════════════════
#  主窗口
# ══════════════════════════════════════════════════════════════

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._calc = MLClassifier()
        self._train_loaded = False
        self._pixels_loaded = False

        self._setup_plot()
        self._setup_tables()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请依次加载 train.txt 和 pixel.txt")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_plot(self):
        layout = self.ui.groupPlot.layout()
        self.ui.plotWidget.setParent(None)
        self._plot = PlotWidget(self.ui.groupPlot)
        self._plot.setMinimumSize(400, 350)
        layout.addWidget(self._plot)

    def _setup_tables(self):
        for tbl in [self.ui.tableStats, self.ui.tableLikelihood, self.ui.tableCM]:
            tbl.setFont(QFont("Consolas", 9))
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _connect_signals(self):
        self.ui.actionOpenTrain.triggered.connect(self.slot_open_train)
        self.ui.actionOpenPixels.triggered.connect(self.slot_open_pixels)
        self.ui.actionRun.triggered.connect(self.slot_run)
        self.ui.actionVerify.triggered.connect(self.slot_verify)
        self.ui.actionExport.triggered.connect(self.slot_export)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open_train(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开训练样本文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._calc = MLClassifier()
            file_io.read_train(path, self._calc)
            self._train_loaded = True
            self.statusBar().showMessage(
                f"已加载训练样本：{path}  |  "
                f"类别数：{len(self._calc.train_samples)}  |  "
                f"总样本：{sum(len(v) for v in self._calc.train_samples.values())}"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_open_pixels(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开待分类像元文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._calc.pixels.clear()
            self._calc.results.clear()
            file_io.read_pixels(path, self._calc)
            self._pixels_loaded = True
            self.statusBar().showMessage(
                f"已加载待分类像元：{path}  |  共{len(self._calc.pixels)}个"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_run(self):
        if not self._train_loaded:
            QMessageBox.warning(self, "提示", "请先加载训练样本文件 (train.txt)")
            return
        if not self._pixels_loaded:
            QMessageBox.warning(self, "提示", "请先加载待分类像元文件 (pixel.txt)")
            return
        try:
            self._calc.compute()
            self._fill_stats_table()
            self._fill_likelihood_table()
            self._plot.show_spectral(self._calc.stats_map)
            self.ui.tabWidget.setCurrentIndex(1)
            cls1 = sum(1 for r in self._calc.results if r.pred_class == 1)
            cls2 = sum(1 for r in self._calc.results if r.pred_class == 2)
            self.statusBar().showMessage(
                f"分类完成  |  共{len(self._calc.results)}像元  "
                f"类别1: {cls1}个  类别2: {cls2}个  |  可加载 verify.txt 进行精度验证"
            )
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_verify(self):
        if not self._calc.results:
            QMessageBox.warning(self, "提示", "请先完成最大似然分类解算")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "打开精度验证样本文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._calc.verify_samples.clear()
            file_io.read_verify(path, self._calc)
            # 重新构建混淆矩阵
            from calculator import build_confusion_matrix
            class_ids = sorted(self._calc.stats_map.keys())
            self._calc.cm = build_confusion_matrix(
                self._calc.verify_samples, self._calc.stats_map, class_ids)

            oa = compute_oa(self._calc.cm)
            kappa = compute_kappa(self._calc.cm)
            self._fill_cm_table()
            self._plot.show_heatmap(self._calc.cm)
            self.ui.tabWidget.setCurrentIndex(2)
            diag = sum(self._calc.cm.matrix[c][c] for c in class_ids)
            self.statusBar().showMessage(
                f"精度验证完成  |  总验证样本: {self._calc.cm.total}  "
                f"正确: {diag}  |  OA={oa:.4f}  Kappa={kappa:.4f}"
            )
        except Exception as e:
            QMessageBox.critical(self, "验证失败", str(e))

    def slot_export(self):
        if not self._calc.results:
            QMessageBox.warning(self, "提示", "请先完成最大似然分类解算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出结果文件", "mlc_result.txt", "文本文件 (*.txt)"
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
        self._calc = MLClassifier()
        self._train_loaded = False
        self._pixels_loaded = False
        for tbl in [self.ui.tableStats, self.ui.tableLikelihood, self.ui.tableCM]:
            tbl.setRowCount(0)
        self._plot.clear_data()
        self.ui.tabWidget.setCurrentIndex(0)
        self.statusBar().showMessage("已清空")

    # ── 训练样本统计表 ────────────────────────────────────────

    def _fill_stats_table(self):
        tbl = self.ui.tableStats
        tbl.setColumnCount(7)
        tbl.setHorizontalHeaderLabels(
            ["类别", "样本数", "B1均值", "B2均值", "B3均值", "B4均值", "ln|Σ|"]
        )
        rows = []
        for cls_id, st in sorted(self._calc.stats_map.items()):
            rows.append((cls_id, st))
        tbl.setRowCount(len(rows))
        for row, (cls_id, st) in enumerate(rows):
            vals = [str(cls_id), str(st.count),
                    f"{st.mean[0]:.4f}", f"{st.mean[1]:.4f}",
                    f"{st.mean[2]:.4f}", f"{st.mean[3]:.4f}",
                    f"{st.log_det:.6f}"]
            bg = C_ALT1 if row % 2 == 0 else C_ALT2
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                tbl.setItem(row, col, item)

    # ── 似然值与分类结果表 ────────────────────────────────────

    def _fill_likelihood_table(self):
        tbl = self.ui.tableLikelihood
        n_cls = len(self._calc.stats_map)
        tbl.setColumnCount(4 + n_cls)
        hdr = ["像元号", "B1", "B2", "B3", "B4"]
        cls_ids = sorted(self._calc.stats_map.keys())
        for c in cls_ids:
            hdr.append(f"类别{c}似然值")
        hdr.append("分类结果")
        tbl.setHorizontalHeaderLabels(hdr)
        tbl.setRowCount(len(self._calc.results))
        for row, pr in enumerate(self._calc.results):
            vals = [str(pr.idx),
                    f"{pr.values[0]:.2f}", f"{pr.values[1]:.2f}",
                    f"{pr.values[2]:.2f}", f"{pr.values[3]:.2f}"]
            for c in cls_ids:
                vals.append(f"{pr.likelihoods.get(c, 0):.4f}")
            vals.append(str(pr.pred_class))
            bg = C_ALT1 if row % 2 == 0 else C_ALT2
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                tbl.setItem(row, col, item)

    # ── 混淆矩阵表 ────────────────────────────────────────────

    def _fill_cm_table(self):
        cm = self._calc.cm
        if cm is None:
            return
        tbl = self.ui.tableCM
        cls_ids = sorted(cm.class_ids)
        tbl.setColumnCount(len(cls_ids) + 1)
        tbl.setHorizontalHeaderLabels(
            ["真实 \\ 预测"] + [f"类别{c}" for c in cls_ids])
        tbl.setRowCount(len(cls_ids) + 1)
        for ri, true_c in enumerate(cls_ids):
            vals = [f"真实 类别{true_c}"]
            for ci, pred_c in enumerate(cls_ids):
                vals.append(str(cm.matrix[true_c][pred_c]))
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(C_ALT1 if ri % 2 == 0 else C_ALT2)
                tbl.setItem(ri, col, item)
        # 精度行
        oa = compute_oa(cm)
        kp = compute_kappa(cm)
        diag = sum(cm.matrix[c][c] for c in cls_ids)
        info_vals = ["精度指标",
                     f"OA={oa:.4f}",
                     f"Kappa={kp:.4f}"]
        for col, text in enumerate(info_vals):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            item.setBackground(QColor(230, 255, 230))
            tbl.setItem(len(cls_ids), col, item)


# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
