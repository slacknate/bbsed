# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bbsed\ui\main_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(1228, 853)
        self.central_widget = QtWidgets.QWidget(MainWindow)
        self.central_widget.setObjectName("central_widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.central_widget)
        self.verticalLayout.setObjectName("verticalLayout")
        MainWindow.setCentralWidget(self.central_widget)
        self.menu_bar = QtWidgets.QMenuBar(MainWindow)
        self.menu_bar.setEnabled(True)
        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 1228, 21))
        self.menu_bar.setObjectName("menu_bar")
        self.file_menu = QtWidgets.QMenu(self.menu_bar)
        self.file_menu.setEnabled(True)
        self.file_menu.setObjectName("file_menu")
        self.view_menu = QtWidgets.QMenu(self.menu_bar)
        self.view_menu.setEnabled(True)
        self.view_menu.setObjectName("view_menu")
        self.palettes_menu = QtWidgets.QMenu(self.menu_bar)
        self.palettes_menu.setEnabled(True)
        self.palettes_menu.setObjectName("palettes_menu")
        self.game_files_menu = QtWidgets.QMenu(self.menu_bar)
        self.game_files_menu.setEnabled(True)
        self.game_files_menu.setObjectName("game_files_menu")
        self.help_menu = QtWidgets.QMenu(self.menu_bar)
        self.help_menu.setObjectName("help_menu")
        self.edit_menu = QtWidgets.QMenu(self.menu_bar)
        self.edit_menu.setObjectName("edit_menu")
        MainWindow.setMenuBar(self.menu_bar)
        self.toolbar = QtWidgets.QToolBar(MainWindow)
        self.toolbar.setEnabled(True)
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.toolbar.setObjectName("toolbar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        self.exit = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/images/exit.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.exit.setIcon(icon)
        self.exit.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.exit.setObjectName("exit")
        self.apply_palettes = QtWidgets.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/images/images/apply.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.apply_palettes.setIcon(icon1)
        self.apply_palettes.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.apply_palettes.setObjectName("apply_palettes")
        self.discard_palette = QtWidgets.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/images/images/cancel.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.discard_palette.setIcon(icon2)
        self.discard_palette.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.discard_palette.setObjectName("discard_palette")
        self.restore_all = QtWidgets.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/images/images/undo.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.restore_all.setIcon(icon3)
        self.restore_all.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.restore_all.setObjectName("restore_all")
        self.restore_character = QtWidgets.QAction(MainWindow)
        self.restore_character.setIcon(icon3)
        self.restore_character.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.restore_character.setObjectName("restore_character")
        self.launch_bbcf = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/images/images/launch.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.launch_bbcf.setIcon(icon4)
        self.launch_bbcf.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.launch_bbcf.setObjectName("launch_bbcf")
        self.view_palette = QtWidgets.QAction(MainWindow)
        self.view_palette.setCheckable(True)
        self.view_palette.setChecked(False)
        self.view_palette.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.view_palette.setObjectName("view_palette")
        self.view_zoom = QtWidgets.QAction(MainWindow)
        self.view_zoom.setCheckable(True)
        self.view_zoom.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.view_zoom.setObjectName("view_zoom")
        self.import_palettes = QtWidgets.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/images/images/import.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.import_palettes.setIcon(icon5)
        self.import_palettes.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.import_palettes.setObjectName("import_palettes")
        self.export_palettes = QtWidgets.QAction(MainWindow)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/images/images/export.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.export_palettes.setIcon(icon6)
        self.export_palettes.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.export_palettes.setObjectName("export_palettes")
        self.settings = QtWidgets.QAction(MainWindow)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/images/images/settings.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.settings.setIcon(icon7)
        self.settings.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.settings.setObjectName("settings")
        self.copy_palette = QtWidgets.QAction(MainWindow)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/images/images/copy.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.copy_palette.setIcon(icon8)
        self.copy_palette.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.copy_palette.setObjectName("copy_palette")
        self.paste_palette = QtWidgets.QAction(MainWindow)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(":/images/images/paste.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.paste_palette.setIcon(icon9)
        self.paste_palette.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.paste_palette.setObjectName("paste_palette")
        self.save_palette = QtWidgets.QAction(MainWindow)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/images/images/save.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.save_palette.setIcon(icon10)
        self.save_palette.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.save_palette.setObjectName("save_palette")
        self.delete_palette = QtWidgets.QAction(MainWindow)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(":/images/images/delete.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.delete_palette.setIcon(icon11)
        self.delete_palette.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.delete_palette.setObjectName("delete_palette")
        self.save_palette_as = QtWidgets.QAction(MainWindow)
        self.save_palette_as.setIcon(icon10)
        self.save_palette_as.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.save_palette_as.setObjectName("save_palette_as")
        self.tutorial = QtWidgets.QAction(MainWindow)
        icon12 = QtGui.QIcon()
        icon12.addPixmap(QtGui.QPixmap(":/images/images/info.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tutorial.setIcon(icon12)
        self.tutorial.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.tutorial.setObjectName("tutorial")
        self.about = QtWidgets.QAction(MainWindow)
        icon13 = QtGui.QIcon()
        icon13.addPixmap(QtGui.QPixmap(":/images/images/question.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.about.setIcon(icon13)
        self.about.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.about.setObjectName("about")
        self.cut_color = QtWidgets.QAction(MainWindow)
        icon14 = QtGui.QIcon()
        icon14.addPixmap(QtGui.QPixmap(":/images/images/cut.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.cut_color.setIcon(icon14)
        self.cut_color.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.cut_color.setObjectName("cut_color")
        self.copy_color = QtWidgets.QAction(MainWindow)
        self.copy_color.setIcon(icon8)
        self.copy_color.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.copy_color.setObjectName("copy_color")
        self.paste_color = QtWidgets.QAction(MainWindow)
        self.paste_color.setIcon(icon9)
        self.paste_color.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.paste_color.setObjectName("paste_color")
        self.fill_color = QtWidgets.QAction(MainWindow)
        icon15 = QtGui.QIcon()
        icon15.addPixmap(QtGui.QPixmap(":/images/images/fill.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.fill_color.setIcon(icon15)
        self.fill_color.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.fill_color.setObjectName("fill_color")
        self.swap_color = QtWidgets.QAction(MainWindow)
        icon16 = QtGui.QIcon()
        icon16.addPixmap(QtGui.QPixmap(":/images/images/swap.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.swap_color.setIcon(icon16)
        self.swap_color.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.swap_color.setObjectName("swap_color")
        self.gradient_color = QtWidgets.QAction(MainWindow)
        icon17 = QtGui.QIcon()
        icon17.addPixmap(QtGui.QPixmap(":/images/images/gradient.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.gradient_color.setIcon(icon17)
        self.gradient_color.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        self.gradient_color.setObjectName("gradient_color")
        self.file_menu.addAction(self.launch_bbcf)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.settings)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit)
        self.view_menu.addAction(self.view_palette)
        self.view_menu.addAction(self.view_zoom)
        self.palettes_menu.addAction(self.import_palettes)
        self.palettes_menu.addAction(self.export_palettes)
        self.palettes_menu.addSeparator()
        self.palettes_menu.addAction(self.save_palette)
        self.palettes_menu.addAction(self.save_palette_as)
        self.palettes_menu.addAction(self.delete_palette)
        self.palettes_menu.addSeparator()
        self.palettes_menu.addAction(self.copy_palette)
        self.palettes_menu.addAction(self.paste_palette)
        self.palettes_menu.addSeparator()
        self.palettes_menu.addAction(self.discard_palette)
        self.game_files_menu.addAction(self.apply_palettes)
        self.game_files_menu.addSeparator()
        self.game_files_menu.addAction(self.restore_all)
        self.game_files_menu.addAction(self.restore_character)
        self.help_menu.addAction(self.tutorial)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about)
        self.edit_menu.addAction(self.cut_color)
        self.edit_menu.addAction(self.copy_color)
        self.edit_menu.addAction(self.paste_color)
        self.edit_menu.addAction(self.fill_color)
        self.edit_menu.addAction(self.swap_color)
        self.edit_menu.addAction(self.gradient_color)
        self.menu_bar.addAction(self.file_menu.menuAction())
        self.menu_bar.addAction(self.edit_menu.menuAction())
        self.menu_bar.addAction(self.game_files_menu.menuAction())
        self.menu_bar.addAction(self.palettes_menu.menuAction())
        self.menu_bar.addAction(self.view_menu.menuAction())
        self.menu_bar.addAction(self.help_menu.menuAction())
        self.toolbar.addAction(self.cut_color)
        self.toolbar.addAction(self.copy_color)
        self.toolbar.addAction(self.paste_color)
        self.toolbar.addAction(self.fill_color)
        self.toolbar.addAction(self.swap_color)
        self.toolbar.addAction(self.gradient_color)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.apply_palettes)
        self.toolbar.addAction(self.restore_all)
        self.toolbar.addAction(self.restore_character)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.import_palettes)
        self.toolbar.addAction(self.export_palettes)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.save_palette)
        self.toolbar.addAction(self.save_palette_as)
        self.toolbar.addAction(self.delete_palette)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.copy_palette)
        self.toolbar.addAction(self.paste_palette)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.discard_palette)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.file_menu.setTitle(_translate("MainWindow", "&File"))
        self.view_menu.setTitle(_translate("MainWindow", "&View"))
        self.palettes_menu.setTitle(_translate("MainWindow", "&Palettes"))
        self.game_files_menu.setTitle(_translate("MainWindow", "&Game Files"))
        self.help_menu.setTitle(_translate("MainWindow", "&Help"))
        self.edit_menu.setTitle(_translate("MainWindow", "&Edit"))
        self.toolbar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.exit.setText(_translate("MainWindow", "&Exit"))
        self.apply_palettes.setText(_translate("MainWindow", "&Apply Palettes"))
        self.apply_palettes.setToolTip(_translate("MainWindow", "Apply all palettes to BBCF game data"))
        self.apply_palettes.setShortcut(_translate("MainWindow", "Ctrl+A"))
        self.discard_palette.setText(_translate("MainWindow", "&Discard Changes"))
        self.discard_palette.setToolTip(_translate("MainWindow", "Discard selected palette changes"))
        self.discard_palette.setShortcut(_translate("MainWindow", "Ctrl+D"))
        self.restore_all.setText(_translate("MainWindow", "&Restore All"))
        self.restore_all.setToolTip(_translate("MainWindow", "Restore game data for all palettes"))
        self.restore_all.setShortcut(_translate("MainWindow", "Ctrl+R"))
        self.restore_character.setText(_translate("MainWindow", "Restore &Character"))
        self.restore_character.setToolTip(_translate("MainWindow", "Restore game data for selected character palettes"))
        self.restore_character.setShortcut(_translate("MainWindow", "Ctrl+M"))
        self.launch_bbcf.setText(_translate("MainWindow", "&Launch BBCF"))
        self.launch_bbcf.setToolTip(_translate("MainWindow", "Launch BBCF"))
        self.launch_bbcf.setShortcut(_translate("MainWindow", "Ctrl+L"))
        self.view_palette.setText(_translate("MainWindow", "&Palette Dialog"))
        self.view_palette.setShortcut(_translate("MainWindow", "Ctrl+B"))
        self.view_zoom.setText(_translate("MainWindow", "&Zoom Dialog"))
        self.view_zoom.setShortcut(_translate("MainWindow", "Ctrl+J"))
        self.import_palettes.setText(_translate("MainWindow", "&Import"))
        self.import_palettes.setShortcut(_translate("MainWindow", "Ctrl+I"))
        self.export_palettes.setText(_translate("MainWindow", "&Export"))
        self.export_palettes.setToolTip(_translate("MainWindow", "Export saved palettes"))
        self.export_palettes.setShortcut(_translate("MainWindow", "Ctrl+E"))
        self.settings.setText(_translate("MainWindow", "&Settings"))
        self.settings.setToolTip(_translate("MainWindow", "Edit settings"))
        self.settings.setShortcut(_translate("MainWindow", "Ctrl+T"))
        self.copy_palette.setText(_translate("MainWindow", "&Copy"))
        self.copy_palette.setToolTip(_translate("MainWindow", "Copy current palette"))
        self.copy_palette.setShortcut(_translate("MainWindow", "Ctrl+U"))
        self.paste_palette.setText(_translate("MainWindow", "&Paste"))
        self.paste_palette.setToolTip(_translate("MainWindow", "Paste copied palette"))
        self.paste_palette.setShortcut(_translate("MainWindow", "Ctrl+P"))
        self.save_palette.setText(_translate("MainWindow", "&Save"))
        self.save_palette.setToolTip(_translate("MainWindow", "Save current palette"))
        self.save_palette.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.delete_palette.setText(_translate("MainWindow", "D&elete"))
        self.delete_palette.setToolTip(_translate("MainWindow", "Delete selected saved palette"))
        self.delete_palette.setShortcut(_translate("MainWindow", "Ctrl+K"))
        self.save_palette_as.setText(_translate("MainWindow", "Save &As"))
        self.save_palette_as.setToolTip(_translate("MainWindow", "Save current palette as"))
        self.tutorial.setText(_translate("MainWindow", "&Tutorial"))
        self.tutorial.setToolTip(_translate("MainWindow", "Show tutorial dialog"))
        self.about.setText(_translate("MainWindow", "&About"))
        self.cut_color.setText(_translate("MainWindow", "C&ut"))
        self.cut_color.setToolTip(_translate("MainWindow", "Cut current selected color"))
        self.cut_color.setShortcut(_translate("MainWindow", "Ctrl+X"))
        self.copy_color.setText(_translate("MainWindow", "&Copy"))
        self.copy_color.setToolTip(_translate("MainWindow", "Copy current selected color"))
        self.copy_color.setShortcut(_translate("MainWindow", "Ctrl+C"))
        self.paste_color.setText(_translate("MainWindow", "&Paste"))
        self.paste_color.setToolTip(_translate("MainWindow", "Paste color"))
        self.paste_color.setShortcut(_translate("MainWindow", "Ctrl+V"))
        self.fill_color.setText(_translate("MainWindow", "&Fill"))
        self.fill_color.setToolTip(_translate("MainWindow", "Fill color selection"))
        self.fill_color.setShortcut(_translate("MainWindow", "Ctrl+F"))
        self.swap_color.setText(_translate("MainWindow", "&Swap"))
        self.swap_color.setToolTip(_translate("MainWindow", "Swap colors"))
        self.swap_color.setShortcut(_translate("MainWindow", "Ctrl+W"))
        self.gradient_color.setText(_translate("MainWindow", "&Gradient"))
        self.gradient_color.setToolTip(_translate("MainWindow", "Generate a color gradient"))
        self.gradient_color.setShortcut(_translate("MainWindow", "Ctrl+G"))
from bbsed.ui import resources_rc
