from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2
import time
import sys
from datetime import datetime, timedelta
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from utils.visualize import visualize
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QTableWidget, QTableWidgetItem, QWidget
)
from utils.controller import RobotController
import numpy as np
from ultralytics import YOLO
import random

# Global variables to calculate FPS
COUNTER, FPS = 0, 0
START_TIME = time.time()

class TestPage(QWidget):
    def __init__(self, main_window, model="models/efficientdet_lite0.tflite", max_results=5, score_threshold=0.3, width=640, height=480):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Responsive GUI with Camera and Table")
        self.setGeometry(100, 100, 1200, 800)
        self.height = height
        self.width = width
        self.robot = RobotController()

        # Main layout
        main_layout = QHBoxLayout()

        # First column layout (camera and table)
        first_col_layout = QVBoxLayout()

        # Camera stream (row 2)
        self.camera_label = QLabel("Camera Stream")
        self.camera_label.setMinimumSize(640, 360)
        first_col_layout.addWidget(self.camera_label)

        # Table with random data (row 2)
        self.table = QTableWidget(5, 3)  # 5 rows, 3 columns
        self.table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        self.populate_table_with_random_data()
        first_col_layout.addWidget(self.table)

        # Second column layout (buttons)
        button_layout = QVBoxLayout()

        self.start_button = QPushButton("Button 1")
        self.start_button.clicked.connect(self.button1_callback)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Button 2")
        self.stop_button.clicked.connect(self.button2_callback)
        button_layout.addWidget(self.stop_button)

        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(QApplication.quit)
        button_layout.addWidget(self.quit_button)

        # Status label 
        self.status_label = QLabel("Status: Waiting for detection...")
        self.status_label.setStyleSheet("font-size: 14px; color: green;")
        button_layout.addWidget(self.status_label)

        # Add both columns to the main layout
        main_layout.addLayout(first_col_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Camera properties
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Detection tracking variables
        self.last_person_detected = datetime.now()
        self.redirect_timer = None

        # Visualization parameters
        self.row_size = 50  # pixels
        self.left_margin = 24  # pixels
        self.text_color = (0, 0, 0)  # black
        self.font_size = 1
        self.font_thickness = 1
        fps_avg_frame_count = 10

        self.detection_frame = None
        self.detection_result_list = []
        
        def save_result(result: vision.ObjectDetectorResult, unused_output_image: mp.Image, timestamp_ms: int):
            global FPS, COUNTER, START_TIME

            # Calculate the FPS
            if COUNTER % fps_avg_frame_count == 0:
                FPS = fps_avg_frame_count / (time.time() - START_TIME)
                START_TIME = time.time()

            self.detection_result_list.append(result)
            COUNTER += 1

        # Initialize the object detection model
        base_options = python.BaseOptions(model_asset_path=model)
        options = vision.ObjectDetectorOptions(base_options=base_options,
                                                running_mode=vision.RunningMode.LIVE_STREAM,
                                                max_results=max_results, score_threshold=score_threshold,
                                                result_callback=save_result)
        self.detector = vision.ObjectDetector.create_from_options(options)

        self.model = YOLO("../models/yolov8m-seg.pt")
        self.timer.start(30)  # Update every 30 ms

    def populate_table_with_random_data(self):
        """Populate the table with random data."""
        for i in range(5):  # 5 rows
            for j in range(3):  # 3 columns
                self.table.setItem(i, j, QTableWidgetItem(str(np.random.randint(1, 100))))

    def button1_callback(self):
        print("Button 1 Pressed")

    def button2_callback(self):
        print("Button 2 Pressed")

    def update_frame(self):
        # Update IP camera stream
        ip_success, ip_frame = (self.main_window.ip_cap.read() if self.main_window.ip_cap else (False, None))
        if not ip_success or ip_frame is None:
            self.camera_label.setText("Failed to read IP camera frame.")
            return

        # Resize the frame to 400x300
        ip_frame = cv2.resize(ip_frame, (640, 480))

        yolo_classes = list(self.model.names.values())
        classes_ids = [yolo_classes.index(clas) for clas in yolo_classes]

        conf = 0.5

        results = self.model.predict(ip_frame, conf=conf)
        colors = [random.choices(range(256), k=3) for _ in classes_ids]
        print(results)
        for result in results:
            for mask, box in zip(result.masks.xy, result.boxes):
                points = np.int32([mask])
                # cv2.polylines(img, points, True, (255, 0, 0), 1)
                color_number = classes_ids.index(int(box.cls[0]))
                cv2.fillPoly(ip_frame, points, colors[color_number])

        # Convert BGR to QImage for IP camera label
        ip_height, ip_width, ip_channel = ip_frame.shape
        ip_bytes_per_line = ip_channel * ip_width
        ip_qt_image = QImage(ip_frame.data, ip_width, ip_height, ip_bytes_per_line, QImage.Format_BGR888)

        # Create a QPixmap from the QImage and directly set it (no scaling needed)
        ip_qt_pixmap = QPixmap.fromImage(ip_qt_image)

        # Directly set the pixmap since we already resized the frame
        self.camera_label.setPixmap(ip_qt_pixmap)