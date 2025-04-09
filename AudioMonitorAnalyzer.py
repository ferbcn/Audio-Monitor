import sys
from AudioIn import AudioIn
import numpy as np

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QSlider
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

CHUNK = 1024


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.line1 = None
        self.bar1 = None
        self.peak_text = None
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)
        self.fig.set_facecolor('#595959')
        self.ax = self.fig.add_subplot(211)
        self.bx = self.fig.add_subplot(212)
        self.fig.tight_layout(h_pad=3)
        self.plot()

    def plot(self):
        self.ax.set(xlabel='Time [μs]', facecolor='#3a3a3a')
        self.ax.xaxis.label.set_fontsize('small')
        self.ax.set(facecolor='#3a3a3a')
        self.ax.set_title('Time Domain', color='#000000', size='medium')
        self.ax.tick_params(axis='both', which='major', labelsize=6, labelcolor='#000000')
        self.ax.set_ylim([-2000, 2000])
        self.ax.set_xlim([0, 500])
        x = np.arange(0, CHUNK, 1)
        y = [0 for x in range(CHUNK)]
        self.line1, = self.ax.plot(x, y, 'r-')

        self.bx.set(xlabel='Frequency [Hz]', facecolor='#3a3a3a')
        self.bx.xaxis.label.set_fontsize('small')
        self.bx.set(facecolor='#3a3a3a')
        self.bx.set_title('Frequency Domain', color='#000000', size='medium')
        self.bx.tick_params(axis='both', which='major', labelsize=6, labelcolor='#000000')
        self.bx.set_ylim([0, 1000])
        self.bx.set_xlim([10, 5000])

        x = np.arange(0, 10*CHUNK, 20)
        y = [0 for x in range(int(CHUNK/2))]
        self.bar1, = self.bx.plot(x, y, 'r-')
        
        self.peak_text = self.bx.text(0, 0, '', color='red', fontsize=8, ha='center', va='bottom')

    def update_plot(self, data):
        # update time plot
        self.line1.set_ydata(data)

        # update frequency plot
        # define spectrogram
        t = np.linspace(0, 1, len(data))
        s = data
        T = t[1] - t[0]  # sampling interval
        N = s.size
        fft = np.fft.fft(data)
        abs_data = np.abs(fft)
        bar_data = abs_data[:N // 2] * 1 / N
        
        # Create frequency array starting from 10 Hz
        freq = np.arange(0, len(bar_data)) * 20  # 20 Hz per bin
        mask = freq >= 10  # Only include frequencies >= 10 Hz
        bar_data = bar_data[mask]
        freq = freq[mask]
        
        # Get current slider range
        slider_min, slider_max = self.bx.get_xlim()
        
        # Find peak within slider range
        mask = (freq >= slider_min) & (freq <= slider_max)
        if np.any(mask):  # Only if there are frequencies in the range
            peak_idx = np.argmax(bar_data[mask])
            peak_freq = freq[mask][peak_idx]
            peak_amplitude = bar_data[mask][peak_idx]
            
            # Only show peak if amplitude is above threshold
            amplitude_threshold = 100
            if peak_amplitude > amplitude_threshold:
                self.peak_text.set_position((peak_freq, peak_amplitude + 50))
                self.peak_text.set_text(f'{peak_freq:.0f} Hz')
            else:
                self.peak_text.set_text('')  # Hide text if amplitude is too low
        else:
            self.peak_text.set_text('')  # Hide text if no peaks in range
        
        hz = freq[bar_data.argmax()]  # Get frequency of maximum amplitude
        self.bar1.set_xdata(freq)
        self.bar1.set_ydata(bar_data)

        # update figure
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        return hz


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.label = None
        self.hz_label = None
        self.sc = None
        self.button_on_out = None
        self.button_on = None
        self.title = 'Audio Input Monitor and Analyzer'
        self.setWindowTitle(self.title)

        self.width = 400
        self.height = 650
        self.left = 10
        self.top = 10

        self.monitor_on = False
        self.output_on = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.refresh_rate = 10

        self.my_audio = AudioIn()
        self.hz = 0
        self.input_device_id = None
        self.output_device_id = None
        self.init_ui()
        self.show()

    def init_ui(self):
        page_layout = QVBoxLayout()
        page_widget = QWidget()
        page_widget.setLayout(page_layout)

        self.setStyleSheet("background-color: #595959")
        self.setGeometry(self.left, self.top, self.width, self.height)

        button_layout = QHBoxLayout()
        self.button_on = QPushButton('MONITOR\nOFF', self)
        self.button_on.setToolTip('Turn Line-In/Mic  On / Off')
        self.button_on.setStyleSheet("background-color: #777777")
        self.button_on.setMinimumHeight(100)
        self.button_on.setMinimumWidth(100)
        self.button_on.setMaximumWidth(250)
        self.button_on.clicked.connect(self.on_click)
        button_layout.addWidget(self.button_on)

        self.button_on_out = QPushButton('OUTPUT\nOFF', self)
        self.button_on_out.setToolTip('Turn Audio Playback On / Off')
        self.button_on_out.setStyleSheet("background-color: #777777")
        self.button_on_out.setMinimumHeight(100)
        self.button_on_out.setMinimumWidth(100)
        self.button_on_out.setMaximumWidth(200)
        self.button_on_out.clicked.connect(self.on_click_out)
        button_layout.addWidget(self.button_on_out)

        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        button_widget.setFixedHeight(100)

        # Input and Output device selection layout
        device_layout = QHBoxLayout()
        
        # Input device selection
        input_layout = QVBoxLayout()
        input_label = QLabel("Input Device:")
        input_label.setStyleSheet("color: white")
        input_devices = self.my_audio.get_input_devices_info()
        self.input_device_id = self.my_audio.get_default_input_device().get('index')
        input_combo_box = QComboBox(self)
        input_combo_box.setMaximumWidth(200)
        for device in input_devices:
            input_combo_box.addItem(device.get('name'))
        input_combo_box.activated[str].connect(self.input_choice)
        input_layout.addWidget(input_label)
        input_layout.addWidget(input_combo_box)
        
        # Output device selection
        output_layout = QVBoxLayout()
        output_label = QLabel("Output Device:")
        output_label.setStyleSheet("color: white")
        output_devices = self.my_audio.get_output_devices_info()
        self.output_device_id = self.my_audio.get_default_output_device().get('index')
        output_combo_box = QComboBox(self)
        output_combo_box.setMaximumWidth(200)
        for device in output_devices:
            output_combo_box.addItem(device.get('name'))
        output_combo_box.activated[str].connect(self.output_choice)
        output_layout.addWidget(output_label)
        output_layout.addWidget(output_combo_box)
        
        device_layout.addLayout(input_layout)
        device_layout.addLayout(output_layout)
        
        device_widget = QWidget()
        device_widget.setMaximumHeight(100)
        device_widget.setLayout(device_layout)

        # Create the maptlotlib FigureCanvas object,
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)

        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.sc)
        plot_widget = QWidget()
        plot_widget.setMinimumHeight(400)
        plot_widget.setLayout(plot_layout)

        info_layout = QHBoxLayout()
        self.hz_label = QLabel(" Hz")
        self.hz_label.setMaximumWidth(100)
        self.hz_label.setFixedHeight(30)
        self.hz_label.setMargin(20)
        self.hz_label.setStyleSheet("background-color: #3a3a3a;  color : red")
        info_layout.addWidget(self.hz_label)

        control_layout = QHBoxLayout()
        slider0 = QSlider(Qt.Horizontal)
        slider0.setMinimum(1000)
        slider0.setMaximum(10000)
        slider0.setValue(5000)
        slider0.setMaximumWidth(300)
        slider0.setStyleSheet(
            "QSlider::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #3a3a3a); border: 1px solid #5c5c5c; width: 10px; border-radius: 3px; margin: -7px 0;} \
             QSlider::groove:horizontal {border: 1px solid #777777;height: 5px; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #b22222, stop:1 #777777); margin: 0px 0;}")
        slider0.valueChanged.connect(self.slider_change)
        slider0.setTickInterval(1000)
        slider0.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        control_layout.addWidget(slider0)
        control_widget = QWidget()
        control_widget.setFixedHeight(50)
        control_widget.setLayout(control_layout)

        self.label = QLabel(" ms")
        self.label.setMaximumWidth(100)
        self.label.setFixedHeight(30)
        self.label.setMargin(20)
        self.label.setStyleSheet("background-color: #3a3a3a;  color : red")
        info_layout.addWidget(self.label)
        info_widget = QWidget()
        info_widget.setLayout(info_layout)

        page_layout.addWidget(button_widget)
        page_layout.addWidget(device_widget)
        page_layout.addWidget(plot_widget)
        page_layout.addWidget(control_widget)
        #page_layout.addWidget(info_widget)

        self.setCentralWidget(page_widget)

    def on_click_out(self):
        if not self.output_on:
            if self.monitor_on:
                self.on_click()
            else:
                self.my_audio.start_stream(output=True, chunk=CHUNK, device=self.input_device_id, output_device=self.output_device_id)
                self.monitor_on = True
                self.button_on.setText('MONITOR\nON')
                self.button_on.setStyleSheet("background-color: #3a3a3a; color: green")
                self.output_on = True
                self.button_on_out.setText('OUTPUT\nON')
                self.button_on_out.setStyleSheet("background-color: #3a3a3a; color: green")
                self.timer.start(self.refresh_rate)
        else:
            self.my_audio.stop_stream()
            self.monitor_on = False
            self.button_on.setText('MONITOR\nOFF')
            self.button_on.setStyleSheet("background-color: #777777")
            self.output_on = False
            self.button_on_out.setText('OUTPUT\nOFF')
            self.button_on_out.setStyleSheet("background-color: #777777")
            self.timer.stop()

    def on_click(self):
        if not self.monitor_on:
            self.my_audio.start_stream(output=False, chunk=CHUNK, device=self.input_device_id)
            self.monitor_on = True
            self.button_on.setText('MONITOR\nON')
            self.button_on.setStyleSheet ("background-color: #3a3a3a; color: green")
            self.timer.start(self.refresh_rate)
        else:
            self.my_audio.stop_stream()
            self.monitor_on = False
            self.button_on.setText('MONITOR\nOFF')
            self.button_on.setStyleSheet ("background-color: #777777")
            self.timer.stop()

    def update_data(self):
        try:
            self.hz = self.sc.update_plot(self.my_audio.audio)
        except Exception as e:
            print(e)

    def input_choice(self, choice):
        self.input_device_id = self.get_device_index_by_name(choice)
        if self.monitor_on:
            self.my_audio.stop_stream()
            self.my_audio.start_stream(output=self.output_on, chunk=CHUNK, device=self.input_device_id)

    def output_choice(self, choice):
        self.output_device_id = self.get_device_index_by_name(choice, is_output=True)
        if self.output_on:
            self.my_audio.stop_stream()
            self.my_audio.start_stream(output=True, chunk=CHUNK, device=self.input_device_id, output_device=self.output_device_id)

    def get_device_index_by_name(self, choice, is_output=False):
        devices = self.my_audio.get_output_devices_info() if is_output else self.my_audio.get_input_devices_info()
        device_id = 0
        for device in devices:
            if device.get('name') == choice:
                device_id = device.get('index')
        return device_id

    def slider_change(self, value):
        self.sc.bx.set_xlim([0, value])
        self.sc.ax.set_xlim([0, 1000-value/10])
        self.sc.draw()

    def closeEvent(self, event):
        """Override closeEvent to ensure audio stream is properly closed"""
        if self.monitor_on:
            self.my_audio.stop_stream()
        event.accept()


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()