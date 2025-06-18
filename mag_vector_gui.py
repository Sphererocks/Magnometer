import sys
import time
import math
from collections import deque
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import board
import busio
import adafruit_lis2mdl
from gpiozero import LED

# === Sensor Initialization ===
i2c = busio.I2C(board.SCL, board.SDA)
mag_sensor = adafruit_lis2mdl.LIS2MDL(i2c)

# === GPIO Setup Using gpiozero ===
gpio_output = LED(16)
gpio_output.off()

# === Spike Detection Thresholds ===
VECTOR_JUMP_THRESHOLD = 25.0  # uT change to register motion
MAG_JUMP_THRESHOLD = 10.0     # uT change in |B| to register motion (optional)
HISTORY_LENGTH = 200          # Number of points to show in graph
SMOOTHING_ALPHA = 0.3         # Low-pass filter alpha (0.0 - 1.0)
SPIKE_HOLD_TIME = 5.0         # Seconds to hold GPIO HIGH

# === PyQt Application Setup ===
class MagnetometerGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magnetic Field Monitor")
        self.setGeometry(100, 100, 1280, 720)

        # Data history
        self.x_data = deque(maxlen=HISTORY_LENGTH)
        self.y_data = deque(maxlen=HISTORY_LENGTH)
        self.z_data = deque(maxlen=HISTORY_LENGTH)
        self.mag_data = deque(maxlen=HISTORY_LENGTH)

        # Smoothed previous values
        self.prev_x = None
        self.prev_y = None
        self.prev_z = None
        self.prev_mag = None

        self.last_vector = (0, 0, 0)
        self.spike_count = 0
        self.use_mag_only = False
        self.spike_active = False
        self.spike_start_time = None

        self.initUI()
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(100)  # 10 Hz

    def initUI(self):
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)

        # Plot widget
        self.plot_widget = pg.PlotWidget(title="Magnetic Field Components (uT)")
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_x = self.plot_widget.plot(pen='r', name='X')
        self.plot_y = self.plot_widget.plot(pen='g', name='Y')
        self.plot_z = self.plot_widget.plot(pen='b', name='Z')
        self.plot_mag = self.plot_widget.plot(pen='y', name='|B|')
        layout.addWidget(self.plot_widget)

        # Toggle checkbox
        self.toggle_checkbox = QtWidgets.QCheckBox("Use Magnitude Only")
        self.toggle_checkbox.stateChanged.connect(self.toggle_mode)
        layout.addWidget(self.toggle_checkbox)

        # Info display
        self.info_label = QtWidgets.QLabel("Initializing...", self)
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 24px; padding: 10px;")
        layout.addWidget(self.info_label)

    def toggle_mode(self, state):
        self.use_mag_only = state == QtCore.Qt.Checked

    def low_pass_filter(self, new_value, prev_value):
        if prev_value is None:
            return new_value
        return SMOOTHING_ALPHA * new_value + (1 - SMOOTHING_ALPHA) * prev_value

    def update_data(self):
        try:
            x_raw, y_raw, z_raw = mag_sensor.magnetic

            # Apply low-pass filtering
            self.prev_x = self.low_pass_filter(x_raw, self.prev_x)
            self.prev_y = self.low_pass_filter(y_raw, self.prev_y)
            self.prev_z = self.low_pass_filter(z_raw, self.prev_z)

            x, y, z = self.prev_x, self.prev_y, self.prev_z
            magnitude = math.sqrt(x**2 + y**2 + z**2)
            self.prev_mag = self.low_pass_filter(magnitude, self.prev_mag)

            self.x_data.append(x)
            self.y_data.append(y)
            self.z_data.append(z)
            self.mag_data.append(self.prev_mag)

            self.plot_x.setData(list(self.x_data))
            self.plot_y.setData(list(self.y_data))
            self.plot_z.setData(list(self.z_data))
            self.plot_mag.setData(list(self.mag_data))

            # Spike hold release check
            if self.spike_active and (time.time() - self.spike_start_time >= SPIKE_HOLD_TIME):
                gpio_output.off()
                self.spike_active = False

            # Motion detection
            if self.use_mag_only:
                mag_delta = abs(self.prev_mag - math.sqrt(self.last_vector[0]**2 + self.last_vector[1]**2 + self.last_vector[2]**2))
                triggered = mag_delta >= MAG_JUMP_THRESHOLD
            else:
                dx = abs(x - self.last_vector[0])
                dy = abs(y - self.last_vector[1])
                dz = abs(z - self.last_vector[2])
                delta = max(dx, dy, dz)
                mag_delta = abs(self.prev_mag - math.sqrt(self.last_vector[0]**2 + self.last_vector[1]**2 + self.last_vector[2]**2))
                triggered = delta >= VECTOR_JUMP_THRESHOLD or mag_delta >= MAG_JUMP_THRESHOLD

            if triggered:
                self.spike_count += 1
                self.info_label.setText(f"\u26a1 Motion Detected! |B|: {self.prev_mag:.1f} uT | Spikes: {self.spike_count}")
                self.info_label.setStyleSheet("color: red; font-size: 28px; font-weight: bold;")
                gpio_output.on()
                self.spike_active = True
                self.spike_start_time = time.time()
            else:
                self.info_label.setText(f"X: {x:.1f} Y: {y:.1f} Z: {z:.1f} | |B|: {self.prev_mag:.1f} uT | Spikes: {self.spike_count}")
                self.info_label.setStyleSheet("font-size: 24px;")

            self.last_vector = (x, y, z)

        except Exception as e:
            self.info_label.setText(f"Error reading sensor: {e}")
            self.info_label.setStyleSheet("color: orange; font-size: 18px;")

# === Main Launch ===
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MagnetometerGUI()
    window.show()
    sys.exit(app.exec_())
