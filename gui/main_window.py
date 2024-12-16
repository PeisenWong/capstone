from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
)
from gui.face_page import FacePage
from gui.object_page import ObjectPage
from gui.all import CombinedPage
from gui.setup import SetupPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Face Recognition and Object Detection")
        self.userName = "Unknown"
        self.setGeometry(100, 100, 1200, 800)

        # Create the stacked widget
        self.stack = QStackedWidget()

        # Instantiate pages
        self.face_page = FacePage(self)
        self.object_page = ObjectPage(self)
        self.combined_page = CombinedPage(self)
        self.setup_page = SetupPage(self)

        # Add pages to the stack
        self.stack.addWidget(self.setup_page)    # index 0
        self.stack.addWidget(self.face_page)     # index 1
        self.stack.addWidget(self.object_page)   # index 2
        self.stack.addWidget(self.combined_page) # index 3

        self.stack.setCurrentWidget(self.setup_page)

        # Create the navigation bar
        nav_bar = QFrame()
        nav_bar_layout = QHBoxLayout()

        btn_setup = QPushButton("Setup")
        btn_face = QPushButton("Face Recognition")
        btn_object = QPushButton("Object Detection")
        btn_combined = QPushButton("Combined")

        nav_bar_layout.addWidget(btn_setup)
        nav_bar_layout.addWidget(btn_face)
        nav_bar_layout.addWidget(btn_object)
        nav_bar_layout.addWidget(btn_combined)

        nav_bar.setLayout(nav_bar_layout)

        # Connect the navigation buttons to the switching methods
        btn_setup.clicked.connect(self.switch_to_setup_page)
        btn_face.clicked.connect(self.switch_to_face_recognition)
        btn_object.clicked.connect(self.switch_to_object_detection)
        btn_combined.clicked.connect(self.switch_to_combined_page)

        # Create a main widget to hold both the stack and navigation
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(self.stack)
        main_layout.addWidget(nav_bar)

        # Set the main_widget as the central widget
        self.setCentralWidget(main_widget)

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
