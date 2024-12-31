from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QLineEdit
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from gui.face_page import FacePage
from gui.object_page import ObjectPage
from gui.all import CombinedPage
from gui.setup import SetupPage
from gui.bluetooth_gui import BluetoothManager
import cv2
from face_process import process_frame, draw_results
from utils.controller import RobotController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Face Recognition and Object Detection")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()

        self.userName = "Unknown"
        self.class_coordinates = []

        # Centralized camera capture object
        self.ip_cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.241.39:554/stream2")
        if not self.ip_cap.isOpened():
            print("Not able to open IP camera")

        self.robot = RobotController()

        # Create the stacked widget
        self.stack = QStackedWidget()

        # Instantiate pages
        self.auth_page = QWidget()
        self.setup_auth_page()

        self.face_page = FacePage(self)
        self.object_page = ObjectPage(self)
        self.combined_page = CombinedPage(self)
        self.setup_page = SetupPage(self)
        self.bluetooth_page = BluetoothManager(self)

        # Add pages to the stack
        self.stack.addWidget(self.auth_page)
        self.stack.addWidget(self.setup_page)
        self.stack.addWidget(self.object_page)

        self.stack.setCurrentWidget(self.auth_page)

        # Create the navigation bar
        nav_bar = QFrame()
        nav_bar_layout = QHBoxLayout()
        nav_bar_layout.setSpacing(10)
        nav_bar_layout.setContentsMargins(5, 5, 5, 5)

        btn_setup = QPushButton("Setup")
        btn_object = QPushButton("Object Detection")

        btn_setup.setSizePolicy(QPushButton.MinimumExpanding, QPushButton.MinimumExpanding)
        btn_object.setSizePolicy(QPushButton.MinimumExpanding, QPushButton.MinimumExpanding)

        nav_bar_layout.addWidget(btn_setup)
        nav_bar_layout.addWidget(btn_object)
        nav_bar.setLayout(nav_bar_layout)

        # Connect the navigation buttons to switching methods
        btn_setup.clicked.connect(self.authenticate_user)
        btn_object.clicked.connect(self.switch_to_object_detection)

        # Main layout combining the stack and navigation bar
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        main_layout.addWidget(self.stack)
        main_layout.addWidget(nav_bar)

        self.setCentralWidget(main_widget)

    def setup_auth_page(self):
        """Set up the authentication page."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.camera_label = QLabel("Face Recognition Stream")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setSizePolicy(QLabel.MinimumExpanding, QLabel.MinimumExpanding)
        layout.addWidget(self.camera_label)

        self.status_label = QLabel("Waiting for authentication...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Add password input field
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        layout.addWidget(self.password_input)

        # Add buttons for face recognition and password validation
        self.start_button = QPushButton("Start Face Recognition")
        self.start_button.clicked.connect(self.start_face_recognition)
        layout.addWidget(self.start_button)

        self.validate_button = QPushButton("Validate Password")
        self.validate_button.clicked.connect(self.validate_password)
        layout.addWidget(self.validate_button)

        self.auth_page.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_face_recognition_frame)

    def authenticate_user(self):
        """Switch to the authentication page."""
        self.stack.setCurrentWidget(self.auth_page)

    def validate_password(self):
        """Validate the password input."""
        entered_password = self.password_input.text()
        correct_password = "1234"

        if entered_password == correct_password:
            self.status_label.setText("Password correct! Redirecting to setup page...")
            self.switch_to_setup_page()
        else:
            self.status_label.setText("Incorrect password. Please try again.")

    def start_face_recognition(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_label.setText("Error: Unable to access camera.")
            return
        self.timer.start(30)

    def update_face_recognition_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.setText("Error: Failed to read frame.")
            return

        processed_frame, is_authorized, user = process_frame(frame)
        display_frame = draw_results(processed_frame)

        if is_authorized:
            self.status_label.setText(f"Welcome, {user}!")
            # self.userName = user
            # self.timer.stop()
            # self.cap.release()
            # self.switch_to_setup_page()
        else:
            self.status_label.setText("Authorizing...Go near to the camera")

        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        qt_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

    def switch_to_object_detection(self):
        """Switch to the object detection page."""
        self.stack.setCurrentWidget(self.object_page)

    def switch_to_setup_page(self):
        """Switch to the setup page."""
        self.stack.setCurrentWidget(self.setup_page)

            
