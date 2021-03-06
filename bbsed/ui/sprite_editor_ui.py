# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bbsed\ui\sprite_editor.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Editor(object):
    def setupUi(self, Editor):
        Editor.setObjectName("Editor")
        Editor.resize(886, 627)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Editor.sizePolicy().hasHeightForWidth())
        Editor.setSizePolicy(sizePolicy)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Editor)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(4)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.sprite_search = QtWidgets.QLineEdit(Editor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sprite_search.sizePolicy().hasHeightForWidth())
        self.sprite_search.setSizePolicy(sizePolicy)
        self.sprite_search.setMaximumSize(QtCore.QSize(256, 16777215))
        self.sprite_search.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.sprite_search.setObjectName("sprite_search")
        self.horizontalLayout_3.addWidget(self.sprite_search)
        self.clear_search_button = QtWidgets.QPushButton(Editor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.clear_search_button.sizePolicy().hasHeightForWidth())
        self.clear_search_button.setSizePolicy(sizePolicy)
        self.clear_search_button.setMaximumSize(QtCore.QSize(38, 16777215))
        self.clear_search_button.setObjectName("clear_search_button")
        self.horizontalLayout_3.addWidget(self.clear_search_button)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.collapse_all_button = QtWidgets.QPushButton(Editor)
        self.collapse_all_button.setObjectName("collapse_all_button")
        self.horizontalLayout_2.addWidget(self.collapse_all_button)
        self.expand_all_button = QtWidgets.QPushButton(Editor)
        self.expand_all_button.setObjectName("expand_all_button")
        self.horizontalLayout_2.addWidget(self.expand_all_button)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.sprite_list = QtWidgets.QTreeView(Editor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sprite_list.sizePolicy().hasHeightForWidth())
        self.sprite_list.setSizePolicy(sizePolicy)
        self.sprite_list.setMaximumSize(QtCore.QSize(256, 16777215))
        self.sprite_list.setObjectName("sprite_list")
        self.sprite_list.header().setVisible(False)
        self.sprite_list.header().setDefaultSectionSize(0)
        self.verticalLayout.addWidget(self.sprite_list)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.sprite_preview = QtWidgets.QGraphicsView(Editor)
        self.sprite_preview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.sprite_preview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.sprite_preview.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.sprite_preview.setObjectName("sprite_preview")
        self.horizontalLayout.addWidget(self.sprite_preview)
        self.show_animation_info = QtWidgets.QAction(Editor)
        self.show_animation_info.setObjectName("show_animation_info")

        self.retranslateUi(Editor)
        QtCore.QMetaObject.connectSlotsByName(Editor)

    def retranslateUi(self, Editor):
        _translate = QtCore.QCoreApplication.translate
        Editor.setWindowTitle(_translate("Editor", "Form"))
        self.sprite_search.setPlaceholderText(_translate("Editor", "Search..."))
        self.clear_search_button.setText(_translate("Editor", "Clear"))
        self.collapse_all_button.setText(_translate("Editor", "Collapse All"))
        self.expand_all_button.setText(_translate("Editor", "Expand All"))
        self.show_animation_info.setText(_translate("Editor", "View Animation Details"))
        self.show_animation_info.setToolTip(_translate("Editor", "View animation game information"))
