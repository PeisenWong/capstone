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
model = YOLO("models/trained.pt")

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

        self.camera_label = QLabel("Streaming RTSP Camera")
        self.camera_label.setFixedSize(400, 300)
        first_col_layout.addWidget(self.camera_label)

        self.instructions_label = QLabel("Instructions: Ensure proper network connectivity for smooth streaming.")
        self.instructions_label.setStyleSheet("font-size: 14px; color: gray;")
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

        second_col_layout.addLayout(button_row_layout)

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

            print("Coordinates saved to main_window.class_coordinates:")
            for item in self.main_window.class_coordinates:
                print(item)
        else:
            print("No boxes to confirm.")


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
                (128, 0, 0), (0, 128, 0), (0, 0, 128),
                (128, 128, 0), (128, 0, 128), (0, 128, 128)
            ]

            # Original frame dimensions
            h_original, w_original = self.current_frame.shape[:2]
            target_w, target_h = 400, 300  # Desired display size

            # Process detections
            for r in results:
                for box in r.boxes:
                    b_xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = b_xyxy
                    cls_id = int(box.cls)

                    # Convert to four-corner representation
                    corners = [
                        [x1, y1],  # top-left
                        [x2, y1],  # top-right
                        [x1, y2],  # bottom-left
                        [x2, y2]   # bottom-right
                    ]

                    # Assign unique colors for adjustable boxes if not assigned
                    if cls_id not in adjustable_colors:
                        adjustable_colors[cls_id] = adjustable_palette[len(adjustable_colors) % len(adjustable_palette)]

                    print(f"Detected Box: {b_xyxy}, Class: {model.names[cls_id]}, Confidence: {box.conf.item():.2f}")

                    adjustable_boxes.append((corners, cls_id))

            # Resize the frame for display
            displayed_frame = cv2.resize(self.current_frame.copy(), (target_w, target_h))

            # Scale boxes to the displayed frame size
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

            # Update the captured_image_label with scaled boxes
            self.captured_image_label.set_data(displayed_frame, scaled_boxes, adjustable_colors, model.names)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()  # Placeholder for a main window if needed
    setup_page = SetupPage(main_window)
    setup_page.show()
    sys.exit(app.exec_())
