from ultralytics import YOLO

# Load a YOLO11n PyTorch model
model = YOLO("../models/yolo11n-pose.pt")

# Export the model to NCNN format
model.export(format="ncnn", imgsz=640)  # creates 'yolov11n-pose_ncnn_model'