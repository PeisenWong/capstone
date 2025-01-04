from PyQt5.QtWidgets import (
    QMainWindow, QScrollArea, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QLineEdit
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from gui.face_page import FacePage
from gui.object_page import ObjectPage
from gui.all import CombinedPage
from gui.setup import SetupPage
from gui.bluetooth_gui import BluetoothManager
from gui.test_page import TestPage
import cv2
from face_process import process_frame, draw_results, calculate_fps
from utils.controller import RobotController
from utils.database import MySQLHandler
import time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Face Recognition and Object Detection")
        self.userName = "Unknown"
        self.class_coordinates = []
        self.setGeometry(100, 100, 1200, 800)

        # Centralized camera capture object
        self.ip_cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.241.39:554/stream2")  # Use the first camera
        if not self.ip_cap.isOpened():
            # raise RuntimeError("Failed to open camera")
            print("Not able to open ip camera")
        
        self.robot = RobotController()
        self.db = MySQLHandler()
        self.db.connect()

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
        # self.test_page = TestPage(self)

        # Add pages to the stack
        self.stack.addWidget(self.auth_page)
        self.stack.addWidget(self.setup_page)    # index 0
        self.stack.addWidget(self.object_page)   # index 1
        # self.stack.addWidget(self.test_page)
        # self.stack.addWidget(self.combined_page) # index 2

        if self.db.zone_available():
            self.stack.setCurrentWidget(self.object_page)
        else:
            self.stack.setCurrentWidget(self.auth_page)

        # Wrap the stacked widget in a scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.stack)
        self.scroll_area.setWidgetResizable(True)  # Allow resizing of the stack to fit the scroll area

        # Create the navigation bar
        nav_bar = QFrame()
        nav_bar_layout = QHBoxLayout()

        btn_setup = QPushButton("Setup")
        btn_setup.setMinimumHeight(50)
        btn_face = QPushButton("Face Recognition")
        btn_object = QPushButton("Object Detection")
        btn_object.setMinimumHeight(50)
        btn_combined = QPushButton("Combined")
        btn_bluetooth = QPushButton("Bluetooth")

        nav_bar_layout.addWidget(btn_setup)
        # nav_bar_layout.addWidget(btn_face)
        nav_bar_layout.addWidget(btn_object)
        # nav_bar_layout.addWidget(btn_combined)
        # nav_bar_layout.addWidget(btn_bluetooth)

        nav_bar.setLayout(nav_bar_layout)

        # Connect the navigation buttons to the switching methods
        btn_setup.clicked.connect(self.authenticate_user)
        btn_face.clicked.connect(self.switch_to_face_recognition)
        btn_object.clicked.connect(self.switch_to_object_detection)
        btn_combined.clicked.connect(self.switch_to_combined_page)
        btn_bluetooth.clicked.connect(self.switch_to_bluetooth_page)

        # Create a main widget to hold both the scroll area and navigation
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(self.scroll_area)  # Add the scroll area containing the stack
        main_layout.addWidget(nav_bar)

        # Set the main_widget as the central widget
        self.setCentralWidget(main_widget)

        self.showMaximized()

    def setup_auth_page(self):
        """Set up the authentication page."""
        layout = QVBoxLayout()

        self.camera_label = QLabel("Face Recognition Stream")
        self.camera_label.setMaximumSize(640, 480)  # Set maximum size
        layout.addWidget(self.camera_label)

        self.status_label = QLabel("Waiting for authentication...")
        layout.addWidget(self.status_label)

        # Add password input field
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        layout.addWidget(self.password_input)

        # Add buttons for face recognition and password validation
        self.start_button = QPushButton("Start Face Recognition")
        self.start_button.setMinimumSize(200, 50)
        self.start_button.clicked.connect(self.start_face_recognition)
        layout.addWidget(self.start_button)

        self.validate_button = QPushButton("Validate Password")
        self.validate_button.setMinimumSize(200, 50)
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
        correct_password = "1234"  # Predefined password for demo

        if entered_password == correct_password:
            self.status_label.setText("Password correct! Redirecting to setup page...")
            self.userName = "admin"
            self.switch_to_setup_page()
            self.reset_page()
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
        frame = cv2.resize(frame, (400, 300))
        # Process frame (replace `process_frame` with your actual face recognition logic)
        processed_frame, is_authorized, user = process_frame(frame)
        display_frame = draw_results(processed_frame)

        if is_authorized:
            time.sleep(1)
            self.status_label.setText(f"Welcome, {user}!")
            self.userName = user
            self.timer.stop()
            self.cap.release()
            self.switch_to_setup_page()
            self.reset_page()
        else:
            self.status_label.setText("Authorizing...Go near to the camera")

        # Convert frame to QImage
        height, width, channel = display_frame.shape
        bytes_per_line = 3 * width
        qt_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

    def reset_page(self):
        self.camera_label.setText("Face Recognition Stream")
        self.password_input.clear()
        self.status_label.setText("Waiting for authentication")

    def switch_to_object_detection(self):
        """Switch to the object detection page."""
        self.stack.setCurrentWidget(self.object_page)

    def switch_to_face_recognition(self):
        """Switch back to the face recognition page."""
        self.stack.setCurrentWidget(self.face_page)

    def switch_to_combined_page(self):
        """Switch back to the combine page."""
        self.stack.setCurrentWidget(self.combined_page)

    def switch_to_setup_page(self):
        self.stack.setCurrentWidget(self.setup_page)

    def switch_to_bluetooth_page(self):
        self.stack.setCurrentWidget(self.bluetooth_page)
