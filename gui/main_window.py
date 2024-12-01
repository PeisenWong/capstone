from PyQt5.QtWidgets import QMainWindow, QStackedWidget
from gui.face_page import FacePage
from gui.object_page import ObjectPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Face Recognition and Object Detection")
        self.userName = "Unknown"
        self.setGeometry(100, 100, 1200, 800)

        # Stack widget to manage multiple pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Add pages to the stack
        self.face_page = FacePage(self)
        self.object_page = ObjectPage(self)

        self.stack.addWidget(self.face_page)
        self.stack.addWidget(self.object_page)

        # Set the initial page to the Face Recognition page
        self.stack.setCurrentWidget(self.face_page)  # Load FacePage first

    def switch_to_object_detection(self):
        """Switch to the object detection page."""
        self.stack.setCurrentWidget(self.object_page)

    def switch_to_face_recognition(self):
        """Switch back to the face recognition page."""
        self.stack.setCurrentWidget(self.face_page)
