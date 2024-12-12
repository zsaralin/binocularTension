import pyrealsense2 as rs
import cv2
import numpy as np
from ultralytics import YOLO

# Load the YOLOv11 model
model = YOLO("../yolo/yolo11n.pt")  # Replace with your custom model path

def draw_bounding_boxes(image, detections):
    """
    Draw bounding boxes on the image.
    :param image: The input image.
    :param detections: List of detections from the YOLO model.
    :return: Image with bounding boxes drawn.
    """
    for result in detections:
        boxes = result.boxes
        for box in boxes:
            # Extract box coordinates and confidence
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
            confidence = box.conf[0].item()  # Confidence score
            class_id = box.cls[0].item()  # Class ID

            # Draw the bounding box
            color = (0, 255, 0)  # Green color for the box
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            # Add label and confidence
            label = f"ID: {int(class_id)}, Conf: {confidence:.2f}"
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return image

def main():
    # Configure the RealSense pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # Start the RealSense pipeline
    pipeline.start(config)

    try:
        while True:
            # Wait for a frame
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            # Convert RealSense frame to numpy array
            frame = np.asanyarray(color_frame.get_data())

            # Run YOLO inference
            results = model(frame, stream=True)

            # Draw bounding boxes on the frame
            frame_with_boxes = draw_bounding_boxes(frame, results)

            # Display the output
            cv2.imshow("YOLOv11 Detection with RealSense", frame_with_boxes)

            # Exit on pressing 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Stop the pipeline
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
