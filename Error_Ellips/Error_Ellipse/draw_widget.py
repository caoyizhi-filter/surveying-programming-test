# draw_widget.py
# 绘图区：继承 QWidget，用 QPainter 绘制误差椭圆
# 在 Qt Designer 里将 widget_canvas「提升」为此类

import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont


class DrawWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._points = []   # 由 app.py 调用 set_points() 传入

    def set_points(self, points: list):
        self._points = points
        self.update()   # 触发 paintEvent

    def clear(self):
        self._points = []
        self.update()

    # ── Qt 绘制入口 ───────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 白色背景
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        if not self._points:
            painter.setPen(QColor(180, 180, 180))
            painter.setFont(QFont("微软雅黑", 13))
            painter.drawText(self.rect(), Qt.AlignCenter, "请先打开文件并计算")
            return

        self._draw_ellipses(painter)

    # ── 绘制所有椭圆（网格排列）──────────────────────────────
    def _draw_ellipses(self, painter: QPainter):
        n    = len(self._points)
        cols = max(1, math.ceil(math.sqrt(n)))
        rows = math.ceil(n / cols)
        cw   = self.width()  / cols
        ch   = self.height() / rows

        for i, p in enumerate(self._points):
            cx = cw * (i % cols) + cw / 2
            cy = ch * (i // cols) + ch / 2
            self._draw_one(painter, p, cx, cy, cw, ch)

    def _draw_one(self, painter, p, cx, cy, cw, ch):
        """绘制单个椭圆"""
        # 缩放：让椭圆不超出单元格
        max_axis = max(p.E, p.F, 1e-9)
        scale    = min(cw, ch) / 2 * 0.65 / max_axis
        a = p.E * scale   # 长半轴像素
        b = p.F * scale   # 短半轴像素

        # 颜色：异常=红，正常=蓝
        if p.anomaly:
            line_color = QColor(200, 30, 30)
            fill_color = QColor(255, 180, 180, 60)
        else:
            line_color = QColor(30, 100, 200)
            fill_color = QColor(173, 216, 230, 60)

        painter.save()
        painter.translate(cx, cy)

        # 坐标轴
        axis = min(cw, ch) * 0.38
        painter.setPen(QPen(QColor(180, 180, 180), 0.8, Qt.DashLine))
        painter.drawLine(QPointF(-axis, 0), QPointF(axis, 0))
        painter.drawLine(QPointF(0, -axis), QPointF(0, axis))

        # 旋转画布，绘制椭圆
        painter.rotate(-p.phi_E)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(line_color, 2))
        painter.drawEllipse(QPointF(0, 0), a, b)

        # 长轴方向线
        painter.setPen(QPen(line_color, 1.5, Qt.SolidLine))
        painter.drawLine(QPointF(-a, 0), QPointF(a, 0))

        painter.restore()

        # 点名标注（不随旋转）
        label = p.name + (" ⚠" if p.anomaly else "")
        painter.setPen(QColor(50, 50, 50))
        font = QFont("微软雅黑", 8, QFont.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()

        # 点名 + 异常标记
        painter.drawText(
            QPointF(cx - fm.horizontalAdvance(label) / 2,
                    cy + b + 14),
            label
        )

        # E / F 数值
        info = f"E={p.E:.4f}  F={p.F:.4f}  φ={p.phi_E:.1f}°"
        painter.setFont(QFont("Consolas", 7))
        fm2 = painter.fontMetrics()
        painter.drawText(
            QPointF(cx - fm2.horizontalAdvance(info) / 2,
                    cy + b + 26),
            info
        )

        # 异常点加红色提示
        if p.anomaly:
            warn = "⚠ 异常点"
            painter.setPen(QColor(200, 30, 30))
            painter.setFont(QFont("微软雅黑", 7, QFont.Bold))
            fm3 = painter.fontMetrics()
            painter.drawText(
                QPointF(cx - fm3.horizontalAdvance(warn) / 2,
                        cy + b + 38),
                warn
            )
