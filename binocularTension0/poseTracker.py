import cv2
import mediapipe as mp
import numpy as np
# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils
import pyrealsense2 as rs
import numpy as np
import cv2
import mediapipe as mp
def process_pose(image, aligned_depth_frame, intrinsics, visibility_threshold=0.5):
    """
    Processes an image to detect human pose landmarks using MediaPipe Pose, draws the landmarks,
    retrieves the z-coordinate (depth) for each visible landmark from the aligned depth frame, and converts them into 3D points.

    :param image: The RGB image in which pose landmarks need to be detected.
    :param aligned_depth_frame: The depth frame aligned with the color frame from RealSense.
    :param intrinsics: The RealSense camera intrinsics for 2D to 3D conversion.
    :param visibility_threshold: Minimum visibility score to consider the landmark visible.
    :return: The image with pose landmarks drawn and a list of 3D points (x, y, z) for each visible landmark.
    """
    # Convert the image to RGB format (MediaPipe expects RGB)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Process the image to detect pose
    results = pose.process(rgb_image)

    # List to store 3D coordinates of visible landmarks
    landmarks_3d = []

    if results.pose_landmarks:
        # Draw pose landmarks on the image
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        image_height, image_width = image.shape[:2]

        for landmark in results.pose_landmarks.landmark:
            # Only process the landmark if its visibility score is above the threshold
            if landmark.visibility >= visibility_threshold:
                # Convert normalized coordinates to pixel coordinates
                x_pixel = int(landmark.x * image_width)
                y_pixel = int(landmark.y * image_height)

                # Ensure pixel coordinates are within valid bounds
                x_pixel = np.clip(x_pixel, 0, image_width - 1)
                y_pixel = np.clip(y_pixel, 0, image_height - 1)

                # Get depth at the pixel location from the aligned depth frame
                depth_value = aligned_depth_frame.get_distance(x_pixel, y_pixel)

                if depth_value > 0:
                    # Convert 2D pixel (x, y) and depth (z) to 3D using RealSense intrinsics
                    landmark_3d = rs.rs2_deproject_pixel_to_point(intrinsics, [x_pixel, y_pixel], depth_value)
                    landmarks_3d.append(landmark_3d)

    return image, landmarks_3d
