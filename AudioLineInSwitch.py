from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
import sys
import AudioIn as audio

class PushButton(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'LineIn Audio'
        self.width = 200
        self.height = 140
        self.left = 10
        self.top = 10
        self.initUI()
        self.audio_on = False
        self.myaudio = audio.AudioIn()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.button = QPushButton('OFF', self)
        self.button.setToolTip('Turn Line-In On / Off')
        self.button.setStyleSheet("background-color: lightgrey")
        self.button.move(10, 20)
        self.button.setMinimumHeight(100)
        self.button.setMinimumWidth(180)
        self.button.clicked.connect(self.on_click)

        self.show()

    @pyqtSlot()
    def on_click(self):
        if not self.audio_on:
            self.myaudio.start_stream()
            print('Line-In is ON')
            self.audio_on = True
            self.button.setText('ON')
            self.button.setStyleSheet ("background-color: darkgrey")
        else:
            self.myaudio.stop_stream()
            print('Line-In is OFF')
            self.audio_on = False
            self.button.setText('OFF')
            self.button.setStyleSheet ("background-color: lightgrey")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    button = PushButton()
    sys.exit(app.exec_())
