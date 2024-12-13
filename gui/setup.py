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
        """Capture the current frame, process it with YOLOv8, and store four-corner boxes."""
        if hasattr(self, "current_frame") and self.current_frame is not None:
            # Run YOLO model on the captured frame
            results = model.predict(self.current_frame)  # Perform YOLOv8 inference

            self.adjustable_boxes = []  # To store boxes as [(corners, cls_id), ...]

            # Define unique colors for adjustable boxes
            adjustable_colors = {}
            adjustable_palette = [
                (128, 0, 0), (0, 128, 0), (0, 0, 128),
                (128, 128, 0), (128, 0, 128), (0, 128, 128)
            ]

            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # Extract bounding box in xyxy format
                    b_xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = b_xyxy

                    # Convert to four-corner representation
                    corners = [
                        [int(x1), int(y1)],  # top-left
                        [int(x2), int(y1)],  # top-right
                        [int(x1), int(y2)],  # bottom-left
                        [int(x2), int(y2)]   # bottom-right
                    ]

                    cls_id = int(box.cls)  # Class ID
                    self.adjustable_boxes.append((corners, cls_id))

                    # Assign unique colors for adjustable boxes
                    if cls_id not in adjustable_colors:
                        adjustable_colors[cls_id] = adjustable_palette[len(adjustable_colors) % len(adjustable_palette)]

                    print(f"Detected Box: {b_xyxy}, Class: {model.names[cls_id]}, Confidence: {box.conf.item():.2f}")

            # Enable interaction for the adjustable boxes
            self.enable_adjustable_boxes(adjustable_colors)


    def enable_adjustable_boxes(self, adjustable_colors):
        """Enable adjustable boxes for all detected objects with independent corners."""
        if self.current_frame is not None and self.adjustable_boxes:
            window_name = "Adjustable Boxes"
            cv2.namedWindow(window_name)
            cv2.setMouseCallback(window_name, self.handle_mouse_event)

            while True:
                frame = self.current_frame.copy()

                for corners, cls_id in self.adjustable_boxes:
                    color = adjustable_colors[cls_id]

                    # Draw lines between corners to form the box
                    # corners: [top-left, top-right, bottom-left, bottom-right]
                    # Indices: 0: top-left, 1: top-right, 2: bottom-left, 3: bottom-right
                    cv2.line(frame, tuple(corners[0]), tuple(corners[1]), color, 2)  # top edge
                    cv2.line(frame, tuple(corners[0]), tuple(corners[2]), color, 2)  # left edge
                    cv2.line(frame, tuple(corners[1]), tuple(corners[3]), color, 2)  # right edge
                    cv2.line(frame, tuple(corners[2]), tuple(corners[3]), color, 2)  # bottom edge

                    # Draw white circles at each corner
                    corner_radius = 6
                    for (cx, cy) in corners:
                        cv2.circle(frame, (cx, cy), corner_radius, (255, 255, 255), -1)

                    # Display the class name above the top-left corner
                    label = f"{model.names[cls_id]}"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.6
                    thickness = 2
                    text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                    text_x = corners[0][0]
                    text_y = max(corners[0][1] - 10, 0)
                    cv2.rectangle(
                        frame, 
                        (text_x, text_y - text_size[1] - 5), 
                        (text_x + text_size[0] + 5, text_y + 5), 
                        (255, 255, 255), 
                        -1
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
        """Handle mouse events for dragging the adjustable boxes. Each corner moves independently."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check each box's corners
            for i, (corners, cls_id) in enumerate(self.adjustable_boxes):
                for corner_idx, (cx, cy) in enumerate(corners):
                    if abs(x - cx) < 10 and abs(y - cy) < 10:
                        # Store which box and corner is being dragged
                        self.dragging = (i, corner_idx)
                        break

        elif event == cv2.EVENT_MOUSEMOVE and self.dragging:
            i, corner_idx = self.dragging
            corners, cls_id = self.adjustable_boxes[i]

            # Update only the dragged corner
            corners[corner_idx] = [x, y]

            self.adjustable_boxes[i] = (corners, cls_id)

        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = None




if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()  # Placeholder for a main window if needed
    setup_page = SetupPage(main_window)
    setup_page.show()
    sys.exit(app.exec_())
