import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO
from inference import get_model
import supervision as sv
from norfair import Tracker, Detection

# Load YOLO Model
# yolo_model = YOLO("./yolo/yolo11n.pt")  # Change to your actual YOLO model path

# # Load the Overhead Tracker Model (Roboflow API)
# API_KEY = "PfGednJlJMw5JDXfKw9e"  # Replace with your actual API key
# overhead_model = get_model(model_id="overhead-people-tracking/1", api_key=API_KEY)
# prediction = overhead_model.download()

import roboflow

rf = roboflow.Roboflow(api_key="PfGednJlJMw5JDXfKw9e")
model = rf.workspace().project("overhead-people-tracking").version("1").model
prediction = model.download()
# Configure the RealSense pipeline
# pipeline = rs.pipeline()
# config = rs.config()
# config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# # Start streaming
# pipeline.start(config)

# # Initialize Norfair Trackers
# yolo_tracker = Tracker(distance_function="euclidean", distance_threshold=100, hit_counter_max=5)
# overhead_tracker = Tracker(distance_function="euclidean", distance_threshold=100, hit_counter_max=5)

# # Initialize Supervision annotators
# bounding_box_annotator = sv.BoxAnnotator()
# label_annotator = sv.LabelAnnotator()

# try:
#     while True:
#         # Wait for frames from RealSense
#         frames = pipeline.wait_for_frames()
#         color_frame = frames.get_color_frame()
#         if not color_frame:
#             continue

#         # Convert RealSense frame to OpenCV format
#         frame = np.asanyarray(color_frame.get_data())

#         ###### 📌 Run YOLO and Overhead Tracker at the Same Time ######
#         yolo_results = yolo_model(frame, stream=True)
#         overhead_results = overhead_model.infer(frame)  # Roboflow API inference returns a LIST

#         ###### 📌 Convert YOLO Detections to Norfair Format ######
#         yolo_detections, yolo_bbs = [], []
#         for result in yolo_results:
#             for box in result.boxes:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
#                 conf = box.conf[0].item()
#                 if conf > 0.5:
#                     center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
#                     width, height = x2 - x1, y2 - y1
#                     yolo_detections.append(Detection(points=center, scores=np.array([conf]), 
#                                                      data={"width": width, "height": height, "is_yolo": True}))
#                     yolo_bbs.append((x1, y1, x2, y2))

#         ###### 📌 Convert Overhead Tracker Detections to Norfair Format ######
#         overhead_detections, overhead_bbs = [], []
#         if overhead_results:  # Ensure there's valid data
#             sv_detections = sv.Detections.from_inference(overhead_results[0])  # Extract first element
#             for detection in sv_detections:
#                 print(detection)
#                 x1, y1, x2, y2 = map(int, detection[0])  # Extract bounding box
#                 conf = detection[2]  # Extract confidence
#                 if conf > 0.5:
#                     center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
#                     width, height = x2 - x1, y2 - y1
#                     overhead_detections.append(Detection(points=center, scores=np.array([conf]), 
#                                                          data={"width": width, "height": height, "is_overhead": True}))
#                     overhead_bbs.append((x1, y1, x2, y2))  # Store bounding boxes

#         ###### 📌 Update Norfair Trackers ######
#         yolo_tracked_objects = yolo_tracker.update(yolo_detections)
#         overhead_tracked_objects = overhead_tracker.update(overhead_detections)

#         ###### 📌 Merge Tracked Objects ######
#         all_tracked_bbs = []
#         for tracked_object in yolo_tracked_objects + overhead_tracked_objects:
#             center = np.array(tracked_object.estimate).flatten()
#             x, y = int(center[0]), int(center[1])
#             width = tracked_object.last_detection.data["width"]
#             height = tracked_object.last_detection.data["height"]
#             x1, y1, x2, y2 = x - width // 2, y - height // 2, x + width // 2, y + height // 2
#             all_tracked_bbs.append((x1, y1, x2, y2))

#         ###### 📌 Draw Bounding Boxes ######
#         for x1, y1, x2, y2 in all_tracked_bbs:
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green bounding box

#         # Display the annotated frame
#         cv2.imshow("YOLO + Overhead Tracker", frame)

#         # Exit on 'q' key
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

# finally:
#     pipeline.stop()
#     cv2.destroyAllWindows()
