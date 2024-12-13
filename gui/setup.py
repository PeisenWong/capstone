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
model = YOLO("models/trained.pt")


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

        # Adjustable box properties
        self.adjustable_box = None
        self.dragging = False
        self.current_frame = None
        self.processed_frame = None

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

            self.adjustable_boxes = []  # To store bounding boxes and their class IDs

            # Define unique colors for adjustable boxes
            adjustable_colors = {}
            adjustable_palette = [
                (128, 0, 0), (0, 128, 0), (0, 0, 128),
                (128, 128, 0), (128, 0, 128), (0, 128, 128)
            ]

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # Extract bounding box, confidence, and class ID
                    b = box.xyxy[0].cpu().numpy()  # Get box coordinates in (x1, y1, x2, y2)
                    cls_id = int(box.cls)  # Class ID
                    self.adjustable_boxes.append((b, cls_id))  # Store box with class ID

                    # Assign unique colors for adjustable boxes
                    if cls_id not in adjustable_colors:
                        adjustable_colors[cls_id] = adjustable_palette[len(adjustable_colors) % len(adjustable_palette)]

                    print(f"Detected Box: {b}, Class: {model.names[cls_id]}, Confidence: {box.conf.item():.2f}")

            # Enable interaction for the adjustable boxes
            self.enable_adjustable_boxes(adjustable_colors)

    def enable_adjustable_boxes(self, adjustable_colors):
        """Enable adjustable boxes for all detected objects with enhanced corners and labels."""
        if self.current_frame is not None and self.adjustable_boxes:
            window_name = "Adjustable Boxes"
            cv2.namedWindow(window_name)
            cv2.setMouseCallback(window_name, self.handle_mouse_event)

            while True:
                frame = self.current_frame.copy()  # Use the original frame without detections

                # Draw all adjustable boxes
                for box, cls_id in self.adjustable_boxes:
                    x1, y1, x2, y2 = [int(coord) for coord in box]
                    color = adjustable_colors[cls_id]  # Use adjustable box color for this class

                    # Draw the adjustable box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    # Draw larger, distinct white points at the corners of the box
                    corner_radius = 6
                    cv2.circle(frame, (x1, y1), corner_radius, (255, 255, 255), -1)  # Top-left
                    cv2.circle(frame, (x2, y1), corner_radius, (255, 255, 255), -1)  # Top-right
                    cv2.circle(frame, (x1, y2), corner_radius, (255, 255, 255), -1)  # Bottom-left
                    cv2.circle(frame, (x2, y2), corner_radius, (255, 255, 255), -1)  # Bottom-right

                    # Display the class name above the box
                    label = f"{model.names[cls_id]}"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.6
                    thickness = 2
                    text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                    text_x = x1
                    text_y = max(y1 - 10, 0)  # Position label above the box
                    cv2.rectangle(
                        frame, 
                        (text_x, text_y - text_size[1] - 5), 
                        (text_x + text_size[0] + 5, text_y + 5), 
                        (255, 255, 255), 
                        -1  # Filled rectangle for background
                    )
                    cv2.putText(
                        frame, label, 
                        (text_x + 2, text_y), 
                        font, font_scale, (0, 0, 0), thickness
                    )

                cv2.imshow(window_name, frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cv2.destroyWindow(window_name)

    def handle_mouse_event(self, event, x, y, flags, param):
        """Handle mouse events for dragging the adjustable boxes while allowing independent corner movement."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if the mouse is near the corners of any box
            for i, (box, cls_id) in enumerate(self.adjustable_boxes):
                x1, y1, x2, y2 = [int(coord) for coord in box]
                if abs(x - x1) < 10 and abs(y - y1) < 10:  # Top-left corner
                    self.dragging = (i, "top_left")
                elif abs(x - x2) < 10 and abs(y - y1) < 10:  # Top-right corner
                    self.dragging = (i, "top_right")
                elif abs(x - x1) < 10 and abs(y - y2) < 10:  # Bottom-left corner
                    self.dragging = (i, "bottom_left")
                elif abs(x - x2) < 10 and abs(y - y2) < 10:  # Bottom-right corner
                    self.dragging = (i, "bottom_right")

        elif event == cv2.EVENT_MOUSEMOVE and self.dragging:
            # Adjust the corner being dragged while keeping other corners fixed
            i, corner = self.dragging
            box, cls_id = self.adjustable_boxes[i]
            if corner == "top_left":
                box[0], box[1] = x, y
            elif corner == "top_right":
                box[2], box[1] = x, y
            elif corner == "bottom_left":
                box[0], box[3] = x, y
            elif corner == "bottom_right":
                box[2], box[3] = x, y

            # Update the box coordinates dynamically
            self.adjustable_boxes[i] = (box, cls_id)

        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()  # Placeholder for a main window if needed
    setup_page = SetupPage(main_window)
    setup_page.show()
    sys.exit(app.exec_())
