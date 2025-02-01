import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QPushButton, QHBoxLayout,
    QDialog, QLineEdit, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QFileSystemModel

class ExplorerSidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_directory = ""
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(""))
        self.tree.doubleClicked.connect(self.open_file_from_explorer)
        layout.addWidget(self.tree)

        buttonLayout = QHBoxLayout()
        newFileButton = QPushButton("New File")
        newFileButton.clicked.connect(self.create_new_file)
        newFolderButton = QPushButton("New Folder")
        newFolderButton.clicked.connect(self.create_new_folder)
        buttonLayout.addWidget(newFileButton)
        buttonLayout.addWidget(newFolderButton)
        layout.addLayout(buttonLayout)

        selectDirButton = QPushButton("Select Directory")
        selectDirButton.clicked.connect(self.select_directory)
        layout.addWidget(selectDirButton)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.current_directory = directory
            self.tree.setRootIndex(self.model.index(directory))

    def open_file_from_explorer(self, index):
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            editor = self.parent.get_current_editor()
            with open(file_path, "r") as file:
                editor.setPlainText(file.read())
            editor.file_path = file_path
            self.parent.tabWidget.setTabText(self.parent.tabWidget.currentIndex(), os.path.basename(file_path))

    def create_new_file(self):
        if not self.current_directory:
            QMessageBox.warning(self, "Error", "Please select a directory first!")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("New File")
        dialogLayout = QVBoxLayout()
        dialog.setLayout(dialogLayout)

        fileNameInput = QLineEdit()
        fileNameInput.setPlaceholderText("Enter file name (e.g., example.c)")
        dialogLayout.addWidget(fileNameInput)

        createButton = QPushButton("Create")
        createButton.clicked.connect(lambda: self.create_file(fileNameInput.text(), self.current_directory, dialog))
        dialogLayout.addWidget(createButton)

        dialog.exec()

    def create_file(self, file_name, directory, dialog):
        if not file_name:
            QMessageBox.warning(self, "Error", "File name cannot be empty!")
            return

        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "File already exists!")
            return

        with open(file_path, "w") as file:
            file.write("")
        dialog.close()
        self.tree.setRootIndex(self.model.index(directory))

        editor = self.parent.get_current_editor()
        editor.file_path = file_path
        self.parent.tabWidget.setTabText(self.parent.tabWidget.currentIndex(), os.path.basename(file_path))

    def create_new_folder(self):
        if not self.current_directory:
            QMessageBox.warning(self, "Error", "Please select a directory first!")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("New Folder")
        dialogLayout = QVBoxLayout()
        dialog.setLayout(dialogLayout)

        folderNameInput = QLineEdit()
        folderNameInput.setPlaceholderText("Enter folder name")
        dialogLayout.addWidget(folderNameInput)

        createButton = QPushButton("Create")
        createButton.clicked.connect(lambda: self.create_folder(folderNameInput.text(), self.current_directory, dialog))
        dialogLayout.addWidget(createButton)

        dialog.exec()

    def create_folder(self, folder_name, directory, dialog):
        if not folder_name:
            QMessageBox.warning(self, "Error", "Folder name cannot be empty!")
            return

        folder_path = os.path.join(directory, folder_name)
        if os.path.exists(folder_path):
            QMessageBox.warning(self, "Error", "Folder already exists!")
            return

        os.mkdir(folder_path)
        dialog.close()
        self.tree.setRootIndex(self.model.index(directory))