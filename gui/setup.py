import cv2
import os
from ultralytics import YOLO
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
import sys
from ultralytics.utils.plotting import Annotator

# Load YOLOv8 model
model = YOLO("models/yolov8n.pt")

class AdjustableBoundingBox:
    def __init__(self, image, box):
        self.image = image
        self.box = box  # Initial box (x1, y1, x2, y2)
        self.start_point = None  # Dragging start point
        self.end_point = None  # Dragging end point
        self.selected_point = None  # Currently selected point
        self.dragging = False

    def draw_box(self):
        """Draw the adjustable box."""
        # Draw box and draggable points
        x1, y1, x2, y2 = map(int, self.box)
        color = (0, 255, 0)  # Green
        thickness = 2
        cv2.rectangle(self.image, (x1, y1), (x2, y2), color, thickness)

        # Draw corner points
        point_color = (0, 0, 255)  # Red
        point_radius = 5
        for point in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
            cv2.circle(self.image, point, point_radius, point_color, -1)

    def handle_event(self, event, x, y, flags, param):
        """Handle mouse events."""
        x1, y1, x2, y2 = map(int, self.box)

        # Check if mouse is pressed on a corner point
        if event == cv2.EVENT_LBUTTONDOWN:
            for idx, point in enumerate([(x1, y1), (x2, y1), (x1, y2), (x2, y2)]):
                px, py = point
                if abs(x - px) < 10 and abs(y - py) < 10:
                    self.selected_point = idx
                    self.dragging = True
                    break

        # Adjust the box dynamically during drag
        elif event == cv2.EVENT_MOUSEMOVE and self.dragging:
            if self.selected_point == 0:  # Top-left corner
                self.box[0], self.box[1] = x, y
            elif self.selected_point == 1:  # Top-right corner
                self.box[2], self.box[1] = x, y
            elif self.selected_point == 2:  # Bottom-left corner
                self.box[0], self.box[3] = x, y
            elif self.selected_point == 3:  # Bottom-right corner
                self.box[2], self.box[3] = x, y

        # Stop dragging
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False
            self.selected_point = None


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
            results = model.predict(self.current_frame)  # Perform YOLOv8 inference
            
            for r in results:
                annotator = Annotator(self.current_frame)
                
                boxes = r.boxes
                for box in boxes:
                    b = box.xyxy[0]  # get box coordinates
                    adjustable_box = AdjustableBoundingBox(self.current_frame.copy(), b.tolist())
                    
                    # Enable interaction
                    cv2.namedWindow("Adjustable Box")
                    cv2.setMouseCallback("Adjustable Box", adjustable_box.handle_event)
                    
                    while True:
                        adjustable_image = self.current_frame.copy()
                        adjustable_box.draw_box()
                        cv2.imshow("Adjustable Box", adjustable_image)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

                    cv2.destroyWindow("Adjustable Box")
        else:
            self.captured_image_label.setText("No frame available to capture!")

