import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, QVBoxLayout,
    QWidget, QSplitter, QPlainTextEdit, QPushButton, QHBoxLayout, 
    QTabWidget, QTextBrowser, QToolBar, QLabel
)
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter
from PyQt6.QtCore import Qt, QRegularExpression

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Courier", 12))
        self.setPlaceholderText("Write your C code here...")
        self.highlighter = SyntaxHighlighter(self.document())
        
class SyntaxHighlighter(QSyntaxHighlighter):
    # Basic syntax highlighting for C 
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

class IDE(QMainWindow):
    # Main IDE Window with VS Code-like styling and AI panel 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VS Code Style C IDE")
        self.setGeometry(100, 100, 1200, 800)
        self.initUI()

    def initUI(self):
        # Setup UI with split panels 
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout()
        
        # Tabs
        self.tabWidget = QTabWidget()
        self.add_new_tab()
        
        # Console
        self.outputConsole = QTextEdit()
        self.outputConsole.setFont(QFont("Courier", 11))
        self.outputConsole.setReadOnly(True)
        self.outputConsole.setPlaceholderText("Compilation and execution output will appear here...")
        
        # AI Assistant
        self.aiPanel = QTextBrowser()
        self.aiPanel.setFont(QFont("Arial", 11))
        self.aiPanel.setText("💡 AI Code Assistant: Ask for help, explanations, and suggestions here.")
        self.aiPanel.setReadOnly(True)
        
        mainSplitter = QSplitter(Qt.Orientation.Horizontal)
        mainSplitter.addWidget(self.tabWidget) 
        mainSplitter.addWidget(self.aiPanel)  
        
        bottomSplitter = QSplitter(Qt.Orientation.Vertical)
        bottomSplitter.addWidget(mainSplitter)  
        bottomSplitter.addWidget(self.outputConsole)  
        
        layout.addWidget(bottomSplitter)
        
        self.initToolBar()
        centralWidget.setLayout(layout)

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
        # code editor 
        editor = CodeEditor()
        self.tabWidget.addTab(editor, "Untitled.c")

    def get_current_editor(self):
        # active editor 
        return self.tabWidget.currentWidget()
    
    def open_file(self):
        # Open a file into the editor 
        fileName, _ = QFileDialog.getOpenFileName(self, "Open C File", "", "C Files (*.c)")
        if fileName:
            with open(fileName, "r") as file:
                self.get_current_editor().setPlainText(file.read())
            self.tabWidget.setTabText(self.tabWidget.currentIndex(), os.path.basename(fileName))
    
    def save_file(self):
        # Save the current file 
        fileName, _ = QFileDialog.getSaveFileName(self, "Save C File", "", "C Files (*.c)")
        if fileName:
            with open(fileName, "w") as file:
                file.write(self.get_current_editor().toPlainText())
            self.tabWidget.setTabText(self.tabWidget.currentIndex(), os.path.basename(fileName))
    
    def clear_output(self):
        # Clear the output console 
        self.outputConsole.clear()
    
    def compile_and_run(self):
        # Compile and execute the C code
        editor = self.get_current_editor()
        if not editor:
            return
        
        code = editor.toPlainText()
        if not code.strip():
            self.outputConsole.setText("⚠️ No code to compile!")
            return
        
        tempFile = "temp.c"
        with open(tempFile, "w") as file:
            file.write(code)
        
        outputExe = "temp.exe" if os.name == "nt" else "./temp.out"
        compileCommand = f"gcc {tempFile} -o {outputExe} 2>&1"
        compileResult = os.popen(compileCommand).read()
        
        if compileResult:
            self.outputConsole.setText(f"❌ Compilation Error:\n\n{compileResult}")
            return
        
        executionResult = os.popen(outputExe).read()
        self.outputConsole.setText(f"✅ Output:\n\n{executionResult}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = IDE()
    ide.show()
    sys.exit(app.exec())
