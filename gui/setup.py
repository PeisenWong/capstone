import cv2
import os
from ultralytics import YOLO
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import sys

# Load YOLOv8 model
model = YOLO("models/yolov8n.pt")

class SetupPage(QWidget):
    def __init__(self, main_window, rtsp_url="rtsp://peisen:peisen@192.168.113.39:554/stream2"):
        super().__init__()

        self.main_window = main_window
        self.setWindowTitle("Camera Streaming and Capture")
        self.setGeometry(100, 100, 1200, 800)

        # Main layout
        main_layout = QHBoxLayout()

        # First column layout: RTSP Camera Stream and Instructions
        first_col_layout = QVBoxLayout()

        self.camera_label = QLabel("Streaming RTSP Camera")
        self.camera_label.setFixedSize(400, 300)
        first_col_layout.addWidget(self.camera_label)

        self.instructions_label = QLabel("Instructions: Ensure proper network connectivity for smooth streaming.")
        self.instructions_label.setStyleSheet("font-size: 14px; color: gray;")
        first_col_layout.addWidget(self.instructions_label)

        # Second column layout: Captured image and buttons
        second_col_layout = QVBoxLayout()

        # Image display (first row)
        self.captured_image_label = QLabel("Captured Frame")
        self.captured_image_label.setFixedSize(400, 300)
        second_col_layout.addWidget(self.captured_image_label)

        # Buttons (second row)
        button_row_layout = QHBoxLayout()
        self.capture_button_1 = QPushButton("Capture")
        self.capture_button_1.clicked.connect(self.capture_callback)
        button_row_layout.addWidget(self.capture_button_1)

        self.capture_button_2 = QPushButton("Clear")
        self.capture_button_2.clicked.connect(self.clear)
        button_row_layout.addWidget(self.capture_button_2)

        self.capture_button_3 = QPushButton("Confirm")
        self.capture_button_3.clicked.connect(self.confirm)
        button_row_layout.addWidget(self.capture_button_3)

        second_col_layout.addLayout(button_row_layout)

        # Add layouts to the main layout
        main_layout.addLayout(first_col_layout)
        main_layout.addLayout(second_col_layout)

        self.setLayout(main_layout)

        # Camera properties
        self.rtsp_url = rtsp_url
        self.cap = cv2.VideoCapture(self.rtsp_url)

        if not self.cap.isOpened():
            print("Error: Unable to access the RTSP camera stream.")
            sys.exit()

        # Timer for updating camera stream
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stream)
        self.timer.start(30)  # Update every 30 ms

    def confirm(self):
        print("Confirm")

    def clear(self):
        self.captured_image_label.setText("Captured Frame")

    def update_stream(self):
        """Update the camera stream in the first column."""
        ret, frame = self.cap.read()
        if not ret:
            self.camera_label.setText("Failed to fetch camera stream!")
            return

        # Resize and display the frame
        frame = cv2.resize(frame, (400, 300))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = channel * width
        qt_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

        # Save the current frame for capture purposes
        self.current_frame = frame

    def capture_callback(self):
        """Capture the current frame, process it with YOLOv8, and display the annotated image."""
        if hasattr(self, "current_frame") and self.current_frame is not None:
            # Run YOLO model on the captured frame
            results = model(self.current_frame)  # Perform YOLOv8 inference
            
            # Annotate the frame with the detection results
            annotated_frame = results[0].plot()  # Get the annotated frame

            print(results[0])
            print(results[0].boxes.cls)
            
            # Convert the annotated frame to RGB for QImage display
            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            height, width, channel = annotated_frame_rgb.shape
            bytes_per_line = channel * width
            qt_image = QImage(annotated_frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Display the annotated image in the captured image label
            self.captured_image_label.setPixmap(QPixmap.fromImage(qt_image))
        else:
            self.captured_image_label.setText("No frame available to capture!")

    def closeEvent(self, event):
        """Cleanup on close."""
        self.timer.stop()
        if self.cap.isOpened():
            self.cap.release()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()  # Placeholder for a main window if needed
    setup_page = SetupPage(main_window)
    setup_page.show()
    sys.exit(app.exec_())
