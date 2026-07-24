# ============================================================
# gui.py —— 界面文件（换题零改动）
# ============================================================
# 只依赖 ransac_core.run_all() 的 table_rows 和 config 两个字段。
# 换题时修改 ransac_core.py，本文件不动。
# ============================================================

import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTableWidgetItem,
                              QHeaderView, QAction, QStatusBar, QSplitter,
                              QGroupBox, QVBoxLayout, QTableWidget, QLabel)
from PyQt5.QtCore import Qt

from ransac_core import run_all, WINDOW_TITLE


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.resize(1100, 720)

        # 使用绝对路径，确保文件能找到
        self._cloud_path = os.path.join(os.path.dirname(__file__), "plane_cloud.txt")
        self._table_rows = None
        self._config = None

        # 先搭建界面组件（表格需要先创建）
        self._setup_actions()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central()
        self.setStatusBar(QStatusBar())

        # 只获取题目配置（标题），不执行计算
        self._load_title()

    def _load_title(self):
        """只获取竞赛题目标题（不执行计算）"""
        self.setWindowTitle(WINDOW_TITLE)
        self.statusBar().showMessage("请选择数据文件并点击计算")

    def _fill_table(self):
        """填充结果表格"""
        t = self.tableResult
        t.setRowCount(len(self._table_rows))
        for i, (no, lb, val) in enumerate(self._table_rows):
            item = QTableWidgetItem(str(no))
            item.setTextAlignment(Qt.AlignCenter)
            t.setItem(i, 0, item)
            item = QTableWidgetItem(lb)
            item.setTextAlignment(Qt.AlignCenter)
            t.setItem(i, 1, item)
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            t.setItem(i, 2, item)

    # ---- 界面搭建 ----

    def _setup_actions(self):
        self.actOpen = QAction("点云数据", self)
        self.actOpen.triggered.connect(self._open)
        self.actCalc = QAction("计算", self)
        self.actCalc.triggered.connect(self._calc)
        self.actSave = QAction("导出", self)
        self.actSave.triggered.connect(self._save)
        self.actClear = QAction("清空", self)
        self.actClear.triggered.connect(self._clear)
        self.actExit = QAction("退出", self)
        self.actExit.triggered.connect(self.close)

    def _setup_menubar(self):
        mb = self.menuBar()
        menuF = mb.addMenu("文件(&F)")
        menuF.addAction(self.actOpen)
        menuF.addSeparator()
        menuF.addAction(self.actSave)
        menuF.addSeparator()
        menuF.addAction(self.actClear)
        menuF.addSeparator()
        menuF.addAction(self.actExit)
        mb.addMenu("计算(&C)").addAction(self.actCalc)

    def _setup_toolbar(self):
        tb = self.addToolBar("工具栏")
        tb.addAction(self.actOpen)
        tb.addSeparator()
        tb.addAction(self.actCalc)
        tb.addSeparator()
        tb.addAction(self.actSave)
        tb.addAction(self.actClear)

    def _setup_central(self):
        self.labelFile = QLabel("未加载数据")
        gb = QGroupBox("输入参数")
        gb.setMinimumSize(220, 0)
        lay = QVBoxLayout(gb)
        lay.addWidget(self.labelFile)

        # 表格列头需与 ransac_core 输出的 table_rows 三元组对应
        self.tableResult = QTableWidget()
        self.tableResult.setColumnCount(3)
        self.tableResult.setHorizontalHeaderLabels(["序号", "指标", "计算结果"])
        h = self.tableResult.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(gb)
        splitter.addWidget(self.tableResult)
        self.setCentralWidget(splitter)

    # ---- 槽函数 ----

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "", "", "文本文件 (*.txt);;所有文件 (*)")
        if not path:
            return
        self._cloud_path = path
        filename = os.path.basename(path)
        self.labelFile.setText(f"点云数据: {filename}")

    def _calc(self):
        try:
            r = run_all(self._cloud_path, "result.txt")
        except Exception as e:
            self.statusBar().showMessage(f"计算失败: {e}")
            return

        self._table_rows = r["table_rows"]
        self._config = r.get("config", {})

        # 填充表格
        self._fill_table()

        # 从 config 读取标题和状态栏
        title = self._config.get("window_title", WINDOW_TITLE)
        self.setWindowTitle(title)
        msg = self._config.get("status_message", "计算完成")
        self.statusBar().showMessage(msg)

    def _save(self):
        if not self._table_rows:
            return
        default_name = "result.txt"
        if self._config:
            default_name = self._config.get("output_file", "result.txt")
        path, _ = QFileDialog.getSaveFileName(self, "", default_name, "文本文件 (*.txt)")
        if not path:
            return
        # CSV 表头需与 ransac_core.run_all() 内部保持一致
        with open(path, "w", encoding="utf-8") as f:
            f.write("序号,指标名称,计算结果\n")
            for no, lb, val in self._table_rows:
                f.write(f"{no},{lb},{val}\n")

    def _clear(self):
        self._cloud_path = os.path.join(os.path.dirname(__file__), "plane_cloud.txt")
        self._table_rows = None
        self._config = None
        self.tableResult.setRowCount(0)
        self.labelFile.setText("未加载数据")
        # 恢复标题为竞赛题目
        self.setWindowTitle(WINDOW_TITLE)
        self.statusBar().showMessage("请选择数据文件并点击计算")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())
