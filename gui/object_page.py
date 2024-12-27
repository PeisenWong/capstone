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
import numpy as np

# Global variables to calculate FPS
COUNTER, FPS = 0, 0
START_TIME = time.time()

class ObjectPage(QWidget):
    def __init__(self, main_window, model="models/efficientdet_lite0.tflite", max_results=5, score_threshold=0.3, width=640, height=480):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Responsive GUI with Camera and Table")
        self.setGeometry(100, 100, 1200, 800)
        self.height = height
        self.width = width
        self.stop_detected = False
        self.slow_detected = False
        self.start_robot = False
        self.stop_robot = False
        self.ticks = 0
        self.current_state = "disabled"

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

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.button1_callback)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.button2_callback)
        button_layout.addWidget(self.stop_button)

        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(QApplication.quit)
        button_layout.addWidget(self.quit_button)

        # Status label 
        self.status_label = QLabel("Disabled")
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

        self.speaker_timer = QTimer()
        self.speaker_timer.timeout.connect(self.update_speaker)

        self.robot_timer = QTimer()
        self.robot_timer.timeout.connect(self.update_robot)

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

        self.timer.start(30)  # Update every 30 ms
        # self.speaker_timer.start(2000)  # Update every 2s
        # self.robot_timer.start(2000)  # Update every 2s

    def populate_table_with_random_data(self):
        """Populate the table with random data."""
        for i in range(5):  # 5 rows
            for j in range(3):  # 3 columns
                self.table.setItem(i, j, QTableWidgetItem(str(np.random.randint(1, 100))))

    def button1_callback(self):
        self.update_robot_state("normal")

    def button2_callback(self):
        self.update_robot_state("disabled")  # Disable commands

    def update_speaker(self):
        if self.main_window.robot.connected:
            if self.stop_detected:
                self.engine.say("   Stop")
                self.engine.runAndWait()

            if self.slow_detected:
                self.engine.say("   Slow")
                self.engine.runAndWait()

    def update_robot(self):
        if self.stop_detected:
            self.main_window.robot.stop()

        if self.slow_detected:
            self.main_window.robot.slow()

        if not self.slow_detected and not self.stop_detected and self.start_robot:
            self.main_window.robot.start()

    def update_robot_state(self, new_state):
        """Update the robot's state and send commands only if the state changes."""
        if self.current_state != new_state:
            self.current_state = new_state  # Update to the new state

            if new_state == "stop":
                self.main_window.robot.stop()
                self.status_label.setText("Stop")
                print("Robot stopped.")
            elif new_state == "slow":
                self.main_window.robot.slow()
                self.status_label.setText("Slow")
                print("Robot slowed down.")
            elif new_state == "normal":
                self.main_window.robot.start()
                self.status_label.setText("Normal")
                print("Robot returned to normal operation.")
            elif new_state == "disabled":
                self.status_label.setText("Disabled")
                print("Robot commands are disabled.")

    def update_frame(self):
        # Update IP camera stream
        ip_success, ip_frame = (self.main_window.ip_cap.read() if self.main_window.ip_cap else (False, None))
        if not ip_success or ip_frame is None:
            self.ip_camera_label.setText("Failed to read IP camera frame.")
            return

        # Resize the frame to 400x300
        ip_frame = cv2.resize(ip_frame, (640, 480))

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

        detection_frame = current_frame.copy()
        person_detected = False
        if self.detection_result_list:
            detection_frame, person_detected = visualize(current_frame, self.detection_result_list[0])

        slow_zone = None
        stop_zone = None
        if hasattr(self.main_window, 'class_coordinates') and self.main_window.class_coordinates:
            # Find the slow zone and stop zone coordinates
            for item in self.main_window.class_coordinates:
                if item['class_name'] == 'slow_zone':
                    slow_zone = item
                elif item['class_name'] == 'stop_zone':
                    stop_zone = item

        # ---------------------
        # Draw Slow Zone Lines
        # ---------------------
        if slow_zone is not None:
            # Vertical line for Slow Zone (top_left to bottom_left)
            X_slow_tl, Y_slow_tl = slow_zone['corners']['top_left']
            X_slow_bl, Y_slow_bl = slow_zone['corners']['bottom_left']
            cv2.line(detection_frame, (X_slow_tl, Y_slow_tl), (X_slow_bl, Y_slow_bl), (0, 255, 255), 2)

            # Horizontal line for Slow Zone (bottom_left to bottom_right)
            X_slow_bl2, Y_slow_bl2 = slow_zone['corners']['bottom_left']
            X_slow_br, Y_slow_br = slow_zone['corners']['bottom_right']
            cv2.line(detection_frame, (X_slow_bl2, Y_slow_bl2), (X_slow_br, Y_slow_br), (0, 255, 255), 2)

            # Horizontal line for Slow Zone (top_left to top_right)
            X_slow_tl, Y_slow_tl = slow_zone['corners']['top_left']
            X_slow_tr, Y_slow_tr = slow_zone['corners']['top_right']
            cv2.line(detection_frame, (X_slow_tl, Y_slow_tl), (X_slow_tr, Y_slow_tr), (0, 255, 255), 2)

        # ---------------------
        # Draw Stop Zone Lines
        # ---------------------
        if stop_zone is not None:
            # Vertical line for Stop Zone (top_left to bottom_left)
            X_stop_tl, Y_stop_tl = stop_zone['corners']['top_left']
            X_stop_bl, Y_stop_bl = stop_zone['corners']['bottom_left']
            cv2.line(detection_frame, (X_stop_tl, Y_stop_tl), (X_stop_bl, Y_stop_bl), (0, 0, 255), 2)

            # Horizontal line for Stop Zone (bottom_left to bottom_right)
            X_stop_bl2, Y_stop_bl2 = stop_zone['corners']['bottom_left']
            X_stop_br, Y_stop_br = stop_zone['corners']['bottom_right']
            cv2.line(detection_frame, (X_stop_bl2, Y_stop_bl2), (X_stop_br, Y_stop_br), (0, 0, 255), 2)

            # Horizontal line for Stop Zone (top_left to top_right)
            X_stop_tl, Y_stop_tl = stop_zone['corners']['top_left']
            X_stop_tr, Y_stop_tr = stop_zone['corners']['top_right']
            cv2.line(detection_frame, (X_stop_tl, Y_stop_tl), (X_stop_tr, Y_stop_tr), (0, 0, 255), 2)

        # If a person is detected, perform zone checks
        if person_detected:
            def point_side_of_line(line_x1, line_y1, line_x2, line_y2, x, y):
                # Cross product: (y - y1)*dx - (x - x1)*dy
                dx = line_x2 - line_x1
                dy = line_y2 - line_y1
                return (y - line_y1)*dx - (x - line_x1)*dy

            # Check each detected person
            for detection in self.detection_result_list[0].detections:
                category_name = detection.categories[0].category_name
                if category_name == "person":
                    bbox = detection.bounding_box
                    X_person_tl = bbox.origin_x
                    Y_person_tl = bbox.origin_y
                    Y_person_br = bbox.origin_y + bbox.height
                    X_person_br = bbox.origin_x + bbox.width

                    # Person's bottom-left foot corner (same Y as bottom-right)
                    X_person_bl = bbox.origin_x
                    Y_person_bl = bbox.origin_y + bbox.height

                    # ---------------------
                    # Stop Zone Checks
                    # ---------------------
                    if stop_zone is not None:
                        # 1) Vertical stop line (top_left to bottom_left)
                        # Similar logic as slow zone vertical line
                        side_right_foot_stop_vert = point_side_of_line(X_stop_tl, Y_stop_tl, X_stop_bl, Y_stop_bl,
                                                                    X_person_br, Y_person_br)
                        
                        inside_right_stop_vert = (side_right_foot_stop_vert < 1700)

                        # 2) Horizontal stop line (bottom_left to bottom_right)
                        # Inside if > 0 means above the line
                        side_left_foot_stop_horz = point_side_of_line(X_stop_bl2, Y_stop_bl2, X_stop_br, Y_stop_br,
                                                                    X_person_bl, Y_person_bl)
                        inside_left_stop_horz = (side_left_foot_stop_horz < 1700)

                        left_foot_stop_vert = point_side_of_line(X_stop_tl, Y_stop_tl, X_stop_tr, Y_stop_tr, 
                                                                 X_person_br, Y_person_br)
                        print(f"LEFT: {left_foot_stop_vert}")

                        if inside_left_stop_horz and inside_right_stop_vert:
                            print("Person crosses stop zone horizontal line! (Above)")
                            cv2.putText(detection_frame, "INSIDE STOP ZONE!", (int(X_person_bl), int(Y_person_bl)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            self.stop_detected = True
                            
                        else:
                            print("Person is on stop zone horizontal boundary!")
                            self.stop_detected = False
                            # cv2.putText(detection_frame, "STOP ZONE HORIZ BOUNDARY!", (int(X_person_bl), int(Y_person_bl)),
                            #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            
                    # ---------------------
                    # Slow Zone Checks
                    # ---------------------
                    if slow_zone is not None:
                        # 1) Vertical slow line (top_left to bottom_left)
                        # Using original logic: inside if < 0
                        
                        side_right_foot_slow_vert = point_side_of_line(X_slow_tl, Y_slow_tl, X_slow_bl, Y_slow_bl,
                                                                    X_person_br, Y_person_br)
                        inside_right_slow_vert = (side_right_foot_slow_vert < -1500)

                        side_left_foot_slow_horz = point_side_of_line(X_slow_bl2, Y_slow_bl2, X_slow_br, Y_slow_br,
                                            X_person_bl, Y_person_bl)
                        inside_left_slow_horz = (side_left_foot_slow_horz < 0)

                        if  inside_right_slow_vert and inside_left_slow_horz and not self.stop_detected:
                            print(f"Person crosses slow zone vertical line! (Right side) {side_right_foot_slow_vert}")
                            cv2.putText(detection_frame, "INSIDE SLOW ZONE", (int(X_person_tl), int(Y_person_br)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                            self.slow_detected = True
                        else:
                            print("Person is not inside slow zone!")
                            self.slow_detected = False
                            # cv2.putText(detection_frame, "SLOW ZONE >= 0", (int(X_person_tl), int(Y_person_br)),
                            #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        self.detection_result_list.clear()

        # Convert BGR to QImage for IP camera label
        ip_height, ip_width, ip_channel = detection_frame.shape
        ip_bytes_per_line = ip_channel * ip_width
        ip_qt_image = QImage(detection_frame.data, ip_width, ip_height, ip_bytes_per_line, QImage.Format_BGR888)

        # Create a QPixmap from the QImage and directly set it (no scaling needed)
        ip_qt_pixmap = QPixmap.fromImage(ip_qt_image)

        # Directly set the pixmap since we already resized the frame
        self.camera_label.setPixmap(ip_qt_pixmap)


    # Update robot state based on detection
        if self.current_state != "disabled":  # Skip updates if in "disabled" state
            if self.stop_detected:
                self.update_robot_state("stop")
            elif self.slow_detected:
                self.update_robot_state("slow")
            else:
                self.update_robot_state("normal")