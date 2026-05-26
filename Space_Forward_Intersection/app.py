# app.py
# 空间前方交会解算系统 — 主程序

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMessageBox, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from main_window_ui import Ui_MainWindow
from calculator import ImageData, SpaceIntersection
import file_io


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._solver = None

        self._setup_table()
        self._connect_signals()
        self._clear_inputs()  # 启动时清空所有输入框
        self.statusBar().showMessage("就绪  |  请打开 input1.txt")

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
        self.ui.actionSave.triggered.connect(self.slot_save)
        self.ui.actionClear.triggered.connect(self.slot_clear)
        self.ui.actionExit.triggered.connect(self.close)

    def _clear_inputs(self):
        """清空所有输入框"""
        fields = [
            "edit_xs1", "edit_ys1", "edit_zs1",
            "edit_phi1", "edit_omega1", "edit_kappa1",
            "edit_xs2", "edit_ys2", "edit_zs2",
            "edit_phi2", "edit_omega2", "edit_kappa2",
            "edit_x0", "edit_y0", "edit_f",
            "edit_x1", "edit_y1", "edit_x2", "edit_y2",
        ]
        for name in fields:
            getattr(self.ui, name).setText("")

    # ── 从界面读取输入参数 ────────────────────────────────────

    def _read_ui_inputs(self) -> SpaceIntersection:
        """从左侧表单读取所有输入，构建 SpaceIntersection 对象"""
        def g(name):
            text = getattr(self.ui, name).text().strip()
            if not text:
                raise ValueError(f"参数「{name}」为空，请先打开输入文件或手动填写")
            return float(text)

        left = ImageData(
            Xs=g("edit_xs1"), Ys=g("edit_ys1"), Zs=g("edit_zs1"),
            phi_deg=g("edit_phi1"), omega_deg=g("edit_omega1"), kappa_deg=g("edit_kappa1")
        )
        right = ImageData(
            Xs=g("edit_xs2"), Ys=g("edit_ys2"), Zs=g("edit_zs2"),
            phi_deg=g("edit_phi2"), omega_deg=g("edit_omega2"), kappa_deg=g("edit_kappa2")
        )
        solver = SpaceIntersection()
        solver.left  = left
        solver.right = right
        solver.x0    = g("edit_x0")
        solver.y0    = g("edit_y0")
        solver.f     = g("edit_f")
        solver.x1    = g("edit_x1")
        solver.y1    = g("edit_y1")
        solver.x2    = g("edit_x2")
        solver.y2    = g("edit_y2")
        return solver

    # ── 将读入数据填回表单 ────────────────────────────────────

    def _fill_ui_inputs(self, solver: SpaceIntersection):
        L, R = solver.left, solver.right
        fields = {
            "edit_xs1": L.Xs,       "edit_ys1": L.Ys,       "edit_zs1": L.Zs,
            "edit_phi1": L.phi_deg, "edit_omega1": L.omega_deg, "edit_kappa1": L.kappa_deg,
            "edit_xs2": R.Xs,       "edit_ys2": R.Ys,       "edit_zs2": R.Zs,
            "edit_phi2": R.phi_deg, "edit_omega2": R.omega_deg, "edit_kappa2": R.kappa_deg,
            "edit_x0": solver.x0,  "edit_y0": solver.y0,   "edit_f": solver.f,
            "edit_x1": solver.x1,  "edit_y1": solver.y1,
            "edit_x2": solver.x2,  "edit_y2": solver.y2,
        }
        for name, val in fields.items():
            getattr(self.ui, name).setText(str(val))

    # ── 槽函数 ────────────────────────────────────────────────

    def slot_open(self):
        """打开 input1.txt，解析后填入左侧表单"""
        path, _ = QFileDialog.getOpenFileName(
            self, "打开输入文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return
        try:
            solver = file_io.read_input(path)
            self._fill_ui_inputs(solver)
            self._solver = None
            self.ui.tableResult.setRowCount(0)
            self.ui.textDetail.clear()
            self.statusBar().showMessage(f"已加载：{path}    请点击「计算」")
        except Exception as e:
            QMessageBox.critical(self, "读取失败", str(e))

    def slot_calc(self):
        """从表单读取参数并执行前方交会计算"""
        try:
            solver = self._read_ui_inputs()
            solver.compute()
            self._solver = solver
            self._fill_table()
            self._fill_detail()
            res = solver.result
            self.statusBar().showMessage(
                f"计算完成  |  X={res.X:.3f}  Y={res.Y:.3f}  Z={res.Z:.3f}"
            )
        except ValueError as e:
            QMessageBox.critical(self, "输入错误", str(e))
        except Exception as e:
            QMessageBox.critical(self, "计算失败", str(e))

    def slot_save(self):
        """保存 result1.txt"""
        if not self._solver:
            QMessageBox.warning(self, "提示", "请先完成计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果文件", "result1.txt", "文本文件 (*.txt)"
        )
        if not path:
            return
        try:
            file_io.write_result(path, self._solver)
            self.statusBar().showMessage(f"结果已保存：{path}")
            QMessageBox.information(self, "保存成功", f"文件已保存：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def slot_clear(self):
        self._solver = None
        self._clear_inputs()
        self.ui.tableResult.setRowCount(0)
        self.ui.textDetail.clear()
        self.statusBar().showMessage("已清除")

    # ── 填充结果表格（7项）───────────────────────────────────

    def _fill_table(self):
        s   = self._solver
        res = s.result
        L, R = s.left, s.right

        rows = [
            ("1", "地面点 X (m)",   f"{res.X:.3f}"),
            ("2", "地面点 Y (m)",   f"{res.Y:.3f}"),
            ("3", "地面点 Z (m)",   f"{res.Z:.3f}"),
            ("4", "φ1 弧度",        f"{L.phi:.6f}"),
            ("5", "κ2 弧度",        f"{R.kappa:.6f}"),
            ("6", "左片 a1",        f"{L.a1:.6f}"),
            ("7", "右片 b2",        f"{R.b2:.6f}"),
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

    # ── 填充右下详细参数面板 ──────────────────────────────────

    def _fill_detail(self):
        s    = self._solver
        L, R = s.left, s.right
        res  = s.result

        text = f"""╔══════════════════════════════════════════╗
║        空间前方交会计算详细报告           ║
╚══════════════════════════════════════════╝

【地面点坐标】
  X = {res.X:.3f} m
  Y = {res.Y:.3f} m
  Z = {res.Z:.3f} m

【左片外方位元素】
  摄站坐标  : ({L.Xs:.3f}, {L.Ys:.3f}, {L.Zs:.3f}) m
  φ1 = {L.phi_deg}°  →  {L.phi:.6f} rad
  ω1 = {L.omega_deg}°  →  {L.omega:.6f} rad
  κ1 = {L.kappa_deg}°  →  {L.kappa:.6f} rad

【左片方向余弦矩阵 R1】
  a1={L.a1:.6f}  b1={L.b1:.6f}  c1={L.c1:.6f}
  a2={L.a2:.6f}  b2={L.b2:.6f}  c2={L.c2:.6f}
  a3={L.a3:.6f}  b3={L.b3:.6f}  c3={L.c3:.6f}

【右片外方位元素】
  摄站坐标  : ({R.Xs:.3f}, {R.Ys:.3f}, {R.Zs:.3f}) m
  φ2 = {R.phi_deg}°  →  {R.phi:.6f} rad
  ω2 = {R.omega_deg}°  →  {R.omega:.6f} rad
  κ2 = {R.kappa_deg}°  →  {R.kappa:.6f} rad

【右片方向余弦矩阵 R2】
  a1={R.a1:.6f}  b1={R.b1:.6f}  c1={R.c1:.6f}
  a2={R.a2:.6f}  b2={R.b2:.6f}  c2={R.c2:.6f}
  a3={R.a3:.6f}  b3={R.b3:.6f}  c3={R.c3:.6f}

【相机内方位元素】
  x0={s.x0} mm  y0={s.y0} mm  f={s.f} mm

【同名像点坐标】
  左像点 : x1={s.x1} mm  y1={s.y1} mm
  右像点 : x2={s.x2} mm  y2={s.y2} mm
"""
        self.ui.textDetail.setFont(QFont("Consolas", 9))
        self.ui.textDetail.setText(text)


# ══════════════════════════════════════════════════════════════
#  程序入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
