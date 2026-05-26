import sys
from PyQt5 import QtWidgets
import file_io
from calculator import GaussCalculator
from main_window_ui import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 绑定下拉菜单可用参考椭球
        self.comboEllipsoid.addItems(list(GaussCalculator.ELLIPSOIDS.keys()))
        self.comboEllipsoid.setCurrentText("CGCS2000")

        # 将输入框默认参数清空，启动后界面保持为空
        self.editB.clear()
        self.editL.clear()
        self.editL0.clear()
        self.editL1.clear()

        # 绑定按钮事件逻辑
        self.btnLoadFile.clicked.connect(self.on_load_file)
        self.btnCalculate.clicked.connect(self.on_calculate)
        self.btnSaveFile.clicked.connect(self.on_save_file)

        self.results_data = []
        self.statusbar.showMessage("就绪。请点击 '读入数据' 引入数据。")

    def on_load_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "导入输入文件", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                B, L, L0, L1 = file_io.read_input_file(file_path)
                self.editB.setText(f"{B:.3f}")
                self.editL.setText(f"{L:.3f}")
                self.editL0.setText(f"{L0:.1f}")
                self.editL1.setText(f"{L1:.1f}")
                self.statusbar.showMessage(f"已成功读入数据文件: {file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "导入失败", f"无法正确加载文件: {str(e)}")

    def on_calculate(self):
        # 在计算前先检查输入框是否为空
        if (not self.editB.text().strip() or
                not self.editL.text().strip() or
                not self.editL0.text().strip() or
                not self.editL1.text().strip()):
            QtWidgets.QMessageBox.warning(self, "输入缺失", "输入参数不能为空，请先载入文件或手动输入数据。")
            return

        try:
            # 1. 读取编辑框数值
            B_deg = float(self.editB.text().strip())
            L_deg = float(self.editL.text().strip())
            L0_deg = float(self.editL0.text().strip())
            L1_deg = float(self.editL1.text().strip())

            # 2. 设置椭球实例
            ellipsoid_name = self.comboEllipsoid.currentText()
            calc = GaussCalculator(ellipsoid_name)

            # 3. 完成核心计算
            x_fwd, y_fwd, l_rad = calc.forward(B_deg, L_deg, L0_deg)
            B_inv, L_inv = calc.inverse(x_fwd, y_fwd, L0_deg)
            x_new, y_new, _ = calc.forward(B_deg, L_deg, L1_deg)

            n0 = calc.get_zone_number(L_deg)
            n1 = calc.get_zone_number(L1_deg)

            # 4. 按标准要求格式化结果
            self.results_data = [
                ("1", "正算 x", f"{x_fwd:.3f}"),
                ("2", "正算 y", f"{y_fwd:.3f}"),
                ("3", "反算 B", f"{B_inv:.3f}"),
                ("4", "反算 L", f"{L_inv:.3f}"),
                ("5", "换带后 x", f"{x_new:.3f}"),
                ("6", "换带后 y", f"{y_new:.3f}"),
                ("7", "经差 l", f"{l_rad:.6f}"),
                ("8", "原带带号", f"{n0}"),
                ("9", "邻带带号", f"{n1}")
            ]

            # 5. 渲染表格
            self.tableResults.setRowCount(len(self.results_data))
            for row_idx, item in enumerate(self.results_data):
                self.tableResults.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(item[0]))
                self.tableResults.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(item[1]))
                self.tableResults.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(item[2]))

            self.statusbar.showMessage("计算已完成。")

        except ValueError:
            QtWidgets.QMessageBox.warning(self, "输入错误", "请检查并保证全部参数为正确数值。")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "异常", f"执行中遇到非预期问题: {str(e)}")

    def on_save_file(self):
        if not self.results_data:
            QtWidgets.QMessageBox.warning(self, "警告", "请先进行计算后再保存。")
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "导出计算结果", "result.txt", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                file_io.write_output_file(file_path, self.results_data)
                self.statusbar.showMessage(f"保存至: {file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "导出失败", f"无法写入目标文件: {str(e)}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())