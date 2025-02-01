import os
import tempfile
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit,
    QTextBrowser, QToolBar, QPushButton, QSplitter, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
from editor import CodeEditor
from explorer_sidebar import ExplorerSidebar

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