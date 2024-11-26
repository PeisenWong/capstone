from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2
from mediapipe.tasks import python, vision
from utils.visualize import visualize


class ObjectPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # Layout and widgets
        self.layout = QVBoxLayout()
        self.camera_label = QLabel("Object Detection Stream")
        self.layout.addWidget(self.camera_label)

        self.back_button = QPushButton("Back to Face Recognition")
        self.back_button.clicked.connect(self.switch_to_face_recognition)
        self.layout.addWidget(self.back_button)

        self.setLayout(self.layout)

        # Camera and timer
        self.cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.113.39:554/stream2")
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Object detection model
        self.detector = self.initialize_detector()

        self.timer.start(30)

    def initialize_detector(self):
        model_path = "efficientdet_lite0.tflite"
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.ObjectDetectorOptions(base_options=base_options, running_mode=vision.RunningMode.LIVE_STREAM)
        return vision.ObjectDetector.create_from_options(options)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Run object detection
        detection_frame = visualize(frame, None)

        # Display in QLabel
        height, width, channel = detection_frame.shape
        bytes_per_line = channel * width
        qt_image = QImage(detection_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

    def switch_to_face_recognition(self):
        self.cap.release()
        self.timer.stop()
        self.main_window.stack.setCurrentWidget(self.main_window.face_page)
