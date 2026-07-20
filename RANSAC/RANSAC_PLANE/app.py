# app.py
# RANSAC 稳健平面参数估计系统 — 主程序

import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QWidget,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QPen, QBrush, QPolygon,
    QMouseEvent, QWheelEvent
)

from main_window_ui import Ui_MainWindow
from calculator import RANSACCalculator
import file_io


# ══════════════════════════════════════════════════════════════
#  颜色常量
# ══════════════════════════════════════════════════════════════

C_INLIER  = QColor(200, 255, 200)   # 绿：内点
C_OUTLIER = QColor(255, 200, 200)   # 红：粗差
C_ALT1    = QColor(235, 245, 235)
C_ALT2    = QColor(248, 248, 248)


# ══════════════════════════════════════════════════════════════
#  3D 可视化控件（纯 QPainter 实现）
# ══════════════════════════════════════════════════════════════

class GLWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 350)
        self.setMouseTracking(True)

        self._azimuth   = 30.0
        self._elevation = 25.0
        self._zoom      = 1.0
        self._last_mouse = None

        self._pts_xyz     = []        # [(x,y,z), ...]
        self._inlier_flags = []       # [bool, ...]
        self._planes       = {}       # {"S1":(A,B,C,D), "J1":(...), "J2":(...)}
        self._proj_pts     = {}       # {"P5_proj":(x,y,z), "P800_proj":(x,y,z)}
        self._highlight    = {}       # {"P5":(x,y,z), "P800":(x,y,z)}
        self._bounds       = (0, 100, 0, 100, 0, 2)

    def set_data(self, pts_xyz, inlier_flags, planes, proj_pts, highlight, bounds):
        self._pts_xyz       = pts_xyz
        self._inlier_flags  = inlier_flags
        self._planes        = planes
        self._proj_pts      = proj_pts
        self._highlight     = highlight
        self._bounds        = bounds
        self.update()

    # ── 3D → 2D 投影 ──────────────────────────────────────

    def _project(self, x, y, z):
        az = math.radians(self._azimuth)
        el = math.radians(self._elevation)
        x1 = x * math.cos(az) - y * math.sin(az)
        y1 = x * math.sin(az) + y * math.cos(az)
        z1 = z
        y2 = y1 * math.cos(el) - z1 * math.sin(el)
        z2 = y1 * math.sin(el) + z1 * math.cos(el)
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        scale = self._zoom * min(self.width(), self.height()) / 120.0
        return cx + x1 * scale, cy - y2 * scale, z2

    # ── 交互 ──────────────────────────────────────────────

    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.LeftButton:
            self._last_mouse = ev.pos()

    def mouseMoveEvent(self, ev: QMouseEvent):
        if self._last_mouse is not None:
            dx = ev.x() - self._last_mouse.x()
            dy = ev.y() - self._last_mouse.y()
            self._azimuth   += dx * 0.5
            self._elevation += dy * 0.5
            self._elevation = max(-89.0, min(89.0, self._elevation))
            self._last_mouse = ev.pos()
            self.update()

    def mouseReleaseEvent(self, ev: QMouseEvent):
        self._last_mouse = None

    def wheelEvent(self, ev: QWheelEvent):
        delta = ev.angleDelta().y() / 120.0
        self._zoom *= (1.0 + delta * 0.1)
        self._zoom = max(0.1, min(10.0, self._zoom))
        self.update()

    # ── 渲染 ──────────────────────────────────────────────

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(25, 25, 35))

        if not self._pts_xyz:
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "请先打开点云文件并执行 RANSAC 计算")
            painter.end()
            return

        xmin, xmax, ymin, ymax, zmin, zmax = self._bounds

        # ---- 平面 ----
        plane_cfg = {
            "S1": (QColor(60, 140, 255, 70),  QColor(80, 160, 255, 150)),
            "J1": (QColor(60, 255, 140, 60),  QColor(80, 255, 160, 140)),
            "J2": (QColor(255, 200, 60, 60),  QColor(255, 220, 80, 140)),
        }
        for name, (A, B, C, D) in self._planes.items():
            fc, lc = plane_cfg.get(name, (QColor(100, 100, 100, 50),
                                          QColor(150, 150, 150, 120)))
            self._draw_plane(painter, A, B, C, D,
                             xmin, xmax, ymin, ymax, fc, lc)

        # ---- 散点（按深度排序） ----
        proj_list = []
        n = len(self._pts_xyz)
        for i, (x, y, z) in enumerate(self._pts_xyz):
            sx, sy, sz = self._project(x, y, z)
            is_in = self._inlier_flags[i] if i < n else True
            proj_list.append((sz, sx, sy, is_in))
        proj_list.sort(key=lambda t: t[0], reverse=True)

        for _, sx, sy, is_inlier in proj_list:
            color = QColor(80, 230, 80) if is_inlier else QColor(255, 60, 60)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(sx), int(sy)), 2, 2)

        # ---- 投影连线 ----
        for pk, (hx, hy, hz) in self._highlight.items():
            proj_key = pk + "_proj"
            if proj_key not in self._proj_pts:
                continue
            px, py, pz = self._proj_pts[proj_key]
            hsx, hsy, _ = self._project(hx, hy, hz)
            psx, psy, _ = self._project(px, py, pz)

            pen = QPen(QColor(255, 255, 100, 150), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(QPoint(int(hsx), int(hsy)),
                             QPoint(int(psx), int(psy)))
            painter.setBrush(QBrush(QColor(255, 255, 0)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(hsx), int(hsy)), 5, 5)
            painter.setBrush(QBrush(QColor(255, 160, 0)))
            painter.drawEllipse(QPoint(int(psx), int(psy)), 5, 5)

        # ---- 图例 ----
        self._draw_legend(painter)
        painter.end()

    def _draw_plane(self, painter, A, B, C, D,
                    xmin, xmax, ymin, ymax, fill_c, line_c):
        if abs(C) < 1e-12:
            return
        gn = 14
        xs = [xmin + (xmax - xmin) * i / (gn - 1) for i in range(gn)]
        ys = [ymin + (ymax - ymin) * i / (gn - 1) for i in range(gn)]
        grid = []
        for x in xs:
            row = []
            for y in ys:
                z = -(A * x + B * y + D) / C
                sx, sy, _ = self._project(x, y, z)
                row.append((sx, sy))
            grid.append(row)

        for i in range(gn - 1):
            for j in range(gn - 1):
                poly = [QPoint(int(grid[i][j][0]),     int(grid[i][j][1])),
                        QPoint(int(grid[i+1][j][0]),   int(grid[i+1][j][1])),
                        QPoint(int(grid[i+1][j+1][0]), int(grid[i+1][j+1][1])),
                        QPoint(int(grid[i][j+1][0]),   int(grid[i][j+1][1]))]
                painter.setBrush(QBrush(fill_c))
                painter.setPen(Qt.NoPen)
                painter.drawPolygon(QPolygon(poly))

        pen = QPen(line_c, 0.5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        for row in grid:
            for i in range(len(row) - 1):
                painter.drawLine(
                    QPoint(int(row[i][0]), int(row[i][1])),
                    QPoint(int(row[i+1][0]), int(row[i+1][1])))
        for j in range(len(grid[0])):
            for i in range(len(grid) - 1):
                painter.drawLine(
                    QPoint(int(grid[i][j][0]), int(grid[i][j][1])),
                    QPoint(int(grid[i+1][j][0]), int(grid[i+1][j][1])))

    def _draw_legend(self, painter):
        painter.setFont(QFont("Consolas", 9))
        y = 15
        for text, color in [
            ("● 内点", QColor(80, 230, 80)),
            ("● 粗差", QColor(255, 60, 60)),
            ("S1 平面", QColor(80, 160, 255)),
            ("J1 平面", QColor(80, 255, 160)),
            ("J2 平面", QColor(255, 220, 80)),
        ]:
            painter.setPen(QPen(color, 1))
            painter.drawText(10, y, text)
            y += 18


# ══════════════════════════════════════════════════════════════
#  主窗口
# ══════════════════════════════════════════════════════════════

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._calc = None

        self._setup_gl()
        self._setup_tables()
        self._connect_signals()
        self.statusBar().showMessage("就绪  |  请打开 plane_cloud.txt")

    # ── 初始化 ────────────────────────────────────────────────

    def _setup_gl(self):
        """将 GLWidget 安装到 groupView 占位区域"""
        self._gl = GLWidget(self.ui.groupView)
        layout = self.ui.groupView.layout()
        # 移除占位 QWidget，替换为 GLWidget
        old = self.ui.glWidget
        if old and layout:
            layout.replaceWidget(old, self._gl)
            old.hide()

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
            self, "打开点云数据文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            self._calc = file_io.read_input(path)
            self._fill_points_table(colored=False)
            self.ui.tableResult.setRowCount(0)
            self._gl.set_data([], [], {}, {}, {}, (0, 100, 0, 100, 0, 2))
            self.statusBar().showMessage(
                f"已加载：{path}  |  共{len(self._calc.points)}个测点  请点击「RANSAC平面解算」"
            )
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_run(self):
        if not self._calc:
            QMessageBox.warning(self, "提示", "请先打开 plane_cloud.txt")
            return
        try:
            self._calc.compute()
            res = self._calc.result
            self._fill_points_table(colored=True)
            self._fill_result_table()
            self._update_gl_view()

            msg = (
                f"RANSAC解算完成  |  "
                f"总点数:{res.total_pts}  "
                f"S1内点:{res.s1_inlier_count}  "
                f"S1粗差:{res.s1_outlier_count}  |  "
                f"J1内点:{res.j1_inlier_count}  "
                f"J2内点:{res.j2_inlier_count}  |  "
                f"三角面积:{res.triangle_area:.4f}"
            )
            self.statusBar().showMessage(msg)
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_export(self):
        if not self._calc or not self._calc.result.total_pts:
            QMessageBox.warning(self, "提示", "请先完成RANSAC解算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出结果文件", "plane_analysis_result.txt", "文本文件 (*.txt)"
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
        self._gl.set_data([], [], {}, {}, {}, (0, 100, 0, 100, 0, 2))
        self.statusBar().showMessage("已清空")

    # ── 填充测点表格 ──────────────────────────────────────────

    def _fill_points_table(self, colored: bool):
        pts = self._calc.points
        t   = self.ui.tablePoints
        t.setRowCount(len(pts))
        for row, p in enumerate(pts):
            bg = (C_INLIER if p.is_inlier else C_OUTLIER) if colored else QColor(248, 248, 248)
            vals = [str(p.idx), f"{p.x:.3f}", f"{p.y:.3f}", f"{p.z:.3f}"]
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                t.setItem(row, col, item)

    # ── 填充43项结果表格 ─────────────────────────────────────

    def _fill_result_table(self):
        res  = self._calc.result
        calc = self._calc
        p5   = calc.points[4]
        p8   = calc.points[799]

        rows = [
            ("1",  "P5的X坐标值",                    f"{p5.x:.3f}"),
            ("2",  "P5的Y坐标值",                    f"{p5.y:.3f}"),
            ("3",  "P5的Z坐标值",                    f"{p5.z:.3f}"),
            ("4",  "全部点X坐标最小值",              f"{res.xmin:.3f}"),
            ("5",  "全部点X坐标最大值",              f"{res.xmax:.3f}"),
            ("6",  "全部点Y坐标最小值",              f"{res.ymin:.3f}"),
            ("7",  "全部点Y坐标最大值",              f"{res.ymax:.3f}"),
            ("8",  "全部点Z坐标最小值",              f"{res.zmin:.3f}"),
            ("9",  "全部点Z坐标最大值",              f"{res.zmax:.3f}"),
            ("10", "P5所在栅格行号i",               str(res.grid_i)),
            ("11", "P5所在栅格列号j",               str(res.grid_j)),
            ("12", "P5所在栅格内总测点数",          str(res.grid_count)),
            ("13", "P5所在栅格高程平均值",          f"{res.grid_mean:.3f}"),
            ("14", "P5所在栅格高程最大值",          f"{res.grid_max:.3f}"),
            ("15", "P5所在栅格高程高差",            f"{res.grid_range:.3f}"),
            ("16", "P5所在栅格高程方差",            f"{res.grid_var:.3f}"),
            ("17", "三点P1P2P3围成三角形面积",       f"{res.triangle_area:.6f}"),
            ("18", "RANSAC拟合平面S1参数A",          f"{res.s1_A:.6f}"),
            ("19", "RANSAC拟合平面S1参数B",          f"{res.s1_B:.6f}"),
            ("20", "RANSAC拟合平面S1参数C",          f"{res.s1_C:.6f}"),
            ("21", "RANSAC拟合平面S1参数D",          f"{res.s1_D:.6f}"),
            ("22", "测点P1000到平面S1垂直距离",       f"{res.dist_p1000_s1:.3f}"),
            ("23", "测点P5到平面S1垂直距离",         f"{res.dist_p5_s1:.3f}"),
            ("24", "拟合平面S1内点数量",             str(res.s1_inlier_count)),
            ("25", "拟合平面S1粗差点数量",           str(res.s1_outlier_count)),
            ("26", "最优分割平面J1参数A",            f"{res.j1_A:.6f}"),
            ("27", "最优分割平面J1参数B",            f"{res.j1_B:.6f}"),
            ("28", "最优分割平面J1参数C",            f"{res.j1_C:.6f}"),
            ("29", "最优分割平面J1参数D",            f"{res.j1_D:.9f}"),
            ("30", "分割平面J1内点数量",             str(res.j1_inlier_count)),
            ("31", "分割平面J1粗差点数量",           str(res.j1_outlier_count)),
            ("32", "分割平面J2参数A",                f"{res.j2_A:.6f}"),
            ("33", "分割平面J2参数B",                f"{res.j2_B:.6f}"),
            ("34", "分割平面J2参数C",                f"{res.j2_C:.6f}"),
            ("35", "分割平面J2参数D",                f"{res.j2_D:.9f}"),
            ("36", "分割平面J2内点数量",             str(res.j2_inlier_count)),
            ("37", "分割平面J2粗差点数量",           str(res.j2_outlier_count)),
            ("38", "P5在平面J1投影X坐标xi",          f"{res.proj_p5_x:.3f}"),
            ("39", "P5在平面J1投影Y坐标yi",          f"{res.proj_p5_y:.3f}"),
            ("40", "P5在平面J1投影Z坐标zi",          f"{res.proj_p5_z:.2f}"),
            ("41", "P800在平面J1投影X坐标xi",        f"{res.proj_p800_x:.3f}"),
            ("42", "P800在平面J1投影Y坐标yi",        f"{res.proj_p800_y:.3f}"),
            ("43", "P800在平面J1投影Z坐标zi",        f"{res.proj_p800_z:.3f}"),
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

    # ── 更新3D视图 ───────────────────────────────────────────

    def _update_gl_view(self):
        res = self._calc.result
        pts = self._calc.points
        n = len(pts)

        inlier_set = set(p.idx for p in res.s1_inlier_pts)
        inlier_flags = [(p.idx in inlier_set) for p in pts]

        planes = {"S1": (res.s1_A, res.s1_B, res.s1_C, res.s1_D)}
        if abs(res.j1_C) > 1e-12:
            planes["J1"] = (res.j1_A, res.j1_B, res.j1_C, res.j1_D)
        if abs(res.j2_C) > 1e-12:
            planes["J2"] = (res.j2_A, res.j2_B, res.j2_C, res.j2_D)

        proj = {
            "P5_proj":   (res.proj_p5_x,   res.proj_p5_y,   res.proj_p5_z),
            "P800_proj": (res.proj_p800_x, res.proj_p800_y, res.proj_p800_z),
        }
        hl = {
            "P5":   (pts[4].x, pts[4].y, pts[4].z),
            "P800": (pts[799].x, pts[799].y, pts[799].z),
        }

        xyz = [(p.x, p.y, p.z) for p in pts]
        self._gl.set_data(xyz, inlier_flags, planes, proj, hl,
                          (res.xmin, res.xmax, res.ymin, res.ymax,
                           res.zmin, res.zmax))


# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
