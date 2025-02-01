import sys
from PyQt6.QtWidgets import QApplication
from ide import IDE

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = IDE()
    ide.show()
    sys.exit(app.exec())