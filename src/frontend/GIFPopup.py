from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt

# QDialog subclass to show GIFS as progress bar
class GIFPopup(QDialog):
    def __init__(self, gif_path, parent=None):
        super(GIFPopup, self).__init__(parent)
        self.setAutoFillBackground(True)
        self.playing = True
        self.movie = QMovie(gif_path)
        self.label = QLabel()
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMovie(self.movie)
        self.setWindowTitle('Processing...')
        self.movie.start()
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)

    def close_dialog(self):
        self.reject()