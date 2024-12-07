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

# Import your face recognition and object detection functions
from face_process import process_frame, draw_results, calculate_fps
from utils.visualize import visualize

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Global variables for FPS calculation (face recognition side)
COUNTER, FPS = 0, 0
START_TIME = time.time()

class CombinedPage(QWidget):
    def __init__(self, 
                 ip_camera_url="rtsp://peisen:peisen@192.168.113.39:554/stream2", 
                 model_path="models/efficientdet_lite0.tflite",
                 max_results=5, 
                 score_threshold=0.25):
        super().__init__()

        self.setWindowTitle("Combined Face Recognition & Object Detection")
        self.setGeometry(100, 100, 1200, 800)

        # Flag to enable/disable face recognition
        self.face_recognition_enabled = False

        # -----------------------
        # Layout Setup
        # -----------------------
        main_layout = QVBoxLayout(self)

        # Top row: 2 columns (IP camera left, Webcam right)
        top_layout = QHBoxLayout()
        self.ip_camera_label = QLabel("IP Camera Stream (Object Detection)")
        self.ip_camera_label.setAlignment(Qt.AlignCenter)
        self.ip_camera_label.setMinimumHeight(200)
        self.ip_camera_label.setStyleSheet("border:1px solid black;")

        self.webcam_label = QLabel("Webcam Stream (Face Recognition)")
        self.webcam_label.setAlignment(Qt.AlignCenter)
        self.webcam_label.setMinimumHeight(200)
        self.webcam_label.setStyleSheet("border:1px solid black;")

        top_layout.addWidget(self.ip_camera_label)
        top_layout.addWidget(self.webcam_label)
        top_layout.setStretch(0, 1)
        top_layout.setStretch(1, 1)

        # Bottom row: 3 columns (40% : 20% : 40%)
        bottom_layout = QHBoxLayout()

        # Left: Table (40%)
        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        for i in range(5):
            for j in range(3):
                self.table.setItem(i, j, QTableWidgetItem(str(np.random.randint(1, 100))))

        # Middle: 4 distinct buttons (20%)
        button_layout = QVBoxLayout()
        self.button1 = QPushButton("Button 1")
        self.button1.clicked.connect(self.button1Callback)
        button_layout.addWidget(self.button1)

        self.button2 = QPushButton("Button 2")
        self.button2.clicked.connect(self.button2Callback)
        button_layout.addWidget(self.button2)

        self.button3 = QPushButton("Button 3")
        self.button3.clicked.connect(self.button3Callback)
        button_layout.addWidget(self.button3)

        self.button4 = QPushButton("Button 4")
        self.button4.clicked.connect(self.button4Callback)
        button_layout.addWidget(self.button4)

        button_layout.addStretch()

        # Right: 4 status labels vertically (40%)
        status_layout = QVBoxLayout()
        # Let's say these are the fixed names for the 4 statuses
        status_names = [
            "Connection Status",
            "People Detected",
            "Machine Running",
            "Door Locked"
        ]

        # Create a list to store references to the labels for updating later
        self.status_labels = []

        for i, name in enumerate(status_names, start=1):
            # Initialize with "N/A" as the state
            label = QLabel(f"Status {i}: {name} - N/A")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border:1px solid black;")
            status_layout.addWidget(label)
            self.status_labels.append(label)

        status_layout.addStretch()

        # Add all to bottom_layout with stretches 2:1:2 to represent 40%:20%:40%
        bottom_layout.addWidget(self.table, 2)
        bottom_layout.addLayout(button_layout, 1)
        bottom_layout.addLayout(status_layout, 2)

        # Add top and bottom layouts to main layout
        main_layout.addLayout(top_layout, 1)
        main_layout.addLayout(bottom_layout, 1)

        # -----------------------
        # Camera Initialization
        # -----------------------
        # IP camera for object detection
        self.ip_cap = cv2.VideoCapture(ip_camera_url)
        self.ip_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.ip_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not self.ip_cap.isOpened():
            self.ip_camera_label.setText("Failed to access IP camera!")

        # Webcam for face recognition (not started yet)
        self.webcam_cap = None

        # Timer for frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # -----------------------
        # Object Detection Model Setup
        # -----------------------
        self.detection_result_list = []
        self.last_restart_time = datetime.now()
        self.camera_restart_interval = timedelta(minutes=1)

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.ObjectDetectorOptions(base_options=base_options,
                                               running_mode=vision.RunningMode.LIVE_STREAM,
                                               max_results=max_results,
                                               score_threshold=score_threshold,
                                               result_callback=self.save_detection_result)
        self.detector = vision.ObjectDetector.create_from_options(options)

        # Visualization parameters for object detection
        self.row_size = 50  # pixels
        self.left_margin = 24  # pixels
        self.text_color = (0, 0, 0)  # black
        self.font_size = 1
        self.font_thickness = 1

        self.update_status_label(0, "True")
        self.update_status_label(1, "False")
        self.update_status_label(2, "Idk")
        self.update_status_label(3, "Bruh")

    def button1Callback(self):
        print("Button 1 clicked")

    def button2Callback(self):
        print("Button 2 clicked")

    def button3Callback(self):
        print("Button 3 clicked")

    def button4Callback(self):
        print("Button 4 clicked")

    def update_status_label(self, index, new_state):
        """
        Update the state of the status label at the given index (0 to 3).
        new_state could be True, False, "Yes", "No", etc.
        """
        # Ensure index is within range
        if 0 <= index < len(self.status_labels):
            # Extract the fixed part of the label text to reconstruct
            # Example of label text: "Status 1: Connection Status - N/A"
            # We'll split by ' - ' and replace the second part
            current_text = self.status_labels[index].text()
            fixed_part = current_text.split(' - ')[0]  # "Status X: Name"
            # Update with new state
            self.status_labels[index].setText(f"{fixed_part} - {new_state}")

    def print_message(self, msg):
        print(msg)

    def save_detection_result(self, result: vision.ObjectDetectorResult, unused_output_image: mp.Image, timestamp_ms: int):
        global FPS, COUNTER, START_TIME
        fps_avg_frame_count = 10

        # Calculate the FPS (for object detection side if needed)
        if COUNTER % fps_avg_frame_count == 0:
            FPS = fps_avg_frame_count / (time.time() - START_TIME)
            START_TIME = time.time()

        self.detection_result_list.append(result)
        COUNTER += 1

    def update_frame(self):
        current_time = datetime.now()

        # Restart IP camera if needed
        if current_time - self.last_restart_time > self.camera_restart_interval:
            if self.ip_cap and self.ip_cap.isOpened():
                self.ip_cap.release()
            self.ip_cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.113.39:554/stream2")
            self.ip_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.ip_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.last_restart_time = current_time

        # -----------------------
        # Object Detection with IP camera
        # -----------------------
        ip_success, ip_frame = (self.ip_cap.read() if self.ip_cap else (False, None))
        if not ip_success or ip_frame is None:
            self.ip_camera_label.setText("Failed to read IP camera frame.")
        else:
            # Object detection
            ip_rgb = cv2.cvtColor(ip_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=ip_rgb)
            self.detector.detect_async(mp_image, time.time_ns() // 1_000_000)

            # Show FPS on IP camera frame (for object detection)
            fps_text = f'FPS: {FPS:.1f}'
            text_location = (self.left_margin, self.row_size)
            current_frame = ip_frame
            cv2.putText(current_frame, fps_text, text_location, cv2.FONT_HERSHEY_DUPLEX,
                        self.font_size, self.text_color, self.font_thickness, cv2.LINE_AA)

            detection_frame = ip_frame.copy()
            if self.detection_result_list:
                detection_frame, person_detected = visualize(current_frame, self.detection_result_list[0])
                self.detection_result_list.clear()
            else:
                person_detected = False  # No results yet

            # Convert BGR to QImage for IP camera label
            ip_height, ip_width, ip_channel = detection_frame.shape
            ip_bytes_per_line = ip_channel * ip_width
            ip_qt_image = QImage(detection_frame.data, ip_width, ip_height, ip_bytes_per_line, QImage.Format_BGR888)
            self.ip_camera_label.setPixmap(QPixmap.fromImage(ip_qt_image))

        # -----------------------
        # Face Recognition with Webcam (only if enabled)
        # -----------------------
        # If you later add logic to start/stop face recognition, you can handle it here.
        # Currently, no start/stop is implemented for face recognition in this version.
        # Just showing that no recognition is done if disabled.
        if self.face_recognition_enabled and self.webcam_cap and self.webcam_cap.isOpened():
            wb_success, wb_frame = self.webcam_cap.read()
            if not wb_success or wb_frame is None:
                self.webcam_label.setText("Failed to read Webcam frame.")
            else:
                # Face recognition
                processed_frame, is_authorized, user = process_frame(wb_frame)
                display_frame = draw_results(processed_frame)
                current_fps = calculate_fps()

                # Attach FPS counter for face recognition
                cv2.putText(display_frame, f"FPS: {current_fps:.1f}", 
                            (display_frame.shape[1] - 150, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Convert frame for PyQt display
                wb_height, wb_width, wb_channel = display_frame.shape
                wb_bytes_per_line = 3 * wb_width
                wb_qt_image = QImage(display_frame.data, wb_width, wb_height, wb_bytes_per_line, QImage.Format_BGR888)
                self.webcam_label.setPixmap(QPixmap.fromImage(wb_qt_image))

                if is_authorized:
                    pass  # Handle authorized user if needed

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CombinedPage()
    window.show()
    sys.exit(app.exec_())
