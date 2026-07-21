# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 720)
        MainWindow.setMinimumWidth(1000)

        # ── 菜单动作 ──────────────────────────────────────────
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionOpen.setText("打开(&O)")
        self.actionOpen.setShortcut("Ctrl+O")

        self.actionCalc = QtWidgets.QAction(MainWindow)
        self.actionCalc.setObjectName("actionCalc")
        self.actionCalc.setText("计算(&C)")
        self.actionCalc.setShortcut("Ctrl+C")

        self.actionSave = QtWidgets.QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave.setText("保存(&S)")
        self.actionSave.setShortcut("Ctrl+S")

        self.actionClear = QtWidgets.QAction(MainWindow)
        self.actionClear.setObjectName("actionClear")
        self.actionClear.setText("清除(&R)")

        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionExit.setText("退出(&X)")
        self.actionExit.setShortcut("Alt+F4")

        # ── 中心部件 ──────────────────────────────────────────
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.mainLayout.setObjectName("mainLayout")

        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")

        # ── 左：信息面板 ────────────────────────────────────────
        self.groupInput = QtWidgets.QGroupBox(self.splitter)
        self.groupInput.setObjectName("groupInput")
        self.groupInput.setTitle("数据信息")
        self.groupInput.setMinimumWidth(200)
        self.inputLayout = QtWidgets.QVBoxLayout(self.groupInput)
        self.inputLayout.setObjectName("inputLayout")

        self.labelFile = QtWidgets.QLabel(self.groupInput)
        self.labelFile.setObjectName("labelFile")
        self.labelFile.setText("未加载数据")
        self.labelFile.setWordWrap(True)
        self.inputLayout.addWidget(self.labelFile)

        self.labelCount = QtWidgets.QLabel(self.groupInput)
        self.labelCount.setObjectName("labelCount")
        self.labelCount.setText("点云数量: -")
        self.inputLayout.addWidget(self.labelCount)

        self.labelStats = QtWidgets.QLabel(self.groupInput)
        self.labelStats.setObjectName("labelStats")
        self.labelStats.setText("坐标范围:\nx: - ~ -\ny: - ~ -\nz: - ~ -")
        self.labelStats.setWordWrap(True)
        self.inputLayout.addWidget(self.labelStats)

        self.labelGrid = QtWidgets.QLabel(self.groupInput)
        self.labelGrid.setObjectName("labelGrid")
        self.labelGrid.setText("栅格信息: -")
        self.labelGrid.setWordWrap(True)
        self.inputLayout.addWidget(self.labelGrid)

        self.labelPlane = QtWidgets.QLabel(self.groupInput)
        self.labelPlane.setObjectName("labelPlane")
        self.labelPlane.setText("分割平面: 待计算")
        self.labelPlane.setWordWrap(True)
        self.inputLayout.addWidget(self.labelPlane)

        self.inputLayout.addStretch()

        # ── 右：结果表格 ────────────────────────────────────────
        self.rightPanel = QtWidgets.QWidget(self.splitter)
        self.rightPanel.setObjectName("rightPanel")
        self.rightLayout = QtWidgets.QVBoxLayout(self.rightPanel)
        self.rightLayout.setObjectName("rightLayout")

        self.tableResult = QtWidgets.QTableWidget(self.rightPanel)
        self.tableResult.setObjectName("tableResult")
        self.rightLayout.addWidget(self.tableResult)

        # ── 装配布局 ──────────────────────────────────────────
        self.splitter.setSizes([250, 810])
        self.mainLayout.addWidget(self.splitter)
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

        self.menuFile.addAction(self.actionOpen)
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
        self.toolbar.addAction(self.actionOpen)
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
        MainWindow.setWindowTitle(_translate("MainWindow", "激光点云数据的平面分割"))
        self.groupInput.setTitle(_translate("MainWindow", "数据信息"))
        self.menuFile.setTitle(_translate("MainWindow", "文件(&F)"))
        self.menuCalc.setTitle(_translate("MainWindow", "计算(&C)"))
        self.actionOpen.setText(_translate("MainWindow", "打开(&O)"))
        self.actionCalc.setText(_translate("MainWindow", "计算(&C)"))
        self.actionSave.setText(_translate("MainWindow", "保存(&S)"))
        self.actionClear.setText(_translate("MainWindow", "清除(&R)"))
        self.actionExit.setText(_translate("MainWindow", "退出(&X)"))
        self.toolbar.setWindowTitle(_translate("MainWindow", "工具栏"))
