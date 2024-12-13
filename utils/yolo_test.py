import cv2
import os
from ultralytics import YOLO

# Load YOLOv8 model
model = YOLO("models/trained.pt")

# Specify the folder containing the images
image_folder = "datasets/data/9_Dec"  # Replace with the path to your image folder
output_folder = "datasets/data/9_Dec_Outputs"  # Replace with the path to save annotated images

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Loop through each image in the folder
for image_name in os.listdir(image_folder):
    image_path = os.path.join(image_folder, image_name)

    # Ensure the file is an image
    if not image_name.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    # Read the image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Unable to read image {image_path}. Skipping...")
        continue

    # Run YOLO model on the image
    results = model(frame)

    # Output the visual detection data and draw this on the image
    annotated_frame = results[0].plot()

    # Save the annotated image to the output folder
    output_path = os.path.join(output_folder, f"annotated_{image_name}")
    cv2.imwrite(output_path, annotated_frame)

    # Optional: Display the annotated image (comment out if running on a headless server)
    cv2.imshow("Annotated Image", annotated_frame)
    if cv2.waitKey(1) == ord("q"):
        break

cv2.destroyAllWindows()
print(f"Inference completed. Annotated images are saved in '{output_folder}'.")
