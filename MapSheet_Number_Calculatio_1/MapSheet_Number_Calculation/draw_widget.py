# draw_widget.py
# 图幅绘制控件：用 QPainter 绘制图幅网格与测量点

import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont


class DrawWidget(QWidget):
    """
    绘制指定比例尺下的图幅网格和测量点位置
    """

    GRID_COLOR   = QColor(100, 149, 237)    # 图幅格网：矢车菊蓝
    POINT_COLOR  = QColor(220,  30,  30)    # 测量点：红
    LABEL_COLOR  = QColor( 50,  50,  50)    # 文字：深灰
    BG_COLOR     = QColor(245, 250, 255)    # 背景：淡蓝白
    MARGIN       = 40                        # 边距(px)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._points  = []     # list[GeoPoint]
        self._scale   = "10万" # 当前比例尺
        self.setMinimumSize(400, 300)

    def set_data(self, points: list, scale: str):
        self._points = points
        self._scale  = scale
        self.update()

    def clear(self):
        self._points = []
        self.update()

    # ── Qt 绘制入口 ───────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.BG_COLOR)

        if not self._points:
            painter.setPen(QColor(180, 180, 180))
            painter.setFont(QFont("微软雅黑", 13))
            painter.drawText(self.rect(), Qt.AlignCenter, "请先打开文件并计算，再点击「绘图」")
            return

        self._draw_map(painter)

    # ── 绘制图幅 ──────────────────────────────────────────────
    def _draw_map(self, painter: QPainter):
        from calculator import SCALES, boundary_10w, _sw_corner_10w

        pts = self._points
        scale_name = self._scale

        # 数据范围
        B_list = [p.B for p in pts]
        L_list = [p.L for p in pts]
        B_min, B_max = min(B_list), max(B_list)
        L_min, L_max = min(L_list), max(L_list)

        # 扩展边距
        dB, dL = SCALES[scale_name]
        B_min -= dB; B_max += dB
        L_min -= dL; L_max += dL

        W = self.width()  - 2 * self.MARGIN
        H = self.height() - 2 * self.MARGIN

        def to_px(B, L):
            x = self.MARGIN + (L - L_min) / (L_max - L_min) * W
            y = self.MARGIN + (B_max - B) / (B_max - B_min) * H
            return x, y

        # 绘制图幅网格
        painter.setPen(QPen(self.GRID_COLOR, 0.8, Qt.SolidLine))

        # 纬线
        B = math.floor(B_min / dB) * dB
        while B <= B_max + dB:
            x1, y1 = to_px(B, L_min)
            x2, y2 = to_px(B, L_max)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            B += dB

        # 经线
        L = math.floor(L_min / dL) * dL
        while L <= L_max + dL:
            x1, y1 = to_px(B_min, L)
            x2, y2 = to_px(B_max, L)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            L += dL

        # 高亮当前点所在图幅
        for p in pts:
            bnd = boundary_10w(p.B, p.L) if scale_name == "10万" else None
            if bnd:
                x1, y1 = to_px(bnd["北"], bnd["西"])
                x2, y2 = to_px(bnd["南"], bnd["东"])
                fill = QColor(255, 255, 180, 60)
                painter.fillRect(QRectF(x1, y1, x2-x1, y2-y1), fill)
                painter.setPen(QPen(QColor(200, 150, 0), 1.5))
                painter.drawRect(QRectF(x1, y1, x2-x1, y2-y1))

        # 绘制测量点
        painter.setBrush(QBrush(self.POINT_COLOR))
        painter.setPen(QPen(Qt.white, 0.8))
        for p in pts:
            px, py = to_px(p.B, p.L)
            painter.drawEllipse(QPointF(px, py), 5, 5)

        # 点名标注
        painter.setPen(self.LABEL_COLOR)
        painter.setFont(QFont("微软雅黑", 7))
        for p in pts:
            px, py = to_px(p.B, p.L)
            painter.drawText(QPointF(px + 7, py - 4), p.name)

        # 标题
        painter.setFont(QFont("微软雅黑", 10, QFont.Bold))
        painter.setPen(self.LABEL_COLOR)
        painter.drawText(
            QPointF(self.MARGIN, self.MARGIN - 10),
            f"1:{scale_name} 图幅分布图"
        )
