import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit,
    QTextBrowser, QToolBar, QPushButton, QSplitter, QFileDialog, QMessageBox,QComboBox, QLabel, QFrame,QMenu
)
from PyQt6.QtGui import QFont,QCursor,QAction
from PyQt6.QtCore import Qt, QTimer
from editor import CodeEditor
from explorer_sidebar import ExplorerSidebar
from main import CodeBuddyConsole
from compile_run import CompileRun
from ai_assistant import AIAssistantHandler
class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CODEBUDDY")
        self.setGeometry(100, 100, 1200, 800)

        self.ai_assistant = AIAssistantHandler(self) 

        self.initUI()
        self.initAutoSave()

        self.code_buddy = CodeBuddyConsole()
        self.compile_run = CompileRun(self.outputConsole)


    def initUI(self):
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QHBoxLayout()
        centralWidget.setLayout(layout)

        self.mainSplitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.mainSplitter)

        # Left Sidebar (Explorer)
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

        self.rightControls = QFrame()
        self.rightControlsLayout = QVBoxLayout()
        self.rightControls.setLayout(self.rightControlsLayout)

        self.languageSelector = QComboBox()
        # self.languageSelector.addItems(["C", "C++", "Java", "Python"])
        self.languageSelector.addItems(["C"])
        self.rightControlsLayout.addWidget(QLabel("Language:"))
        self.rightControlsLayout.addWidget(self.languageSelector)

        self.assistantSelector = QComboBox()
        self.assistantSelector.addItems([
            "General Assistant", "Code Correction", "Code Completion", "Code Optimization",
            "Code Generation", "Code Commenting", "Code Explanation", "LeetCode Solver", "Code Shortener"
        ])
        self.rightControlsLayout.addWidget(QLabel("Assistant:"))
        self.rightControlsLayout.addWidget(self.assistantSelector)

        self.assistButton = QPushButton("Assist")
        self.assistButton.clicked.connect(self.ai_assistant.assist_code)
        self.rightControlsLayout.addWidget(self.assistButton)

        self.rightSidebarLayout.addWidget(self.rightControls)

        self.aiPanel = QTextEdit()
        self.aiPanel.setFont(QFont("Arial", 11))
        self.aiPanel.setPlaceholderText("💡 AI Code Assistant: Write your prompt here...")
        self.rightSidebarLayout.addWidget(self.aiPanel)
        
        self.aiPanel.mouseReleaseEvent = self.showSelectionMenu

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
        runButton.clicked.connect(self.run_code)  
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
    
    def run_code(self):
        editor = self.get_current_editor()
        if not editor:
            return

        code = editor.toPlainText()
        language = self.languageSelector.currentText().lower()
        self.compile_run.compile_and_run(code, language)

    def open_file(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
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
            fileName, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*)")
            if fileName:
                with open(fileName, "w") as file:
                    file.write(editor.toPlainText())
                editor.file_path = fileName
                self.tabWidget.setTabText(self.tabWidget.currentIndex(), os.path.basename(fileName))

    def clear_output(self):
        self.outputConsole.clear()
        
    def showSelectionMenu(self, event):
        if self.aiPanel.textCursor().hasSelection():
            menu = QMenu(self)

            copyAction = QAction("Copy", self)
            cutAction = QAction("Cut", self)
            pasteAction = QAction("Paste", self)
            deleteAction = QAction("Delete", self)

            copyAction.triggered.connect(self.aiPanel.copy)
            cutAction.triggered.connect(self.aiPanel.cut)
            pasteAction.triggered.connect(self.aiPanel.paste)
            deleteAction.triggered.connect(self.aiPanel.delete)

            menu.addAction(copyAction)
            menu.addAction(cutAction)
            menu.addAction(pasteAction)
            menu.addAction(deleteAction)

            menu.exec(QCursor.pos())

        QTextEdit.mouseReleaseEvent(self.aiPanel, event)