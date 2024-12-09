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

# Global variables to calculate FPS
COUNTER, FPS = 0, 0
START_TIME = time.time()

class ObjectPage(QWidget):
    def __init__(self, main_window, model="models/efficientdet_lite0.tflite", max_results=5, score_threshold=0.25, width=640, height=480):
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

        # User name label (row 1)
        self.user_label = QLabel(f"Welcome {self.main_window.userName}")
        self.user_label.setStyleSheet("font-size: 16px; color: blue;")
        first_col_layout.addWidget(self.user_label)

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

        self.camera_restart_interval = timedelta(minutes=1)
        self.last_restart_time = datetime.now()

    def showEvent(self, event):
        """Triggered when the ObjectPage is shown."""
        super().showEvent(event)

        # Reinitialize the camera if it was released
        if not self.cap or not self.cap.isOpened():
            self.cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.113.39:554/stream2")
        if not self.cap.isOpened():
            self.camera_label.setText("Failed to access camera!")
            return

        self.timer.start(30)  # Update every 30 ms
        
        self.user_label.setText(f"Welcome {self.main_window.userName}")

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
        current_time = datetime.now()
    
        # Check if it's time to restart the camera
        if current_time - self.last_restart_time > self.camera_restart_interval:
            print("Restarting the camera...")
            self.cap.release()
            self.cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.113.39:554/stream2")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.last_restart_time = current_time
        
        success, image = self.cap.read()
        image=cv2.resize(image,(640,480))
        if not success:
            sys.exit(
                'ERROR: Unable to read from webcam. Please verify your webcam settings.'
            )

        # image = cv2.flip(image, 1)

        # Convert the image from BGR to RGB as required by the TFLite model.
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # Run object detection using the model.
        self.detector.detect_async(mp_image, time.time_ns() // 1_000_000)

        # Show the FPS
        fps_text = 'FPS = {:.1f}'.format(FPS)
        text_location = (self.left_margin, self.row_size)
        current_frame = image
        cv2.putText(current_frame, fps_text, text_location, cv2.FONT_HERSHEY_DUPLEX,
                    self.font_size, self.text_color, self.font_thickness, cv2.LINE_AA)

        # Initialize detection_frame with the current image
        detection_frame = image.copy()
        if self.detection_result_list:
            # print(detection_result_list)
            detection_frame, person_detected = visualize(current_frame, self.detection_result_list[0])
            self.detection_result_list.clear()

            # Update detection status
            if person_detected:
                self.status_label.setText("Status: Person detected")
                # self.last_person_detected = current_time
                # if self.redirect_timer:
                #     self.redirect_timer.stop()
                #     self.redirect_timer = None
            else:
                # self.start_redirect_countdown()
                self.status_label.setText("Status: No Person detected")
        
        # Convert the BGR frame to QImage directly
        height, width, channel = detection_frame.shape
        bytes_per_line = channel * width
        qt_image = QImage(detection_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)

        # Update the QLabel with the QImage
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

    def switch_to_face_recognition(self):
        if self.cap:
            self.cap.release()
        self.timer.stop()
        self.main_window.switch_to_face_recognition()

    def start_redirect_countdown(self):
        """Starts the countdown if no person is detected."""
        time_since_last_detected = (datetime.now() - self.last_person_detected).total_seconds()
        if time_since_last_detected >= 5:
            self.status_label.setText("Status: Redirecting to face page...")
            self.switch_to_face_recognition()
        else:
            seconds_left = 5 - int(time_since_last_detected)
            self.status_label.setText(f"Status: No person detected, redirecting in {seconds_left}s...")
