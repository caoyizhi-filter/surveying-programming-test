# app.py
# 道路曲线要素计算与里程桩计算 — 主程序

import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPixmap

from main_window_ui import Ui_MainWindow
from calculator import RoadCurve, dms_to_decimal
import file_io


# ══════════════════════════════════════════════════════════════
#  桩号格式化：1326.480 → "K1+326.480"
# ══════════════════════════════════════════════════════════════

def format_stake(value: float) -> str:
    km = int(value / 1000)
    m = value - km * 1000
    return f"K{km}+{m:.3f}"


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._curve = None

        # 固定画布尺寸，配合 scaledContents 缩放，杜绝 label 驱动 splitter 扩张
        from PyQt5.QtWidgets import QSizePolicy
        self.ui.labelDraw.setScaledContents(True)
        self.ui.labelDraw.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self._setup_table()
        self._connect_signals()
        self._clear_inputs()
        self.statusBar().showMessage("就绪  |  请打开 curve_input.txt")

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
        self.ui.actionDraw.triggered.connect(self.slot_draw)
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    def _clear_inputs(self):
        fields = ["edit_jd", "edit_r", "edit_deg", "edit_min", "edit_sec", "edit_stake"]
        for name in fields:
            getattr(self.ui, name).setText("")

    # ── 从界面读取输入 ────────────────────────────────────────

    def _read_ui_inputs(self) -> RoadCurve:
        def g(name):
            text = getattr(self.ui, name).text().strip()
            if not text:
                raise ValueError(f"参数「{name}」为空，请先打开输入文件或手动填写")
            return float(text)

        curve = RoadCurve(
            JD_stake=g("edit_jd"),
            R=g("edit_r"),
            alpha_deg=g("edit_deg"),
            alpha_min=g("edit_min"),
            alpha_sec=g("edit_sec"),
        )
        stake_text = self.ui.edit_stake.text().strip()
        if stake_text:
            curve.specified_stake = float(stake_text)

        return curve

    # ── 将数据填回表单 ────────────────────────────────────────

    def _fill_ui_inputs(self, curve: RoadCurve):
        self.ui.edit_jd.setText(str(curve.JD_stake))
        self.ui.edit_r.setText(str(int(curve.R)))
        self.ui.edit_deg.setText(str(int(curve.alpha_deg_raw)))
        self.ui.edit_min.setText(str(int(curve.alpha_min_raw)))
        self.ui.edit_sec.setText(str(curve.alpha_sec_raw))

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开输入文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            curve = file_io.read_input(path)
            self._fill_ui_inputs(curve)
            self._curve = None
            self.ui.tableResult.setRowCount(0)
            self.ui.labelDraw.setText("请先计算，再点击「绘图」")
            self.statusBar().showMessage(
                f"已加载：{path}  |  JD={format_stake(curve.JD_stake)}  "
                f"R={curve.R:.0f}m  α={curve.alpha_deg_raw:.0f}°{curve.alpha_min_raw:.0f}′{curve.alpha_sec_raw:.3f}″  "
                f"请点击「计算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_calc(self):
        try:
            curve = self._read_ui_inputs()
            curve.compute_elements()
            curve.compute_stakes()

            # 如果填写了指定桩号，计算局部坐标
            stake_text = self.ui.edit_stake.text().strip()
            has_stake = bool(stake_text)

            if has_stake:
                try:
                    curve.compute_local_coords(float(stake_text))
                except ValueError as e:
                    QMessageBox.critical(self, "桩号错误", str(e))
                    return

            self._curve = curve
            self._fill_table()
            self.statusBar().showMessage(
                f"计算完成  |  ZY={format_stake(curve.ZY)}  "
                f"QZ={format_stake(curve.QZ)}  "
                f"YZ={format_stake(curve.YZ)}  |  "
                f"校核差={abs(curve.JD_check - curve.JD_stake):.4f}m"
            )
        except ValueError as e:
            QMessageBox.critical(self, "输入错误", str(e))
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_draw(self):
        if not self._curve:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        self._draw_curve()

    def slot_save(self):
        if not self._curve:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "road_curve_result.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            file_io.write_result(path, self._curve)
            self.statusBar().showMessage(f"结果已保存：{path}")
            QMessageBox.information(self, "保存成功", f"文件已保存：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def slot_clear(self):
        self._curve = None
        self._clear_inputs()
        self.ui.tableResult.setRowCount(0)
        self.ui.labelDraw.clear()
        self.ui.labelDraw.setText("请先计算，再点击「绘图」")
        self.statusBar().showMessage("已清除")

    # ── 填充结果表格（13项）───────────────────────────────────

    def _fill_table(self):
        c = self._curve

        # 桩号格式化
        def fs(v): return format_stake(v)

        rows = [
            ("1",  "JD 原始里程",          f"{c.JD_stake:.3f}"),
            ("2",  "圆曲线半径 R",         f"{c.R:.0f}"),
            ("3",  "路偏角 α (十进制度)",  f"{c.alpha_deg:.4f}"),
            ("4",  "切线长 T",             f"{c.T:.3f}"),
            ("5",  "曲线总长 L",           f"{c.L:.3f}"),
            ("6",  "外距 E",               f"{c.E:.3f}"),
            ("7",  "校差值 D",             f"{c.D:.3f}"),
            ("8",  "直圆点 ZY 里程",       fs(c.ZY)),
            ("9",  "曲中点 QZ 里程",       fs(c.QZ)),
            ("10", "圆直点 YZ 里程",       fs(c.YZ)),
            ("11", "校核 JD 里程",         f"{c.JD_check:.3f}"),
            ("12", "指定桩号距 ZY 弧长 l", f"{c.l:.3f}" if c.l else "（未指定）"),
            ("13", "指定桩号局部坐标 (x,y)",
             f"{c.x:.3f}, {c.y:.3f}" if c.l else "（未指定）"),
        ]

        t = self.ui.tableResult
        t.setRowCount(len(rows))
        colors = [QColor(230, 245, 255), QColor(255, 255, 255)]

        for row, (no, label, val) in enumerate(rows):
            bg = colors[row % 2]
            for col, text in enumerate([no, label, val]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)

    # ── 绘制曲线示意图 ────────────────────────────────────────

    def _draw_curve(self):
        c = self._curve

        # 固定画布尺寸 — pixmap 始终为此大小，由 scaledContents 负责缩放显示
        CW, CH = 900, 380
        pixmap = QPixmap(CW, CH)
        pixmap.fill(Qt.white)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘图区域边距
        margin = 60
        plt_w = CW - 2 * margin
        plt_h = CH - 2 * margin

        if plt_w <= 0 or plt_h <= 0:
            painter.end()
            self.ui.labelDraw.setPixmap(pixmap)
            return

        # 坐标系：ZY 在左下，YZ 在右下偏上
        # JD 在 ZY-YZ 连线的上方（外距方向）
        # 以 ZY 为原点，切线方向为 x，内法线方向为 y

        # 曲线理论范围
        half_alpha = c.alpha_rad / 2.0
        # 弦长 ZY→YZ
        chord = 2.0 * c.R * math.sin(half_alpha)
        # JD 到 ZY-YZ 弦的距离
        jd_height = c.R * (1.0 - math.cos(half_alpha)) + c.E

        # x 范围：[0, chord]，y 范围：[0, jd_height]
        x_range = chord
        y_range = max(jd_height, chord * 0.3)

        scale_x = plt_w / x_range if x_range > 0 else 1
        scale_y = plt_h / y_range if y_range > 0 else 1
        scale = min(scale_x, scale_y)

        ox = margin + (plt_w - x_range * scale) / 2.0
        oy = margin + plt_h - (plt_h - y_range * scale) / 2.0

        def tx(x): return ox + x * scale
        def ty(y): return oy - y * scale

        # ── 绘制 ZY→YZ 弦线（虚线）─────────────────────────────
        pen_dash = QPen(QColor(180, 180, 180), 1, Qt.DashLine)
        painter.setPen(pen_dash)
        painter.drawLine(int(tx(0)), int(ty(0)),
                         int(tx(chord)), int(ty(0)))

        # ── 绘制切线方向线 ──────────────────────────────────────
        pen_tangent = QPen(QColor(200, 200, 200), 1, Qt.DashLine)
        painter.setPen(pen_tangent)
        tan_extend = chord * 0.15
        # ZY 处切线（水平向右）
        painter.drawLine(int(tx(-tan_extend)), int(ty(0)),
                         int(tx(chord * 0.3)), int(ty(0)))
        # YZ 处切线（方向角 = α）
        yz_tx_end = tx(chord + tan_extend * math.cos(c.alpha_rad))
        yz_ty_end = ty(-tan_extend * math.sin(c.alpha_rad))
        painter.drawLine(int(tx(chord)), int(ty(0)),
                         int(yz_tx_end), int(yz_ty_end))

        # ── 绘制圆曲线（弧线）─────────────────────────────────
        pen_curve = QPen(QColor(0, 100, 200), 3)
        painter.setPen(pen_curve)
        steps = 100
        pts = []
        for i in range(steps + 1):
            beta = c.alpha_rad * i / steps
            xi = c.R * math.sin(beta)
            yi = c.R * (1.0 - math.cos(beta))
            pts.append((int(tx(xi)), int(ty(yi))))
        for i in range(len(pts) - 1):
            painter.drawLine(pts[i][0], pts[i][1],
                             pts[i + 1][0], pts[i + 1][1])

        # ── 绘制 JD 点 ──────────────────────────────────────────
        # JD 在 T * sin(α/2) 方向偏离 ZY-YZ 弦（指向曲线外侧）
        # JD 相对于 ZY 的位置：水平 T*cos(α/2)，垂直 T*sin(α/2)
        # 但这是从 ZY 看的方向，实际上：
        # JD 在 ZY 坐标系中：(T*cos(α/2), T*sin(α/2)) 但这里y是内法线方向...
        # 实际上 JD 在 ZY 的前方切线方向距离为 T
        # ZY→JD 方向是切线方向，即水平向右
        jd_x = c.T
        jd_y = 0.0
        # 划线 JD→ZY
        pen_jd = QPen(QColor(200, 80, 80), 1, Qt.DashLine)
        painter.setPen(pen_jd)
        painter.drawLine(int(tx(jd_x)), int(ty(jd_y)),
                         int(tx(0)), int(ty(0)))
        # 划线 JD→YZ
        painter.drawLine(int(tx(jd_x)), int(ty(jd_y)),
                         int(tx(chord)), int(ty(0)))

        # ── 绘制主点标记 ──────────────────────────────────────
        def draw_point(x, y, label, color, above=True):
            r = 5
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(130), 2))
            painter.drawEllipse(int(tx(x)) - r, int(ty(y)) - r, r * 2, r * 2)
            painter.setPen(QPen(Qt.black, 1))
            font = QFont("Consolas", 9, QFont.Bold)
            painter.setFont(font)
            offset = -18 if above else 18
            painter.drawText(int(tx(x)) - 20, int(ty(y)) + offset, label)

        # ZY
        draw_point(0, 0, "ZY", QColor(0, 150, 50))
        # YZ
        draw_point(chord, 0, "YZ", QColor(0, 150, 50))
        # QZ
        qz_beta = c.alpha_rad / 2.0
        qz_x = c.R * math.sin(qz_beta)
        qz_y = c.R * (1.0 - math.cos(qz_beta))
        draw_point(qz_x, qz_y, "QZ", QColor(0, 100, 200))
        # JD
        draw_point(jd_x, 0, "JD", QColor(220, 60, 60), above=False)

        # ── 如果指定了桩号，绘制该点 ──────────────────────────
        if c.l > 0:
            sx, sy = c.x, c.y
            painter.setBrush(QBrush(QColor(255, 140, 0)))
            painter.setPen(QPen(QColor(200, 100, 0), 2))
            r = 4
            painter.drawEllipse(int(tx(sx)) - r, int(ty(sy)) - r, r * 2, r * 2)
            painter.setPen(QPen(Qt.black, 1))
            font = QFont("Consolas", 8)
            painter.setFont(font)
            stk_label = format_stake(c.specified_stake)
            painter.drawText(int(tx(sx)) + 8, int(ty(sy)) - 8, stk_label)

        painter.end()
        self.ui.labelDraw.setPixmap(pixmap)
        self.statusBar().showMessage("曲线示意图已绘制")

    # ── 窗口大小变化时重绘 ───────────────────────────────────



# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
