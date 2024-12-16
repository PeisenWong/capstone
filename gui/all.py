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
                 main_window,
                 ip_cam_url="rtsp://peisen:peisen@192.168.113.39:554/stream2",
                 model_path="models/efficientdet_lite0.tflite",
                 max_results=5, 
                 score_threshold=0.3):
        super().__init__()

        self.setWindowTitle("Combined Face Recognition & Object Detection")
        self.main_window = main_window
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
        self.button1 = QPushButton("Start Face Recognition")
        self.button1.clicked.connect(self.start_webcam_stream)
        button_layout.addWidget(self.button1)

        self.button2 = QPushButton("Stop Face Recognition")
        self.button2.clicked.connect(self.close_webcam_stream)
        button_layout.addWidget(self.button2)

        self.button3 = QPushButton("Button 3")
        self.button3.clicked.connect(self.button3Callback)
        button_layout.addWidget(self.button3)

        self.button4 = QPushButton("Button 4")
        self.button4.clicked.connect(self.button4Callback)
        button_layout.addWidget(self.button4)

        self.button5 = QPushButton("Button 5")
        self.button5.clicked.connect(self.button5Callback)
        button_layout.addWidget(self.button5)

        self.button6 = QPushButton("Button 6")
        self.button6.clicked.connect(self.button6Callback)
        button_layout.addWidget(self.button6)

        button_layout.addStretch()

        # Right: Status labels
        status_layout = QVBoxLayout()
        self.status_labels = []
        status_names = ["User Authorized", "Connection Status", "People Detected", "Machine Running", "Door Locked"]
        for name in status_names:
            label = QLabel(f"{name} - N/A")
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
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.ObjectDetectorOptions(base_options=base_options,
                                                running_mode=vision.RunningMode.LIVE_STREAM,
                                                max_results=max_results, score_threshold=score_threshold,
                                                result_callback=save_result)
        self.detector = vision.ObjectDetector.create_from_options(options)

        # -----------------------
        # Camera Initialization
        # -----------------------
        self.ip_cap = cv2.VideoCapture(ip_cam_url)
        self.ip_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 400)
        self.ip_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)

        self.webcam_cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.face_timer = QTimer()
        self.face_timer.timeout.connect(self.face_update_frame)
        self.face_timer.start(30)
        self.face_counter = 0

        self.update_status_label(0, "Yes")
        self.update_status_label(1, "No")
        self.update_status_label(2, "IDK")
        self.update_status_label(3, "Bruh")

        self.face_recognition_enabled = False

    def print_message(self, msg):
        print(msg)

    def start_webcam_stream(self):
        """Start the webcam stream and initialize the face recognition timer."""
        if not self.webcam_cap:
            self.webcam_cap = cv2.VideoCapture(0)
            self.face_recognition_enabled = True
            self.webcam_label.setText("Webcam stream started.")
            self.update_status_label(0, "Authorizing...")
            self.face_counter = 0
        else:
            self.webcam_label.setText("Webcam is already running.")

    def close_webcam_stream(self):
        """Close the webcam stream and stop the timer."""
        if self.webcam_cap:
            self.webcam_cap.release()
            self.webcam_cap = None
            self.face_recognition_enabled = False
            self.webcam_label.clear()
            self.webcam_label.setText("Webcam stream closed.")
        else:
            self.webcam_label.setText("Webcam is not running.")

    def button3Callback(self):
        print("Button 3 clicked")

    def button4Callback(self):
        print("Button 4 clicked")

    def button5Callback(self):
        print("Button 5 clicked")

    def button6Callback(self):
        print("Button 6 clicked")

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

    def face_update_frame(self):
        # Update webcam stream
        if self.face_recognition_enabled and self.webcam_cap and self.webcam_cap.isOpened():
            wb_success, wb_frame = self.webcam_cap.read()
            if not wb_success or wb_frame is None:
                self.webcam_label.setText("Failed to read Webcam frame.")
            else:
                # Face recognition
                processed_frame, is_authorized, user = process_frame(wb_frame)

                # If authorized, close the webcam immediately
                if is_authorized:
                    print(f"Hi {user}, access granted!")
                    self.update_status_label(0, f"{user}")

                    # Update the webcam display
                    display_frame = draw_results(processed_frame)
                    wb_height, wb_width, wb_channel = display_frame.shape
                    wb_bytes_per_line = 3 * wb_width
                    wb_qt_image = QImage(display_frame.data, wb_width, wb_height, wb_bytes_per_line, QImage.Format_BGR888)
                    self.webcam_label.setPixmap(QPixmap.fromImage(wb_qt_image))

                    self.close_webcam_stream()
                    return
                else:
                    self.face_counter += 1
                    if self.face_counter == 100:
                        self.update_status_label(0, "Timeout")
                        self.close_webcam_stream()
                        return

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

    def update_frame(self):
        # Update IP camera stream
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

            # detection_frame = ip_frame.copy()
            detection_frame = cv2.resize(ip_frame, (400, 300))
            person_detected = False
            if self.detection_result_list:
                detection_frame, person_detected = visualize(current_frame, self.detection_result_list[0])

            # If a person is detected, perform slow zone check
            if person_detected and hasattr(self.main_window, 'class_coordinates') and self.main_window.class_coordinates:
                # Find the slow zone coordinates
                slow_zone = None
                for item in self.main_window.class_coordinates:
                    if item['class_name'] == 'Slow Zone':  # Adjust class_name if needed
                        slow_zone = item
                        break

                if slow_zone is not None:
                    X_slow_tl, Y_slow_tl = slow_zone['corners']['top_left']
                    X_slow_bl, Y_slow_bl = slow_zone['corners']['bottom_left']

                    # Draw the slow line in yellow
                    cv2.line(detection_frame, (X_slow_tl, Y_slow_tl), (X_slow_bl, Y_slow_bl), (0, 255, 255), 2)

                    # Define a helper function to determine side of a point w.r.t the slow zone line
                    def point_side_of_line(line_x1, line_y1, line_x2, line_y2, x, y):
                        # Cross product: (y - y1)*dx - (x - x1)*dy
                        dx = line_x2 - line_x1
                        dy = line_y2 - line_y1
                        return (y - line_y1)*dx - (x - line_x1)*dy

                    # Check each detection
                    for detection in self.detection_result_list[0].detections:
                        category_name = detection.categories[0].category_name
                        if category_name == "person":
                            bbox = detection.bounding_box
                            X_person_tl = bbox.origin_x
                            Y_person_br = bbox.origin_y + bbox.height
                            X_person_br = bbox.origin_x + bbox.width

                            # Compute side for both foot corners
                            side_left_foot = point_side_of_line(X_slow_tl, Y_slow_tl, X_slow_bl, Y_slow_bl,
                                                                X_person_tl, Y_person_br)
                            side_right_foot = point_side_of_line(X_slow_tl, Y_slow_tl, X_slow_bl, Y_slow_bl,
                                                                X_person_br, Y_person_br)

                            # Now consider the inside to be when side < 0 (right side of the line)
                            inside_left = (side_left_foot < 0)
                            inside_right = (side_right_foot < 0)

                            if inside_left and inside_right:
                                print("Person is fully inside the slow zone!")
                                cv2.putText(detection_frame, "SLOW ZONE!", (int(X_person_tl), int(Y_person_br)),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            elif inside_left != inside_right:
                                print("Person is stepping onto the slow zone boundary!")
                                cv2.putText(detection_frame, "STEPPING IN SLOW ZONE!", (int(X_person_tl), int(Y_person_br)),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            else:
                                print("Person is outside the slow zone.")

            self.detection_result_list.clear()

            # Convert BGR to QImage for IP camera label
            ip_height, ip_width, ip_channel = detection_frame.shape
            ip_bytes_per_line = ip_channel * ip_width
            ip_qt_image = QImage(detection_frame.data, ip_width, ip_height, ip_bytes_per_line, QImage.Format_BGR888)

            # Create a QPixmap from the QImage
            ip_qt_pixmap = QPixmap.fromImage(ip_qt_image)

            # Scale the pixmap to fit the label size while maintaining the aspect ratio
            scaled_pixmap = ip_qt_pixmap.scaled(self.ip_camera_label.size(), Qt.KeepAspectRatio)

            # Set the scaled pixmap to the label
            self.ip_camera_label.setPixmap(scaled_pixmap)



