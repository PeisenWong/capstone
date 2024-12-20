from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2
import time
import numpy as np
import tensorflow as tf
from ultralytics import YOLO


class TestPage(QWidget):
    def __init__(self, main_window, model="yolov8n-seg.tflite", width=640, height=480):
        super().__init__()
        self.main_window = main_window

        self.setWindowTitle("Responsive GUI with Camera and Detection")
        self.setGeometry(100, 100, 1200, 800)
        self.height = height
        self.width = width

        # Main layout
        layout = QVBoxLayout()

        # Camera label
        self.camera_label = QLabel("Camera Stream")
        self.camera_label.setMinimumSize(640, 480)
        layout.addWidget(self.camera_label)

        # Buttons
        self.start_button = QPushButton("Start Detection")
        self.start_button.clicked.connect(self.start_detection)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Detection")
        self.stop_button.clicked.connect(self.stop_detection)
        layout.addWidget(self.stop_button)

        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(QApplication.quit)
        layout.addWidget(self.quit_button)

        self.setLayout(layout)

        # Camera properties
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Load TFLite model
        self.interpreter = tf.lite.Interpreter(model_path=model)
        self.interpreter.allocate_tensors()

        # Get input and output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.running = False

    def preprocess(self, frame):
        """Preprocess the frame for YOLO model input."""
        input_shape = self.input_details[0]['shape'][1:3]  # Get input size (e.g., 640x640)
        frame_resized = cv2.resize(frame, (input_shape[1], input_shape[0]))
        frame_normalized = frame_resized / 255.0  # Normalize to [0, 1]
        return np.expand_dims(frame_normalized.astype(np.float32), axis=0)  # Add batch dimension

    def detect(self, frame):
        """Run detection on the frame."""
        input_data = self.preprocess(frame)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()

        # Get outputs (e.g., bounding boxes, class IDs, scores)
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])  # Bounding boxes
        class_ids = self.interpreter.get_tensor(self.output_details[1]['index'])  # Class IDs
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])  # Confidence scores
        return boxes, class_ids, scores

    def start_detection(self):
        """Start the camera and detection."""
        if not self.cap:
            self.cap = cv2.VideoCapture(0)  # Replace 0 with your camera index or IP camera stream
        if not self.timer.isActive():
            self.running = True
            self.timer.start(30)

    def stop_detection(self):
        """Stop the camera and detection."""
        if self.timer.isActive():
            self.running = False
            self.timer.stop()
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.camera_label.clear()

    def update_frame(self):
        """Read frame, run detection, and update the GUI."""
        if not self.cap or not self.cap.isOpened():
            self.camera_label.setText("Failed to read camera frame.")
            return

        ret, frame = self.cap.read()
        if not ret:
            self.camera_label.setText("Failed to capture frame.")
            return

        # Object detection
        if self.running:
            boxes, class_ids, scores = self.detect(frame)
            frame = self.draw_detections(frame, boxes, class_ids, scores)

        # Convert to QImage and display in QLabel
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        q_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(q_img))

    def draw_detections(self, frame, boxes, class_ids, scores, threshold=0.3):
        """Draw detections on the frame."""
        for box, class_id, score in zip(boxes, class_ids, scores):
            if score > threshold:
                # Extract box coordinates and scale them to the frame size
                ymin, xmin, ymax, xmax = box
                h, w, _ = frame.shape
                xmin, xmax, ymin, ymax = int(xmin * w), int(xmax * w), int(ymin * h), int(ymax * h)

                # Draw bounding box and label
                label = f"ID: {int(class_id)} | {score:.2f}"
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                cv2.putText(frame, label, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        return frame
