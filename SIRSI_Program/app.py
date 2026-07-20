# app.py
# 遥感图像空间前方交会系统 — 主程序

import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView, QWidget
)
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QPainterPath,
    QMouseEvent, QWheelEvent, QLinearGradient
)

from main_window_ui import Ui_MainWindow
from calculator import SpaceIntersectionCalculator
import file_io

# 颜色常量（表格）
C_ALT1 = QColor(240, 246, 255)
C_ALT2 = QColor(248, 248, 248)


# ══════════════════════════════════════════════════════════════
#  三维渲染控件（QPainter 手写管线）
# ══════════════════════════════════════════════════════════════

class GLWidget(QWidget):

    # ── 配色 ──────────────────────────────────────────────────
    BG_TOP    = QColor(45, 50, 65)
    BG_BOT    = QColor(25, 28, 38)
    GRID_MAJ  = QColor(80, 85, 100, 90)
    GRID_MIN  = QColor(55, 60, 72, 50)
    AXIS_X    = QColor(240, 90, 90)
    AXIS_Y    = QColor(90, 220, 90)
    AXIS_Z    = QColor(90, 140, 240)
    C_LEFT    = QColor(60, 160, 255)     # S1 蓝
    C_RIGHT   = QColor(255, 160, 50)     # S2 橙
    C_GROUND  = QColor(80, 230, 150)     # 地面点绿
    C_RAY_L   = QColor(60, 160, 255, 35)
    C_RAY_R   = QColor(255, 160, 50, 35)
    C_BASE    = QColor(220, 220, 240, 150)
    C_INFO    = QColor(180, 185, 200)
    C_HIGHLIGHT = QColor(255, 255, 100)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._azimuth   = 35.0
        self._elevation = 30.0
        self._scale     = 1.0
        self._last_mouse = None
        self._pan_x     = 0.0
        self._pan_y     = 0.0

        # 数据
        self._left_pos    = None
        self._right_pos   = None
        self._left_dir    = None
        self._right_dir   = None
        self._ground_pts  : list = []
        self._labels      : list = []
        self._has_data    = False

        # 轨道中心 / 参考网格
        self._center_3d   = (0.0, 0.0, 0.0)
        self._grid_z      = 0.0

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 350)

    # ── 数据注入 ──────────────────────────────────────────────

    def set_data(self, left_pos, right_pos, left_dir, right_dir,
                 ground_pts, labels=None):
        self._left_pos   = left_pos
        self._right_pos  = right_pos
        self._left_dir   = left_dir
        self._right_dir  = right_dir
        self._ground_pts = ground_pts
        self._labels     = labels or []
        self._has_data   = True

        all_pts = [left_pos, right_pos] + ground_pts
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        zs = [p[2] for p in all_pts]

        # 轨道中心 = 质心（旋转围绕此点）
        self._center_3d = (sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs))
        self._grid_z    = min(zs)

        # 自适应缩放
        rng = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs), 1.0)
        self._scale = min(self.width(), self.height()) * 0.35 / rng
        self._pan_x = 0.0
        self._pan_y = 0.0

        # 最佳默认视角：3/4 等轴侧
        self._azimuth   = 35.0
        self._elevation = 30.0
        self.update()

    def clear_data(self):
        self._has_data = False
        self._ground_pts.clear()
        self._labels.clear()
        self.update()

    # ── 投影引擎 ──────────────────────────────────────────────

    def _project(self, x, y, z):
        """将三维点投影到屏幕，旋转围绕 _center_3d"""
        cx3, cy3, cz3 = self._center_3d
        # 平移到中心
        tx, ty, tz = x - cx3, y - cy3, z - cz3
        az = math.radians(self._azimuth)
        el = math.radians(self._elevation)
        # 绕 Z 旋转
        rx = tx*math.cos(az) - ty*math.sin(az)
        ry = tx*math.sin(az) + ty*math.cos(az)
        rz = tz
        # 绕 X 旋转
        sy = ry*math.cos(el) - rz*math.sin(el)
        sz = ry*math.sin(el) + rz*math.cos(el)
        scx = self.width()/2 + self._pan_x
        scy = self.height()/2 + self._pan_y
        return QPointF(scx + rx*self._scale, scy - sy*self._scale), sz

    def _depth(self, x, y, z):
        """返回深度值（越大越靠近观察者），用于排序"""
        cx3, cy3, cz3 = self._center_3d
        tx, ty, tz = x - cx3, y - cy3, z - cz3
        az = math.radians(self._azimuth)
        el = math.radians(self._elevation)
        ry = tx*math.sin(az) + ty*math.cos(az)
        return ry*math.sin(el) + tz*math.cos(el)

    # ══════════════════════════════════════════════════════════
    #  绘制入口（画家算法：远→近）
    # ══════════════════════════════════════════════════════════

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        # 渐变背景
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, self.BG_TOP)
        grad.setColorAt(1.0, self.BG_BOT)
        qp.fillRect(self.rect(), QBrush(grad))

        if not self._has_data:
            qp.setPen(QColor(150, 155, 170))
            qp.setFont(QFont("Microsoft YaHei", 13))
            qp.drawText(self.rect(), Qt.AlignCenter, "请加载数据并执行空间前方交会解算")
            return

        # ── 第 0 层：地面参考网格 ──
        self._draw_ground_grid(qp)

        # ── 第 1 层：投影光线 ──
        self._draw_rays(qp)

        # ── 第 2 层：基线 ──
        self._draw_baseline(qp)

        # ── 第 3 层：地面点（远→近） ──
        self._draw_ground_points_sorted(qp)

        # ── 第 4 层：摄影中心 ──
        self._draw_camera_full(qp, self._left_pos, self._left_dir, "S₁ 左", self.C_LEFT)
        self._draw_camera_full(qp, self._right_pos, self._right_dir, "S₂ 右", self.C_RIGHT)

        # ── 第 5 层：坐标轴（前景） ──
        self._draw_axes_fixed(qp)

        # ── 第 6 层：信息面板 ──
        self._draw_info_panel(qp)

    # ══════════════════════════════════════════════════════════
    #  地面参考网格
    # ══════════════════════════════════════════════════════════

    def _draw_ground_grid(self, qp):
        gz = self._grid_z
        ox, oy, _ = self._center_3d
        # 以原点锚点为中心，展开 ±spread 范围
        spread = 8000
        step_major = 2000
        step_minor = 500

        # 计算可见范围粗略裁剪
        for step, color, pen_w in [(step_minor, self.GRID_MIN, 0.5),
                                    (step_major, self.GRID_MAJ, 1.2)]:
            pen = QPen(color, pen_w)
            qp.setPen(pen)
            lines = []
            v = ox - spread
            while v <= ox + spread:
                p1, d1 = self._project(v, oy - spread, gz)
                p2, d2 = self._project(v, oy + spread, gz)
                lines.append((-(d1+d2)/2, p1, p2))
                v += step
            v = oy - spread
            while v <= oy + spread:
                p1, d1 = self._project(ox - spread, v, gz)
                p2, d2 = self._project(ox + spread, v, gz)
                lines.append((-(d1+d2)/2, p1, p2))
                v += step
            for _, p1, p2 in lines:
                qp.drawLine(p1, p2)

    # ══════════════════════════════════════════════════════════
    #  投影光线（左右摄影中心 → 各地面点）
    # ══════════════════════════════════════════════════════════

    def _draw_rays(self, qp):
        if not self._ground_pts:
            return
        for pt3d in self._ground_pts:
            if self._left_pos:
                p_cam, _ = self._project(*self._left_pos)
                p_gnd, _ = self._project(*pt3d)
                qp.setPen(QPen(self.C_RAY_L, 0.6))
                qp.drawLine(p_cam, p_gnd)
            if self._right_pos:
                p_cam, _ = self._project(*self._right_pos)
                p_gnd, _ = self._project(*pt3d)
                qp.setPen(QPen(self.C_RAY_R, 0.6))
                qp.drawLine(p_cam, p_gnd)

    # ══════════════════════════════════════════════════════════
    #  基线
    # ══════════════════════════════════════════════════════════

    def _draw_baseline(self, qp):
        if not self._left_pos or not self._right_pos:
            return
        p1, _ = self._project(*self._left_pos)
        p2, _ = self._project(*self._right_pos)
        # 发光底色
        qp.setPen(QPen(QColor(255, 255, 255, 40), 3.5))
        qp.drawLine(p1, p2)
        qp.setPen(QPen(self.C_BASE, 1.5, Qt.DashLine))
        qp.drawLine(p1, p2)
        # 标签
        mid = (p1 + p2) / 2.0
        qp.setPen(self.C_INFO)
        qp.setFont(QFont("Consolas", 8))
        bx = self._right_pos[0] - self._left_pos[0]
        by = self._right_pos[1] - self._left_pos[1]
        bz = self._right_pos[2] - self._left_pos[2]
        qp.drawText(mid + QPointF(6, -4),
                    f"B=({bx:.1f},{by:.1f},{bz:.1f})")

    # ══════════════════════════════════════════════════════════
    #  地面点（画家算法排序，远小近大 + 透明度）
    # ══════════════════════════════════════════════════════════

    def _draw_ground_points_sorted(self, qp):
        if not self._ground_pts:
            return
        # 计算深度并排序
        indexed = []
        for i, pt3d in enumerate(self._ground_pts):
            d = self._depth(*pt3d)
            indexed.append((d, i, pt3d))
        indexed.sort(key=lambda t: t[0])  # 远→近

        for depth, i, pt3d in indexed:
            pt, _ = self._project(*pt3d)
            # 远近映射尺寸
            r = 3.5 + (depth - self._depth(*self._center_3d)) * 0.002
            r = max(2.5, min(7.0, r))
            alpha = 0.55 + 0.45 * (r - 2.5) / 4.5
            c = QColor(self.C_GROUND)
            c.setAlphaF(max(0.4, min(1.0, alpha)))

            # 光晕
            qp.setBrush(Qt.NoBrush)
            qp.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 60), r*2.3))
            qp.drawEllipse(pt, 1, 1)

            # 实心点
            qp.setBrush(QBrush(c))
            qp.setPen(QPen(c.darker(140), 1))
            qp.drawEllipse(pt, r, r)

            # 标签
            if i < len(self._labels):
                qp.setPen(QColor(210, 215, 225, int(255*alpha)))
                qp.setFont(QFont("Consolas", 7))
                qp.drawText(pt + QPointF(r+3, -r-2), str(self._labels[i]))

    # ══════════════════════════════════════════════════════════
    #  摄影中心（相机造型：方向锥 + 球体 + 标签）
    # ══════════════════════════════════════════════════════════

    def _draw_camera_full(self, qp, pos, view_dir, label, color):
        if pos is None:
            return
        pt, _ = self._project(*pos)
        r = 11

        if view_dir is not None:
            # 视线方向线段终点（缩放到屏幕空间）
            vlen = 60
            tip = (pos[0] + view_dir[0]*vlen/self._scale,
                   pos[1] + view_dir[1]*vlen/self._scale,
                   pos[2] + view_dir[2]*vlen/self._scale)
            tp, _ = self._project(*tip)

            # 方向线（发光）
            qp.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 70), 3))
            qp.drawLine(pt, tp)
            qp.setPen(QPen(color, 1.2))
            qp.drawLine(pt, tp)

            # 箭头
            arrow_len = 10
            dx, dy = tp.x() - pt.x(), tp.y() - pt.y()
            dn = math.sqrt(dx*dx + dy*dy)
            if dn > 1:
                dx, dy = dx/dn*arrow_len, dy/dn*arrow_len
                qp.setBrush(QBrush(color))
                qp.setPen(QPen(color.darker(120), 1))
                arrow = QPainterPath()
                arrow.moveTo(tp)
                arrow.lineTo(tp.x() - dx + dy*0.5, tp.y() - dy - dx*0.5)
                arrow.lineTo(tp.x() - dx - dy*0.5, tp.y() - dy + dx*0.5)
                arrow.closeSubpath()
                qp.drawPath(arrow)

        # 外发光
        qp.setBrush(Qt.NoBrush)
        qp.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 50), r*2.2))
        qp.drawEllipse(pt, 2, 2)

        # 主体球
        qp.setBrush(QBrush(color.lighter(120)))
        qp.setPen(QPen(color.darker(130), 2))
        qp.drawEllipse(pt, r, r)

        # 高光
        qp.setBrush(QBrush(QColor(255, 255, 255, 90)))
        qp.setPen(Qt.NoPen)
        qp.drawEllipse(QPointF(pt.x()-r*0.3, pt.y()-r*0.35), r*0.4, r*0.35)

        # 标签
        qp.setPen(Qt.white)
        qp.setFont(QFont("Consolas", 9, QFont.Bold))
        qp.drawText(pt + QPointF(r+3, -r-6), label)
        qp.setPen(QColor(200, 200, 210))
        qp.setFont(QFont("Consolas", 7))
        qp.drawText(pt + QPointF(r+3, 4),
                    f"({pos[0]:.1f},{pos[1]:.1f},{pos[2]:.1f})")

    # ══════════════════════════════════════════════════════════
    #  坐标轴（固定在数据锚点，带刻度）
    # ══════════════════════════════════════════════════════════

    def _draw_axes_fixed(self, qp):
        ox, oy, oz = self._center_3d
        axis_len = 70 / self._scale  # 屏幕像素→数据空间

        def draw_axis(dx, dy, dz, color, label):
            end3d = (ox + dx, oy + dy, oz + dz)
            p0, _ = self._project(ox, oy, oz)
            p1, _ = self._project(*end3d)
            # 主线
            qp.setPen(QPen(color, 2.5))
            qp.drawLine(p0, p1)
            # 箭头
            qp.setBrush(QBrush(color))
            qp.setPen(Qt.NoPen)
            edx, edy = p1.x()-p0.x(), p1.y()-p0.y()
            dn = math.sqrt(edx*edx + edy*edy)
            if dn > 2:
                edx, edy = edx/dn*9, edy/dn*9
                arrow = QPainterPath()
                arrow.moveTo(p1)
                arrow.lineTo(p1.x()-edx+edy*0.4, p1.y()-edy-edx*0.4)
                arrow.lineTo(p1.x()-edx-edy*0.4, p1.y()-edy+edx*0.4)
                arrow.closeSubpath()
                qp.drawPath(arrow)
            # 标签（稍远处）
            label_pt = p1 + QPointF((edx/dn)*12, (edy/dn)*12) if dn > 0 else p1
            qp.setPen(color.lighter(140))
            qp.setFont(QFont("Consolas", 10, QFont.Bold))
            qp.drawText(label_pt, label)
            # 刻度
            tick_count = 4
            tick_len = 5
            for i in range(1, tick_count):
                t = i / tick_count
                tx = ox + dx*t
                ty = oy + dy*t
                tz = oz + dz*t
                tp, _ = self._project(tx, ty, tz)
                qp.setPen(QPen(color, 1, Qt.DotLine))
                qp.drawLine(QPointF(tp.x()-tick_len/2, tp.y()),
                            QPointF(tp.x()+tick_len/2, tp.y()))

        draw_axis(axis_len, 0, 0, self.AXIS_X, "X")
        draw_axis(0, axis_len, 0, self.AXIS_Y, "Y")
        draw_axis(0, 0, axis_len, self.AXIS_Z, "Z")

    # ══════════════════════════════════════════════════════════
    #  信息面板（右上角）
    # ══════════════════════════════════════════════════════════

    def _draw_info_panel(self, qp):
        lines = [
            f"方位角: {self._azimuth:.0f}°",
            f"俯仰角: {self._elevation:.0f}°",
            f"缩放:   {self._scale:.2f}",
            f"地面点: {len(self._ground_pts)}",
            "",
            "左键拖拽  旋转",
            "右键拖拽  平移",
            "滚轮      缩放",
            "+ / -     缩放",
            "方向键    平移",
            "R         重置视角",
        ]
        qp.setFont(QFont("Consolas", 8))
        fm = qp.fontMetrics()
        panel_w = max(fm.width(ln) for ln in lines) + 20
        panel_h = fm.height() * len(lines) + 14
        rx, ry = self.width() - panel_w - 12, 10

        # 半透明底
        qp.setBrush(QBrush(QColor(20, 22, 30, 170)))
        qp.setPen(QPen(QColor(80, 85, 100, 120), 1))
        qp.drawRoundedRect(QRectF(rx, ry, panel_w, panel_h), 6, 6)

        qp.setPen(self.C_INFO)
        for i, ln in enumerate(lines):
            qp.drawText(QPointF(rx + 10, ry + 16 + i * fm.height()), ln)

    # ══════════════════════════════════════════════════════════
    #  交互：鼠标 + 键盘
    # ══════════════════════════════════════════════════════════

    def _reset_view(self):
        """恢复到最佳默认视角"""
        self._azimuth   = 35.0
        self._elevation = 30.0
        self._pan_x     = 0.0
        self._pan_y     = 0.0
        # 重新计算自适应缩放
        if self._has_data:
            all_pts = [self._left_pos, self._right_pos] + self._ground_pts
            xs = [p[0] for p in all_pts]
            ys = [p[1] for p in all_pts]
            zs = [p[2] for p in all_pts]
            rng = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs), 1.0)
            self._scale = min(self.width(), self.height()) * 0.35 / rng
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        self._last_mouse = event.pos()
        self.setFocus()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._last_mouse is None:
            return
        dx = event.x() - self._last_mouse.x()
        dy = event.y() - self._last_mouse.y()
        self._last_mouse = event.pos()

        if event.buttons() & Qt.LeftButton:
            # 左键：旋转
            self._azimuth   += dx * 0.4
            self._elevation -= dy * 0.4
            self._elevation = max(-89, min(89, self._elevation))
            self.update()
        elif event.buttons() & (Qt.MiddleButton | Qt.RightButton):
            # 中键 / 右键：平移
            self._pan_x += dx
            self._pan_y += dy
            self.update()

    def contextMenuEvent(self, event):
        pass  # 禁用右键菜单，留给平移使用

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._last_mouse = None

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y() / 120.0
        # 以鼠标位置为中心缩放
        self._scale *= (1.0 + delta * 0.12)
        self._scale = max(0.005, min(30.0, self._scale))
        self.update()

    def keyPressEvent(self, event):
        step = 20
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self._scale *= 1.15
            self._scale = min(30.0, self._scale)
            self.update()
        elif event.key() == Qt.Key_Minus:
            self._scale /= 1.15
            self._scale = max(0.005, self._scale)
            self.update()
        elif event.key() == Qt.Key_Left:
            self._pan_x -= step
            self.update()
        elif event.key() == Qt.Key_Right:
            self._pan_x += step
            self.update()
        elif event.key() == Qt.Key_Up:
            self._pan_y -= step
            self.update()
        elif event.key() == Qt.Key_Down:
            self._pan_y += step
            self.update()
        elif event.key() == Qt.Key_R or event.key() == Qt.Key_Home:
            self._reset_view()
        else:
            super().keyPressEvent(event)


# ══════════════════════════════════════════════════════════════
#  主窗口
# ══════════════════════════════════════════════════════════════

class App(QMainWindow):

    DATA_COLS = [
        "组号", "x1", "y1", "x2", "y2",
        "x̄1", "ȳ1", "x̄2", "ȳ2",
        "U1", "V1", "W1", "U2", "V2", "W2",
        "N1", "N2", "X", "Y", "Z",
    ]

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._calc = SpaceIntersectionCalculator()
        self._eo_loaded = False
        self._pts_loaded = False

        self._setup_gl()
        self._setup_tables()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请依次加载 bhl1.txt 和 data.txt")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_gl(self):
        layout = self.ui.groupView.layout()
        self.ui.glWidget.setParent(None)
        self._gl = GLWidget(self.ui.groupView)
        self._gl.setMinimumSize(400, 350)
        layout.addWidget(self._gl)

    def _setup_tables(self):
        td = self.ui.tableData
        td.setColumnCount(len(self.DATA_COLS))
        td.setHorizontalHeaderLabels(self.DATA_COLS)
        td.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        td.setFont(QFont("Consolas", 8))

    def _connect_signals(self):
        self.ui.actionOpenEO.triggered.connect(self.slot_open_eo)
        self.ui.actionOpenPoints.triggered.connect(self.slot_open_points)
        self.ui.actionRun.triggered.connect(self.slot_run)
        self.ui.actionExport.triggered.connect(self.slot_export)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open_eo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开外方位元素文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            left, right = file_io.read_eo(path)
            self._calc.set_eo(left, right)
            self._eo_loaded = True
            self.statusBar().showMessage(
                f"已加载外方位元素：{path}  |  "
                f"S1=({left.Xs:.2f},{left.Ys:.2f},{left.Zs:.2f})  "
                f"S2=({right.Xs:.2f},{right.Ys:.2f},{right.Zs:.2f})"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_open_points(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开同名像点文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            pairs = file_io.read_image_points(path)
            self._calc.pairs = pairs
            self._calc.result.pairs = pairs
            self._pts_loaded = True
            self.statusBar().showMessage(
                f"已加载同名像点：{path}  |  共{len(pairs)}组"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_run(self):
        if not self._eo_loaded:
            QMessageBox.warning(self, "提示", "请先加载外方位元素文件 (bhl1.txt)")
            return
        if not self._pts_loaded:
            QMessageBox.warning(self, "提示", "请先加载同名像点文件 (data.txt)")
            return
        try:
            self._calc.compute()
            self._fill_data_table()
            self._update_gl_view()
            res = self._calc.result
            p1 = res.pairs[0]
            self.statusBar().showMessage(
                f"解算完成  |  当前点号:1  |  N1={p1.N1:.4f} N2={p1.N2:.4f}  |  "
                f"地面高程 Z={p1.Z:.3f}  |  共{len(res.pairs)}组"
            )
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_export(self):
        if not self._calc.result.pairs:
            QMessageBox.warning(self, "提示", "请先完成空间前方交会解算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出结果文件", "intersection_result.txt", "文本文件 (*.txt)"
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
        self._calc = SpaceIntersectionCalculator()
        self._eo_loaded = False
        self._pts_loaded = False
        self.ui.tableData.setRowCount(0)
        self._gl.clear_data()
        self.statusBar().showMessage("已清空")

    # ── 填充数据表格 ──────────────────────────────────────────

    def _fill_data_table(self):
        pairs = self._calc.result.pairs
        td = self.ui.tableData
        td.setRowCount(len(pairs))
        for row, p in enumerate(pairs):
            vals = [
                str(p.idx),
                f"{p.x1:.3f}", f"{p.y1:.3f}", f"{p.x2:.3f}", f"{p.y2:.3f}",
                f"{p.x1_bar:.3f}", f"{p.y1_bar:.3f}",
                f"{p.x2_bar:.3f}", f"{p.y2_bar:.3f}",
                f"{p.U1:.3f}", f"{p.V1:.3f}", f"{p.W1:.3f}",
                f"{p.U2:.3f}", f"{p.V2:.3f}", f"{p.W2:.3f}",
                f"{p.N1:.4f}", f"{p.N2:.4f}",
                f"{p.X:.3f}", f"{p.Y:.3f}", f"{p.Z:.3f}",
            ]
            bg = C_ALT1 if row % 2 == 0 else C_ALT2
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                td.setItem(row, col, item)

    # ── 更新三维视图 ──────────────────────────────────────────

    def _update_gl_view(self):
        L = self._calc.result.left_eo
        R = self._calc.result.right_eo
        pts = [(p.X, p.Y, p.Z) for p in self._calc.result.pairs]
        labels = [str(p.idx) for p in self._calc.result.pairs]

        # 相机视线方向 = R · [0, 0, -1] = (-a3, -b3, -c3)
        def _view_dir(Rmat):
            return (-Rmat[0][2], -Rmat[1][2], -Rmat[2][2])

        self._gl.set_data(
            (L.Xs, L.Ys, L.Zs),
            (R.Xs, R.Ys, R.Zs),
            _view_dir(L.R),
            _view_dir(R.R),
            pts, labels
        )


# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
