import sys
from PyQt5.QtWidgets import QApplication
from ui import TimerApp

def main():
    app = QApplication(sys.argv)
    window = TimerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()