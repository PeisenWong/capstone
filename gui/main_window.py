from PyQt5.QtWidgets import (
    QMainWindow, QScrollArea, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
)
from gui.face_page import FacePage
from gui.object_page import ObjectPage
from gui.all import CombinedPage
from gui.setup import SetupPage
from gui.bluetooth_gui import BluetoothManager
from gui.test_page import TestPage
import cv2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Face Recognition and Object Detection")
        self.userName = "Unknown"
        self.class_coordinates = []
        self.setGeometry(100, 100, 1200, 800)

        # Centralized camera capture object
        self.ip_cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.113.39:554/stream2")  # Use the first camera
        if not self.ip_cap.isOpened():
            raise RuntimeError("Failed to open camera")

        # Create the stacked widget
        self.stack = QStackedWidget()

        # Instantiate pages
        self.face_page = FacePage(self)
        self.object_page = ObjectPage(self)
        self.combined_page = CombinedPage(self)
        self.setup_page = SetupPage(self)
        self.bluetooth_page = BluetoothManager(self)
        # self.test_page = TestPage(self)

        # Add pages to the stack
        self.stack.addWidget(self.setup_page)    # index 0
        self.stack.addWidget(self.object_page)   # index 1
        # self.stack.addWidget(self.test_page)
        self.stack.addWidget(self.combined_page) # index 2

        self.stack.setCurrentWidget(self.setup_page)

        # Wrap the stacked widget in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.stack)
        scroll_area.setWidgetResizable(True)  # Allow resizing of the stack to fit the scroll area

        # Create the navigation bar
        nav_bar = QFrame()
        nav_bar_layout = QHBoxLayout()

        btn_setup = QPushButton("Setup")
        btn_face = QPushButton("Face Recognition")
        btn_object = QPushButton("Object Detection")
        btn_combined = QPushButton("Combined")
        btn_bluetooth = QPushButton("Bluetooth")

        nav_bar_layout.addWidget(btn_setup)
        nav_bar_layout.addWidget(btn_face)
        nav_bar_layout.addWidget(btn_object)
        nav_bar_layout.addWidget(btn_combined)
        nav_bar_layout.addWidget(btn_bluetooth)

        nav_bar.setLayout(nav_bar_layout)

        # Connect the navigation buttons to the switching methods
        btn_setup.clicked.connect(self.switch_to_setup_page)
        btn_face.clicked.connect(self.switch_to_face_recognition)
        btn_object.clicked.connect(self.switch_to_object_detection)
        btn_combined.clicked.connect(self.switch_to_combined_page)
        btn_bluetooth.clicked.connect(self.switch_to_bluetooth_page)

        # Create a main widget to hold both the scroll area and navigation
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(scroll_area)  # Add the scroll area containing the stack
        main_layout.addWidget(nav_bar)

        # Set the main_widget as the central widget
        self.setCentralWidget(main_widget)

        self.showMaximized()

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
