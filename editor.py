from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter
from PyQt6.QtCore import QRegularExpression

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