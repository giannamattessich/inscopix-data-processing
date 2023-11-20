import sys
sys.path.append(r"C:\Users\Gianna\Documents\Python Scripts\time_series_and_LR_processing")
from src.frontend.UIMain import MainWindow
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())