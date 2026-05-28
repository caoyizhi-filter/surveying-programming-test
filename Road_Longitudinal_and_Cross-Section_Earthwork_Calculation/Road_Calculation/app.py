# app.py
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, QHeaderView
from main_window_ui import Ui_MainWindow
from file_io import read_input_file, write_result_file
from calculator import calculate_earthwork

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.sections = None
        self.query_stake = None
        self.results = None
        self.input_filepath = None

        # 初始功能按钮约束
        self.btn_calc.setEnabled(False)
        self.btn_save.setEnabled(False)

        # 单元格内容自动调整适应
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 挂载按钮交互信号
        self.btn_load.clicked.connect(self.load_file)
        self.btn_calc.clicked.connect(self.run_calculation)
        self.btn_save.clicked.connect(self.save_results)

        self.statusBar.showMessage("准备就绪，请导入观测数据文本。")

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择输入数据文件", "", "Text Files (*.txt);;All Files (*)", options=options
        )
        if file_path:
            try:
                self.input_filepath = file_path
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.txt_input_view.setText(f.read())
                
                self.sections, self.query_stake = read_input_file(file_path)
                self.statusBar.showMessage(f"已装载：{os.path.basename(file_path)}")
                self.btn_calc.setEnabled(True)
                self.btn_save.setEnabled(False)
                self.table_results.setRowCount(0)
            except Exception as e:
                QMessageBox.critical(self, "格式错误", f"解析数据文本失败:\n{str(e)}")

    def run_calculation(self):
        if not self.sections or self.query_stake is None:
            QMessageBox.warning(self, "提示", "未找到完整的观测数据。")
            return
        try:
            # 运行核心计算公式
            self.results = calculate_earthwork(self.sections, self.query_stake)
            self.display_results()
            self.statusBar.showMessage("核心算法执行成功。")
            self.btn_save.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "计算异常", f"算法模块运行遇到故障:\n{str(e)}")

    def display_results(self):
        self.table_results.setRowCount(8)
        items = [
            ("1", "断面 1 高程", f"{self.results['sec1_ground_elev']:.2f}"),
            ("2", "断面 2 高程", f"{self.results['sec2_ground_elev']:.2f}"),
            ("3", "断面 1 面积", f"{self.results['sec1_area']:.2f}"),
            ("4", "断面 2 面积", f"{self.results['sec2_area']:.2f}"),
            ("5", "间距", f"{int(self.results['distance'])}"),
            ("6", "土方总量", f"{self.results['total_volume']:.2f}"),
            ("7", "测点总数", f"{int(self.results['sec1_points_count'])}"),
            ("8", "设计高程", f"{self.results['query_design_elev']:.2f}")
        ]

        for i, (num, desc, val) in enumerate(items):
            self.table_results.setItem(i, 0, QTableWidgetItem(num))
            self.table_results.setItem(i, 1, QTableWidgetItem(desc))
            self.table_results.setItem(i, 2, QTableWidgetItem(val))

    def save_results(self):
        if not self.results:
            QMessageBox.warning(self, "提示", "尚未生成可导出的计算数据。")
            return
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存计算结果", "result4.txt", "Text Files (*.txt);;All Files (*)", options=options
        )
        if file_path:
            try:
                write_result_file(file_path, self.results)
                QMessageBox.information(self, "保存成功", f"结果成功写入至目标文件：\n{file_path}")
                self.statusBar.showMessage("文件导出成功。")
            except Exception as e:
                QMessageBox.critical(self, "写出故障", f"无法完成文件写出:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())