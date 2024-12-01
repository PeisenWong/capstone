import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from face_process import process_frame, draw_results, calculate_fps

class FacePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.userName = "Unknown"

        # Layout and widgets
        self.layout = QVBoxLayout()
        self.camera_label = QLabel("Face Recognition Stream")
        self.layout.addWidget(self.camera_label)

        self.status_label = QLabel("Waiting for authorization...")
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)

        # Camera and timers
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Delay timer for showing authorization message
        self.delay_timer = QTimer()
        self.delay_timer.timeout.connect(self.switch_to_object_detection)

    def showEvent(self, event):
        """Triggered when the FacePage is shown."""
        super().showEvent(event)
        # Reset the page state
        self.reset_page()
        # Reinitialize the camera
        self.cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.113.39:554/stream2")
        if not self.cap.isOpened():
            self.status_label.setText("Error: Unable to access camera.")
            return
        # Start the frame update timer
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.setText("Error: Failed to read frame.")
            return

        # Process frame for face recognition
        processed_frame, is_authorized, user = process_frame(frame)
        display_frame = draw_results(processed_frame)

        # Calculate and update FPS
        current_fps = calculate_fps()

        # Attach FPS counter to the text and boxes
        cv2.putText(display_frame, f"FPS: {current_fps:.1f}", (display_frame.shape[1] - 150, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Convert frame for PyQt display
        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        qt_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

        # Check if authorized
        if is_authorized:
            self.userName = user
            self.main_window.userName = user
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.status_label.setText(f"Authorization done for {user}.... Redirecting...")
            self.delay_timer.start(2000)  # 2-second delay before switching

    def stop_recognition(self):
        """Stop the recognition process."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.timer.stop()
        self.delay_timer.stop()

    def switch_to_object_detection(self):
        """Switch to the ObjectPage."""
        self.stop_recognition()
        self.reset_page()
        self.main_window.switch_to_object_detection()

    def reset_page(self):
        """Reset the page for future use."""
        self.status_label.setText("Waiting for authorization...")
        self.camera_label.setText("Face Recognition Stream")
        if self.cap:
            self.cap.release()
            self.cap = None
        self.timer.stop()
        self.delay_timer.stop()
