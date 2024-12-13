import cv2
from ultralytics import YOLO

# Load YOLOv8 model
model = YOLO("models/trained.pt")

# Set up the IP camera using cv2.VideoCapture with RTSP stream
rtsp_url = "rtsp://peisen:peisen@192.168.113.39:554/stream2"
cap = cv2.VideoCapture(rtsp_url)

# Optionally, set the desired frame width and height
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Error: Unable to access the IP camera stream.")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Unable to read frame from IP camera stream.")
        break

    # Run YOLO model on the captured frame and store the results
    results = model(frame, iou=0.5)

    # Output the visual detection data and draw this on our camera preview window
    annotated_frame = results[0].plot()

    # Get inference time
    inference_time = results[0].speed['inference']
    fps = 1000 / inference_time  # Convert to FPS
    text = f'FPS: {fps:.1f}'

    # Define font and position for FPS display
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 1, 2)[0]
    text_x = annotated_frame.shape[1] - text_size[0] - 10  # 10 pixels from the right
    text_y = text_size[1] + 10  # 10 pixels from the top

    # Draw the FPS text on the annotated frame
    cv2.putText(annotated_frame, text, (text_x, text_y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Display the resulting frame
    cv2.imshow("Camera", annotated_frame)

    # Exit the program if 'q' is pressed
    if cv2.waitKey(1) == ord("q"):
        break

# Release the video capture object and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
