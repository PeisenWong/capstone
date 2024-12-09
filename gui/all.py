import sys
import cv2
import time
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt

class CombinedPage(QWidget):
    def __init__(self, 
                 ip_camera_url="rtsp://peisen:peisen@192.168.113.39:554/stream2", 
                 model_path="models/efficientdet_lite0.tflite",
                 max_results=5, 
                 score_threshold=0.25):
        super().__init__()

        self.setWindowTitle("Combined Face Recognition & Object Detection")
        self.resize(1200, 800)

        # -----------------------
        # Layout Setup
        # -----------------------
        main_layout = QVBoxLayout(self)

        # Top row: 2 columns (IP camera left, Webcam right)
        top_layout = QHBoxLayout()
        self.ip_camera_label = QLabel("IP Camera Stream (Object Detection)")
        self.ip_camera_label.setAlignment(Qt.AlignCenter)
        self.ip_camera_label.setFixedSize(400, 300)
        self.ip_camera_label.setStyleSheet("border:1px solid black;")

        self.webcam_label = QLabel("Webcam Stream (Face Recognition)")
        self.webcam_label.setAlignment(Qt.AlignCenter)
        self.webcam_label.setFixedSize(400, 300)
        self.webcam_label.setStyleSheet("border:1px solid black;")

        top_layout.addWidget(self.ip_camera_label)
        top_layout.addWidget(self.webcam_label)

        # Bottom row: 3 columns
        bottom_layout = QHBoxLayout()

        # Left: Table with random data
        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        for i in range(5):
            for j in range(3):
                self.table.setItem(i, j, QTableWidgetItem(str(np.random.randint(1, 100))))

        # Middle: Buttons
        button_layout = QVBoxLayout()
        self.button1 = QPushButton("Button 1")
        self.button1.clicked.connect(self.start_webcam_stream)
        button_layout.addWidget(self.button1)

        self.button2 = QPushButton("Button 2")
        button_layout.addWidget(self.button2)

        self.button3 = QPushButton("Button 3")
        button_layout.addWidget(self.button3)

        self.button4 = QPushButton("Button 4")
        button_layout.addWidget(self.button4)

        button_layout.addStretch()

        # Right: Status labels
        status_layout = QVBoxLayout()
        self.status_labels = []
        status_names = ["Connection Status", "People Detected", "Machine Running", "Door Locked"]
        for name in status_names:
            label = QLabel(f"{name}: N/A")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border:1px solid black;")
            self.status_labels.append(label)
            status_layout.addWidget(label)

        status_layout.addStretch()

        # Add widgets to bottom layout
        bottom_layout.addWidget(self.table, 2)
        bottom_layout.addLayout(button_layout, 1)
        bottom_layout.addLayout(status_layout, 2)

        # Combine layouts
        main_layout.addLayout(top_layout, 1)
        main_layout.addLayout(bottom_layout, 1)

        self.setLayout(main_layout)

        # -----------------------
        # Camera Initialization
        # -----------------------
        self.ip_cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.113.39:554/stream1")
        self.ip_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.ip_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.webcam_cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def start_webcam_stream(self):
        if not self.webcam_cap:
            self.webcam_cap = cv2.VideoCapture(0)
        print("Webcam stream started.")

    def update_frame(self):
        # Update IP camera stream
        ip_success, ip_frame = (self.ip_cap.read() if self.ip_cap else (False, None))
        if ip_success and ip_frame is not None:
            ip_rgb = cv2.cvtColor(ip_frame, cv2.COLOR_BGR2RGB)
            ip_height, ip_width, ip_channel = ip_rgb.shape
            ip_bytes_per_line = ip_channel * ip_width
            ip_qt_image = QImage(ip_rgb.data, ip_width, ip_height, ip_bytes_per_line, QImage.Format_RGB888)
            self.ip_camera_label.setPixmap(QPixmap.fromImage(ip_qt_image))
        else:
            self.ip_camera_label.setText("Failed to read IP camera stream.")

        # Update webcam stream
        if self.webcam_cap and self.webcam_cap.isOpened():
            wb_success, wb_frame = self.webcam_cap.read()
            if wb_success and wb_frame is not None:
                wb_rgb = cv2.cvtColor(wb_frame, cv2.COLOR_BGR2RGB)
                wb_height, wb_width, wb_channel = wb_rgb.shape
                wb_bytes_per_line = wb_channel * wb_width
                wb_qt_image = QImage(wb_rgb.data, wb_width, wb_height, wb_bytes_per_line, QImage.Format_RGB888)
                self.webcam_label.setPixmap(QPixmap.fromImage(wb_qt_image))
            else:
                self.webcam_label.setText("Failed to read webcam stream.")

