# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 720)
        MainWindow.setMinimumWidth(1000)

        # ── 菜单动作 ──────────────────────────────────────────
        self.actionOpenDirect = QtWidgets.QAction(MainWindow)
        self.actionOpenDirect.setObjectName("actionOpenDirect")
        self.actionOpenDirect.setText("读取正算文件(&D)")
        self.actionOpenDirect.setShortcut("Ctrl+D")

        self.actionOpenInverse = QtWidgets.QAction(MainWindow)
        self.actionOpenInverse.setObjectName("actionOpenInverse")
        self.actionOpenInverse.setText("读取反算文件(&I)")
        self.actionOpenInverse.setShortcut("Ctrl+I")

        self.actionCalc = QtWidgets.QAction(MainWindow)
        self.actionCalc.setObjectName("actionCalc")
        self.actionCalc.setText("执行计算(&C)")
        self.actionCalc.setShortcut("Ctrl+C")

        self.actionSave = QtWidgets.QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave.setText("导出结果(&S)")
        self.actionSave.setShortcut("Ctrl+S")

        self.actionClear = QtWidgets.QAction(MainWindow)
        self.actionClear.setObjectName("actionClear")
        self.actionClear.setText("清空(&R)")

        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionExit.setText("退出(&X)")
        self.actionExit.setShortcut("Alt+F4")

        # ── 中心部件 ──────────────────────────────────────────
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.mainLayout.setObjectName("mainLayout")

        # ── 椭球参数栏（公用） ────────────────────────────────
        self.groupEll = QtWidgets.QGroupBox(self.centralwidget)
        self.groupEll.setObjectName("groupEll")
        self.groupEll.setMaximumHeight(70)
        self.ellLayout = QtWidgets.QHBoxLayout(self.groupEll)
        self.ellLayout.setObjectName("ellLayout")

        self.labelEll = QtWidgets.QLabel(self.groupEll)
        self.labelEll.setObjectName("labelEll")
        self.labelEll.setText("椭球参数: 未加载")
        self.labelEll.setFont(QtGui.QFont("Consolas", 11))
        self.ellLayout.addWidget(self.labelEll)

        self.labelFileInfo = QtWidgets.QLabel(self.groupEll)
        self.labelFileInfo.setObjectName("labelFileInfo")
        self.labelFileInfo.setText("")
        self.labelFileInfo.setAlignment(QtCore.Qt.AlignRight)
        self.ellLayout.addWidget(self.labelFileInfo)

        self.mainLayout.addWidget(self.groupEll)

        # ── Tab 切换 ──────────────────────────────────────────
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setFont(QtGui.QFont("Microsoft YaHei", 10))

        # ────── Tab 1: 正算 ───────────────────────────────────
        self.tabDirect = QtWidgets.QWidget()
        self.tabDirect.setObjectName("tabDirect")
        self.directLayout = QtWidgets.QVBoxLayout(self.tabDirect)
        self.directLayout.setObjectName("directLayout")

        # 正算输入信息
        self.groupDirectInput = QtWidgets.QGroupBox(self.tabDirect)
        self.groupDirectInput.setObjectName("groupDirectInput")
        self.groupDirectInput.setMaximumHeight(100)
        self.directInputLayout = QtWidgets.QVBoxLayout(self.groupDirectInput)
        self.directInputLayout.setObjectName("directInputLayout")

        self.labelDirectInput = QtWidgets.QLabel(self.groupDirectInput)
        self.labelDirectInput.setObjectName("labelDirectInput")
        self.labelDirectInput.setText("输入数据: 请读取正算文件")
        self.labelDirectInput.setWordWrap(True)
        self.labelDirectInput.setFont(QtGui.QFont("Consolas", 10))
        self.directInputLayout.addWidget(self.labelDirectInput)

        self.directLayout.addWidget(self.groupDirectInput)

        # 正算结果表
        self.tableDirect = QtWidgets.QTableWidget(self.tabDirect)
        self.tableDirect.setObjectName("tableDirect")
        self.directLayout.addWidget(self.tableDirect)

        self.tabWidget.addTab(self.tabDirect, "正算 (B1,L1,A12,S → B2,L2,A21)")

        # ────── Tab 2: 反算 ───────────────────────────────────
        self.tabInverse = QtWidgets.QWidget()
        self.tabInverse.setObjectName("tabInverse")
        self.inverseLayout = QtWidgets.QVBoxLayout(self.tabInverse)
        self.inverseLayout.setObjectName("inverseLayout")

        # 反算输入信息
        self.groupInverseInput = QtWidgets.QGroupBox(self.tabInverse)
        self.groupInverseInput.setObjectName("groupInverseInput")
        self.groupInverseInput.setMaximumHeight(100)
        self.inverseInputLayout = QtWidgets.QVBoxLayout(self.groupInverseInput)
        self.inverseInputLayout.setObjectName("inverseInputLayout")

        self.labelInverseInput = QtWidgets.QLabel(self.groupInverseInput)
        self.labelInverseInput.setObjectName("labelInverseInput")
        self.labelInverseInput.setText("输入数据: 请读取反算文件")
        self.labelInverseInput.setWordWrap(True)
        self.labelInverseInput.setFont(QtGui.QFont("Consolas", 10))
        self.inverseInputLayout.addWidget(self.labelInverseInput)

        self.inverseLayout.addWidget(self.groupInverseInput)

        # 反算结果表
        self.tableInverse = QtWidgets.QTableWidget(self.tabInverse)
        self.tableInverse.setObjectName("tableInverse")
        self.inverseLayout.addWidget(self.tableInverse)

        self.tabWidget.addTab(self.tabInverse, "反算 (B1,L1,B2,L2 → S,A12,A21)")

        self.mainLayout.addWidget(self.tabWidget)

        # ── 底部状态信息 ──────────────────────────────────────
        self.groupStatus = QtWidgets.QGroupBox(self.centralwidget)
        self.groupStatus.setObjectName("groupStatus")
        self.groupStatus.setMaximumHeight(80)
        self.statusLayout = QtWidgets.QHBoxLayout(self.groupStatus)
        self.statusLayout.setObjectName("statusLayout")

        self.labelIterInfo = QtWidgets.QLabel(self.groupStatus)
        self.labelIterInfo.setObjectName("labelIterInfo")
        self.labelIterInfo.setText("迭代信息: -")
        self.labelIterInfo.setWordWrap(True)
        self.labelIterInfo.setFont(QtGui.QFont("Consolas", 10))
        self.statusLayout.addWidget(self.labelIterInfo)

        self.mainLayout.addWidget(self.groupStatus)

        MainWindow.setCentralWidget(self.centralwidget)

        # ── 菜单栏 ────────────────────────────────────────────
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")

        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")

        self.menuCalc = QtWidgets.QMenu(self.menubar)
        self.menuCalc.setObjectName("menuCalc")

        MainWindow.setMenuBar(self.menubar)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuCalc.menuAction())

        self.menuFile.addAction(self.actionOpenDirect)
        self.menuFile.addAction(self.actionOpenInverse)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionClear)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.menuCalc.addAction(self.actionCalc)

        # ── 工具栏 ────────────────────────────────────────────
        self.toolbar = QtWidgets.QToolBar(MainWindow)
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.addAction(self.actionOpenDirect)
        self.toolbar.addAction(self.actionOpenInverse)
        self.toolbar.addAction(self.actionCalc)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.actionSave)
        self.toolbar.addAction(self.actionClear)
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)

        # ── 状态栏 ────────────────────────────────────────────
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "大地主题正反算"))
        self.groupEll.setTitle(_translate("MainWindow", "椭球参数"))
        self.groupDirectInput.setTitle(_translate("MainWindow", "正算输入"))
        self.groupInverseInput.setTitle(_translate("MainWindow", "反算输入"))
        self.groupStatus.setTitle(_translate("MainWindow", "计算状态"))
        self.tabWidget.setTabText(0, _translate("MainWindow", "正算 (B1,L1,A12,S → B2,L2,A21)"))
        self.tabWidget.setTabText(1, _translate("MainWindow", "反算 (B1,L1,B2,L2 → S,A12,A21)"))
        self.menuFile.setTitle(_translate("MainWindow", "文件(&F)"))
        self.menuCalc.setTitle(_translate("MainWindow", "计算(&C)"))
        self.actionOpenDirect.setText(_translate("MainWindow", "读取正算文件(&D)"))
        self.actionOpenInverse.setText(_translate("MainWindow", "读取反算文件(&I)"))
        self.actionCalc.setText(_translate("MainWindow", "执行计算(&C)"))
        self.actionSave.setText(_translate("MainWindow", "导出结果(&S)"))
        self.actionClear.setText(_translate("MainWindow", "清空(&R)"))
        self.actionExit.setText(_translate("MainWindow", "退出(&X)"))
        self.toolbar.setWindowTitle(_translate("MainWindow", "工具栏"))
