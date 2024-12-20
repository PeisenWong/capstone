import cv2
from ultralytics import YOLO

ip_cap = cv2.VideoCapture("rtsp://peisen:peisen@192.168.113.39:554/stream2")  # Use the first camera
ip_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
ip_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not ip_cap.isOpened():
    raise RuntimeError("Failed to open camera")

# Load our YOLO11 model
model = YOLO("../models/yolo11n-pose.pt")

while True:
    # Capture a frame from the camera
    success, frame = ip_cap.read()
    
    # Run YOLO model on the captured frame and store the results
    results = model.predict(frame, imgsz = 640)

    # Output the visual detection data, we will draw this on our camera preview window
    annotated_frame = results[0].plot()
    
    # Get inference time
    inference_time = results[0].speed['inference']
    fps = 1000 / inference_time  # Convert to milliseconds
    text = f'FPS: {fps:.1f}'

    # Define font and position
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 1,2)[0]
    text_x = annotated_frame.shape[1] - text_size[0] - 10  # 10 pixels from the right
    text_y = text_size[1] + 10  # 10 pixels from the top

    # Draw the text on the annotated frame
    cv2.putText(annotated_frame, text, (text_x, text_y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Display the resulting frame
    cv2.imshow("Camera", annotated_frame)

    # Exit the program if q is pressed
    if cv2.waitKey(1) == ord("q"):
        break

# Close all windows
cv2.destroyAllWindows()