from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtGui import (
    QFont, QTextCharFormat, QColor, QSyntaxHighlighter,
    QPainter, QTextFormat, QTextCursor
)
from PyQt6.QtCore import Qt, QRect, QRegularExpression, QSize

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Fira Code", 12))
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.file_path = None
        
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth(0)
        
        self.highlighter = SyntaxHighlighter(self.document())
        
        self.bracketFormat = QTextCharFormat()
        self.bracketFormat.setBackground(QColor(100, 100, 100, 50))
        self.bracketPositions = []
        
        self.cursorPositionChanged.connect(self.highlightBrackets)
        
        self.currentTheme = "dark"
        self.applyTheme(self.currentTheme)

    def applyTheme(self, theme_name):
        themes = {
            "dark": {
                "background": "#1e1e1e",
                "foreground": "#d4d4d4",
                "current_line": "#2d2d2d",
                "line_numbers": "#858585",
                "keywords": "#569cd6",
                "functions": "#dcdcaa",
                "comments": "#6a9955",
                "strings": "#ce9178",
                "numbers": "#b5cea8",
                "preprocessor": "#9b9b9b"
            },
            "light": {
                "background": "#ffffff",
                "foreground": "#000000",
                "current_line": "#efefef",
                "line_numbers": "#666666",
                "keywords": "#0000ff",
                "functions": "#795e26",
                "comments": "#008000",
                "strings": "#a31515",
                "numbers": "#098658",
                "preprocessor": "#267f99"
            }
        }
        theme = themes[theme_name]
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {theme['background']};
                color: {theme['foreground']};
            }}
        """)
        self.lineNumberArea.setStyleSheet(f"""
            background-color: {theme['background']};
            color: {theme['line_numbers']};
        """)
        self.highlighter.setTheme(theme)
        self.highlighter.rehighlight()

    def lineNumberAreaWidth(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num /= 10
            digits += 1
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightBrackets(self):
        cursor = self.textCursor()
        if cursor.positionInBlock() < 0:
            return

        text = cursor.block().text()
        pos = cursor.positionInBlock()
        bracket = text[pos] if pos < len(text) else ''
        matching = {'(': ')', '[': ']', '{': '}', ')': '(', ']': '[', '}': '{'}

        if bracket in matching:
            match = self.findMatchingBracket(cursor.block(), pos, bracket, matching[bracket])
            if match:
                self.bracketPositions = [cursor.position(), match.position()]
                return
        self.bracketPositions = []

    def findMatchingBracket(self, block, pos, openBracket, closeBracket):
        stack = []
        text = block.text()
        for i in range(pos, len(text)):
            char = text[i]
            if char == openBracket:
                stack.append(char)
            elif char == closeBracket:
                if stack and stack[-1] == openBracket:
                    stack.pop()
                    if not stack:
                        return QTextCursor(block).position() + i
                else:
                    return None
        return None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            current_line = cursor.block().text()
            indent = len(current_line) - len(current_line.lstrip())
            super().keyPressEvent(event)
            self.insertPlainText(' ' * indent)
        else:
            super().keyPressEvent(event)
    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(self.currentTheme == "dark" and "#1e1e1e" or "#ffffff"))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(self.currentTheme == "dark" and "#858585" or "#666666"))
                painter.drawText(0, top, self.lineNumberArea.width(), self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.theme = {}
        self.rules = []
        
        self.initializeRules()

    def setTheme(self, theme):
        self.theme = theme
        self.initializeRules()

    def initializeRules(self):
        self.rules = []
        
        keywords = [
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default',
            'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto',
            'if', 'int', 'long', 'register', 'return', 'short', 'signed',
            'sizeof', 'static', 'struct', 'switch', 'typedef', 'union',
            'unsigned', 'void', 'volatile', 'while'
        ]
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(self.theme.get('keywords', '#569cd6')))
        self.rules += [(QRegularExpression(fr'\b{kw}\b'), keywordFormat) for kw in keywords]

        functionFormat = QTextCharFormat()
        functionFormat.setForeground(QColor(self.theme.get('functions', '#dcdcaa')))
        self.rules.append((
            QRegularExpression(r'\b[A-Za-z0-9_]+(?=\()'), 
            functionFormat
        ))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(self.theme.get('comments', '#6a9955')))
        self.rules.append((
            QRegularExpression(r'//[^\n]*'), 
            commentFormat
        ))
        self.multiLineCommentFormat = commentFormat

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(self.theme.get('strings', '#ce9178')))
        self.rules.append((
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), 
            stringFormat
        ))

        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(self.theme.get('numbers', '#b5cea8')))
        self.rules.append((
            QRegularExpression(r'\b\d+(\.\d+)?([eE][+-]?\d+)?[fFlL]?\b'), 
            numberFormat
        ))

        preprocessorFormat = QTextCharFormat()
        preprocessorFormat.setForeground(QColor(self.theme.get('preprocessor', '#9b9b9b')))
        self.rules.append((
            QRegularExpression(r'^#.*'), 
            preprocessorFormat
        ))

        self.commentStart = QRegularExpression(r'/\*')
        self.commentEnd = QRegularExpression(r'\*/')

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        self.setCurrentBlockState(0)
        start = 0
        if self.previousBlockState() != 1:
            start = self.commentStart.match(text).capturedStart()

        while start >= 0:
            endMatch = self.commentEnd.match(text, start)
            end = endMatch.capturedStart()
            if end == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - start
            else:
                commentLength = end - start + endMatch.capturedLength()
            self.setFormat(start, commentLength, self.multiLineCommentFormat)
            start = self.commentStart.match(text, start + commentLength).capturedStart()
            
