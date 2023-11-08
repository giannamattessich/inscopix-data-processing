import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout
from src.frontend.TimeseriesTab import TimeseriesTab
from src.frontend.LongitudinalTab import LongitudinalTab
from PyQt5.QtCore import QTimer, Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Processing')
        self.tabs = QTabWidget()
        self.tab1 = TimeseriesTab()
        self.tab2 = LongitudinalTab()
        self.setStyleSheet('background-color:#91899c')

        self.tabs.addTab(self.tab1, 'Timeseries')
        self.tabs.addTab(self.tab2, 'Longitudinal Registration')
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.tabs.setLayout(layout)
        self.setCentralWidget(self.tabs)


        self.tabs.currentChanged.connect(self.on_tab_change)
        self.resize(1920, 1080)
        timer = QTimer(self)
        # open timeseries message after window pop up with slight delay
        timer.singleShot(0, self.show_open_message)
        
    def on_tab_change(self, index):
        if index == 0:
            self.tab1.show_complete_dialog('Hello! Please begin by selecting an input folder that contains the raw recording/dropped frame recording files in year-month-day-hour-minute-hour-second format and an output folder name where processed files will go. Do not include already processed files in input directory.')
        elif index == 1:
            self.tab2.show_complete_dialog('Welcome! To start please input a folder that contains the output of timeseries processing, including motion corrected and CNMFe files.')

    def show_open_message(self):
        self.tab1.show_complete_dialog('Hello! Please begin by selecting an input folder that contains the raw recording/dropped frame recording files in year-month-day-hour-minute-hour-second format and an output folder name where processed files will go. Do not include already processed files in input directory.')
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())