import cv2
import os
from ultralytics import YOLO
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtCore import QTimer, Qt, QPoint
import sys

# Load YOLOv8 model
model = YOLO("models/capstone_model_2.pt")

class AdjustableImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.adjustable_boxes = []  # [([ [x_tl,y_tl], [x_tr,y_tr], [x_bl,y_bl], [x_br,y_br] ], cls_id), ...]
        self.adjustable_colors = {}
        self.dragging = None
        self.captured_image = None
        self.corner_radius = 6
        self.font = QFont("Arial", 10)

    def set_data(self, image, adjustable_boxes, adjustable_colors, class_names):
        """
        Set the image and boxes data.
        image: BGR frame (numpy array)
        adjustable_boxes: list of corners and cls_ids
        adjustable_colors: dict mapping class_id to (B,G,R)
        class_names: name list from model
        """
        self.captured_image = image
        self.adjustable_boxes = adjustable_boxes
        self.adjustable_colors = adjustable_colors
        self.class_names = class_names
        self.update_display()

    def update_display(self):
        """Convert the captured image to QPixmap and update the label."""
        if self.captured_image is not None:
            frame_rgb = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.setPixmap(QPixmap.fromImage(qt_image))
        else:
            self.setText("Captured Frame")
        self.repaint()  # trigger paintEvent

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.captured_image is None or not self.adjustable_boxes:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw boxes
        for corners, cls_id in self.adjustable_boxes:
            color = self.adjustable_colors[cls_id]
            pen = QPen(QColor(color[2], color[1], color[0]), 2)  # Convert BGR to RGB
            painter.setPen(pen)

            # Draw lines between corners
            # corners: [tl, tr, bl, br]
            tl = QPoint(corners[0][0], corners[0][1])
            tr = QPoint(corners[1][0], corners[1][1])
            bl = QPoint(corners[2][0], corners[2][1])
            br = QPoint(corners[3][0], corners[3][1])

            painter.drawLine(tl, tr)  # top edge
            painter.drawLine(tl, bl)  # left edge
            painter.drawLine(tr, br)  # right edge
            painter.drawLine(bl, br)  # bottom edge

            # Draw corner circles (white)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(tl, self.corner_radius, self.corner_radius)
            painter.drawEllipse(tr, self.corner_radius, self.corner_radius)
            painter.drawEllipse(bl, self.corner_radius, self.corner_radius)
            painter.drawEllipse(br, self.corner_radius, self.corner_radius)

            # Display class name above top-left corner
            painter.setPen(Qt.black)
            painter.setFont(self.font)
            label = f"{self.class_names[cls_id]}"
            text_rect = painter.boundingRect(0, 0, 0, 0, Qt.AlignLeft, label)

            text_x = tl.x()
            text_y = tl.y() - 10
            if text_y < text_rect.height():
                text_y = tl.y() + text_rect.height() + 10  # move below if no space above

            # Draw label background
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRect(text_x, text_y - text_rect.height(), text_rect.width() + 6, text_rect.height() + 6)
            # Draw label text
            painter.setPen(Qt.black)
            painter.drawText(text_x + 3, text_y, label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.captured_image is not None and self.adjustable_boxes:
            x, y = event.x(), event.y()
            # Check if near a corner
            for i, (corners, cls_id) in enumerate(self.adjustable_boxes):
                for corner_idx, (cx, cy) in enumerate(corners):
                    if abs(x - cx) < 10 and abs(y - cy) < 10:
                        self.dragging = (i, corner_idx)
                        break
                if self.dragging is not None:
                    break

    def mouseMoveEvent(self, event):
        if self.dragging is not None:
            i, corner_idx = self.dragging
            corners, cls_id = self.adjustable_boxes[i]

            # Clamp coordinates to the range [0, 399] for x and [0, 299] for y
            # This ensures the corner stays within the 400x300 image area.
            new_x = max(0, min(event.x(), 399))
            new_y = max(0, min(event.y(), 299))

            corners[corner_idx] = [new_x, new_y]
            self.adjustable_boxes[i] = (corners, cls_id)
            self.update_display()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = None


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
        self.user_label = QLabel(f"Welcome {self.main_window.userName}")
        self.user_label.setMaximumHeight(30)
        first_col_layout.addWidget(self.user_label)

        self.camera_label = QLabel("Streaming RTSP Camera")
        self.camera_label.setFixedSize(400, 300)
        first_col_layout.addWidget(self.camera_label)

        self.instructions_label = QLabel("Instructions: Ensure proper network connectivity \nfor smooth streaming.")
        self.instructions_label.setStyleSheet("font-size: 20px; color: gray;")
        first_col_layout.addWidget(self.instructions_label)

        # Second column layout: Captured image and buttons
        second_col_layout = QVBoxLayout()

        # Image display (first row)
        self.captured_image_label = AdjustableImageLabel()
        self.captured_image_label.setText("Captured Image")
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

        self.status_label = QLabel("Draw the zone carefully based on the floor")
        self.status_label.setMaximumHeight(30)
        self.status_label.setStyleSheet("font-size: 20px; color: black;")

        second_col_layout.addLayout(button_row_layout)
        second_col_layout.addWidget(self.status_label)

        # Add layouts to the main layout
        main_layout.addLayout(first_col_layout)
        main_layout.addLayout(second_col_layout)

        self.setLayout(main_layout)

        # Camera properties
        # self.rtsp_url = rtsp_url
        # self.cap = cv2.VideoCapture(self.rtsp_url)

        # if not self.cap.isOpened():
        #     print("Error: Unable to access the RTSP camera stream.")
        #     sys.exit()

        # Timer for updating camera stream
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stream)
        self.timer.start(30)  # Update every 30 ms

        self.current_frame = None

    def showEvent(self, event):
        self.user_label.setText(f"Welcome {self.main_window.userName}")
        self.clear()

    def confirm(self):
        """On confirm, store the adjusted box coordinates and their classes in main_window."""
        if self.captured_image_label is not None and self.captured_image_label.adjustable_boxes:
            # Clear previously stored coordinates if needed
            self.main_window.class_coordinates = []

            for corners, cls_id in self.captured_image_label.adjustable_boxes:
                class_name = self.captured_image_label.class_names[cls_id]
                # Append a dictionary or tuple with all relevant info
                self.main_window.class_coordinates.append({
                    'class_name': class_name,
                    'corners': {
                        'top_left': (corners[0][0], corners[0][1]),
                        'top_right': (corners[1][0], corners[1][1]),
                        'bottom_left': (corners[2][0], corners[2][1]),
                        'bottom_right': (corners[3][0], corners[3][1])
                    }
                })
            """
            Save the coordinates for "slow_zone" and "stop_zone" to the database.
            """
            # Prepare the data for the database
            stop_zone = next((zone for zone in self.main_window.class_coordinates if zone['class_name'] == "stop_zone"), None)
            slow_zone = next((zone for zone in self.main_window.class_coordinates if zone['class_name'] == "slow_zone"), None)

            if not stop_zone or not slow_zone:
                self.status_label.setText("Error: Both 'stop_zone' and 'slow_zone' must be defined.")
                return

            # Extract the coordinates for both zones
            stop_corners = stop_zone['corners']
            slow_corners = slow_zone['corners']

            data = (
                1,  # robot_id
                stop_corners['top_left'][0], stop_corners['top_left'][1],
                stop_corners['top_right'][0], stop_corners['top_right'][1],
                stop_corners['bottom_left'][0], stop_corners['bottom_left'][1],
                stop_corners['bottom_right'][0], stop_corners['bottom_right'][1],
                slow_corners['top_left'][0], slow_corners['top_left'][1],
                slow_corners['top_right'][0], slow_corners['top_right'][1],
                slow_corners['bottom_left'][0], slow_corners['bottom_left'][1],
                slow_corners['bottom_right'][0], slow_corners['bottom_right'][1]
            )

            # Call the insert_zone method
            try:
                self.main_window.db.insert_zone(data)
            except Exception as e:
                print(f"Error saving zones to the database: {e}")

            self.clear()
            self.main_window.switch_to_object_detection()
        else:
            self.status_label.setText("No boxes to confirm.")


    def clear(self):
        self.captured_image_label.captured_image = None
        self.captured_image_label.adjustable_boxes = []
        self.captured_image_label.update_display()

    def update_stream(self):
        """Update the camera stream in the first column."""
        ret, frame = self.main_window.ip_cap.read()
        if not ret:
            self.camera_label.setText("Failed to fetch camera stream!")
            return

        # Resize and display the frame
        display_frame = cv2.resize(frame, (400, 300))
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = channel * width
        qt_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

        # Save the current frame (original resolution) for capture purposes
        self.current_frame = frame

    def capture_callback(self):
        """Capture the current frame, run YOLO, and show adjustable boxes in the captured_image_label."""
        if self.current_frame is not None:
            # Run YOLO model on the captured frame
            results = model.predict(self.current_frame)

            adjustable_boxes = []
            adjustable_colors = {}
            adjustable_palette = [
                (0, 255, 0),  # Red for stop_zone
                (255, 0, 0)   # Green for slow_zone
            ]

            # Variables for highest-confidence detections
            highest_confidence_stop_zone = None
            highest_confidence_slow_zone = None

            # Original frame dimensions
            h_original, w_original = self.current_frame.shape[:2]
            target_w, target_h = 400, 300  # Desired display size in the UI

            # Process detections
            for r in results:
                for box in r.boxes:
                    b_xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = b_xyxy
                    cls_id = int(box.cls)
                    confidence = box.conf.item()

                    class_name = model.names[cls_id]

                    # Keep only the box with the highest confidence for each zone
                    if class_name == "stop_zone":
                        if not highest_confidence_stop_zone or confidence > highest_confidence_stop_zone[2]:
                            highest_confidence_stop_zone = (b_xyxy, cls_id, confidence)
                    elif class_name == "slow_zone":
                        if not highest_confidence_slow_zone or confidence > highest_confidence_slow_zone[2]:
                            highest_confidence_slow_zone = (b_xyxy, cls_id, confidence)

            # If no stop_zone detected, manually create a smaller bounding box in the center
            if not highest_confidence_stop_zone:
                center_x, center_y = w_original // 2, h_original // 2
                width, height = 50, 50
                highest_confidence_stop_zone = (
                    [center_x - width, center_y - height, center_x + width, center_y + height],
                    1,  # cls_id for stop_zone
                    1.0
                )

            # If no slow_zone detected, manually create a larger bounding box in the center
            if not highest_confidence_slow_zone:
                center_x, center_y = w_original // 2, h_original // 2
                width, height = 100, 100
                highest_confidence_slow_zone = (
                    [center_x - width, center_y - height, center_x + width, center_y + height],
                    0,  # cls_id for slow_zone
                    1.0
                )

            # Combine the final bounding boxes into a list
            final_zones = [highest_confidence_stop_zone, highest_confidence_slow_zone]

            # Create the adjustable boxes array
            for zone, color in zip(final_zones, adjustable_palette):
                b_xyxy, cls_id, confidence = zone
                x1, y1, x2, y2 = b_xyxy

                corners = [
                    [x1, y1],  # top-left
                    [x2, y1],  # top-right
                    [x1, y2],  # bottom-left
                    [x2, y2]   # bottom-right
                ]

                adjustable_boxes.append((corners, cls_id))
                adjustable_colors[cls_id] = color

            # Resize the original frame for display
            displayed_frame = cv2.resize(self.current_frame.copy(), (target_w, target_h))

            # Scale boxes from original size to displayed size
            scale_x = target_w / w_original
            scale_y = target_h / h_original

            scaled_boxes = []
            for corners, cls_id in adjustable_boxes:
                scaled_corners = []
                for (cx, cy) in corners:
                    sx = int(cx * scale_x)
                    sy = int(cy * scale_y)
                    scaled_corners.append([sx, sy])
                scaled_boxes.append((scaled_corners, cls_id))

            # Update the label to show the final bounding boxes (stop_zone & slow_zone)
            self.captured_image_label.set_data(displayed_frame, scaled_boxes, adjustable_colors, model.names)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()  # Placeholder for a main window if needed
    setup_page = SetupPage(main_window)
    setup_page.show()
    sys.exit(app.exec_())
