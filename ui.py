import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, QVBoxLayout,
    QWidget, QSplitter, QPlainTextEdit, QPushButton, QHBoxLayout, 
    QTabWidget, QTextBrowser, QToolBar, QLabel, QTreeView,
    QDialog, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter,QFileSystemModel
from PyQt6.QtCore import Qt, QRegularExpression, QDir, QTimer
import subprocess
import tempfile

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Courier", 12))
        self.setPlaceholderText("Write your C code here...")
        self.highlighter = SyntaxHighlighter(self.document())
        self.file_path = None 

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.highlightRules = []
        keywords = ["int", "return", "void", "main", "if", "else", "while", "for", "include"]
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#569CD6"))
        for keyword in keywords:
            pattern = QRegularExpression(f"\\b{keyword}\\b")
            self.highlightRules.append((pattern, keywordFormat))
    
    def highlightBlock(self, text):
        for pattern, fmt in self.highlightRules:
            matchIterator = pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

class ExplorerSidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_directory = "" 
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # File system tree view
        self.model = QFileSystemModel()
        self.model.setRootPath("")  
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index("")) 
        self.tree.doubleClicked.connect(self.open_file_from_explorer)
        layout.addWidget(self.tree)

        # Buttons for creating files and folders
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

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CODEBUDDY")
        self.setGeometry(100, 100, 1200, 800)
        self.initUI()
        self.initAutoSave()

    def initUI(self):
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QHBoxLayout()
        centralWidget.setLayout(layout)

        self.mainSplitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.mainSplitter)

        self.leftSidebar = QWidget()
        self.leftSidebarLayout = QVBoxLayout()
        self.leftSidebar.setLayout(self.leftSidebarLayout)

        self.explorer = ExplorerSidebar(self)
        self.leftSidebarLayout.addWidget(self.explorer)
        self.mainSplitter.addWidget(self.leftSidebar)  

        self.middleContent = QWidget()
        self.middleLayout = QVBoxLayout()
        self.middleContent.setLayout(self.middleLayout)

        self.tabWidget = QTabWidget()
        self.add_new_tab()
        self.middleLayout.addWidget(self.tabWidget, 4) 

        self.outputConsole = QTextEdit()
        self.outputConsole.setFont(QFont("Courier", 11))
        self.outputConsole.setReadOnly(True)
        self.outputConsole.setPlaceholderText("Compilation and execution output will appear here...")
        self.middleLayout.addWidget(self.outputConsole, 1)

        self.mainSplitter.addWidget(self.middleContent) 

        self.rightSidebar = QWidget()
        self.rightSidebarLayout = QVBoxLayout()
        self.rightSidebar.setLayout(self.rightSidebarLayout)

        self.aiPanel = QTextBrowser()
        self.aiPanel.setFont(QFont("Arial", 11))
        self.aiPanel.setText("💡 AI Code Assistant: Ask for help, explanations, and suggestions here.")
        self.aiPanel.setReadOnly(True)
        self.rightSidebarLayout.addWidget(self.aiPanel)
        self.mainSplitter.addWidget(self.rightSidebar)  

        self.mainSplitter.setSizes([200, 600, 200])

        self.initToolBar()

    def initAutoSave(self):
        self.autoSaveTimer = QTimer(self)
        self.autoSaveTimer.timeout.connect(self.autoSave)
        self.autoSaveTimer.start(5000)  

    def autoSave(self):
        editor = self.get_current_editor()
        if editor and editor.file_path:
            with open(editor.file_path, "w") as file:
                file.write(editor.toPlainText())

    def initToolBar(self):
        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)

        runButton = QPushButton("Run")
        runButton.clicked.connect(self.compile_and_run)
        toolbar.addWidget(runButton)

        clearButton = QPushButton("Clear Output")
        clearButton.clicked.connect(self.clear_output)
        toolbar.addWidget(clearButton)

        openButton = QPushButton("Open")
        openButton.clicked.connect(self.open_file)
        toolbar.addWidget(openButton)

        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.save_file)
        toolbar.addWidget(saveButton)

        newTabButton = QPushButton("New Tab")
        newTabButton.clicked.connect(self.add_new_tab)
        toolbar.addWidget(newTabButton)

    def add_new_tab(self):
        editor = CodeEditor()
        self.tabWidget.addTab(editor, "Untitled.c")

    def get_current_editor(self):
        return self.tabWidget.currentWidget()

    def open_file(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open C File", "", "C Files (*.c)")
        if fileName:
            editor = self.get_current_editor()
            with open(fileName, "r") as file:
                editor.setPlainText(file.read())
            editor.file_path = fileName  
            self.tabWidget.setTabText(self.tabWidget.currentIndex(), os.path.basename(fileName))

    def save_file(self):
        editor = self.get_current_editor()
        if not editor:
            return

        if editor.file_path:
            with open(editor.file_path, "w") as file:
                file.write(editor.toPlainText())
        else:
            fileName, _ = QFileDialog.getSaveFileName(self, "Save C File", "", "C Files (*.c)")
            if fileName:
                with open(fileName, "w") as file:
                    file.write(editor.toPlainText())
                editor.file_path = fileName 
                self.tabWidget.setTabText(self.tabWidget.currentIndex(), os.path.basename(fileName))

    def clear_output(self):
        self.outputConsole.clear()

    def compile_and_run(self):
        editor = self.get_current_editor()
        if not editor:
            return

        code = editor.toPlainText()
        if not code.strip():
            self.outputConsole.setText("⚠️ No code to compile!")
            return

        with tempfile.TemporaryDirectory() as tempdir:
            output_file = os.path.join(tempdir, 'temp.out')
            compileCommand = ['gcc', '-x', 'c', '-', '-o', output_file]

            try:
                compileProcess = subprocess.Popen(
                    compileCommand, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                compileStdout, compileStderr = compileProcess.communicate(input=code.encode('utf-8'))
                if compileProcess.returncode != 0:
                    self.outputConsole.setText(f"❌ Compilation Error:\n\n{compileStderr.decode()}")
                    return

                runProcess = subprocess.Popen(
                    output_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

                executionStdout, executionStderr = runProcess.communicate()

                if executionStderr:
                    self.outputConsole.setText(f"❌ Execution Error:\n\n{executionStderr.decode()}")
                else:
                    self.outputConsole.setText(f"✅ Output:\n\n{executionStdout.decode()}")

            except Exception as e:
                self.outputConsole.setText(f"⚠️ Error occurred: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = IDE()
    ide.show()
    sys.exit(app.exec())