import pyrealsense2 as rs
import cv2
import numpy as np
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QSlider, QLineEdit, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt
import sys

class MotionDetector:
    def __init__(self, config_vars):
        # Store the configuration variables for dynamic adjustment
        self.config_vars = config_vars
        self.update_background_subtractor()

        # Dictionary to hold tracked objects
        self.tracked_objects = {}
        self.next_object_id = 1

    def update_background_subtractor(self):
        # Update the background subtractor with the latest `history` and `varThreshold`
        history = int(self.config_vars[0])
        var_threshold = self.config_vars[1]
        self.backSub = cv2.createBackgroundSubtractorMOG2(history=history, varThreshold=var_threshold, detectShadows=True)

    def update_config_vars(self, config_vars):
        """Update config_vars dynamically."""
        self.config_vars = config_vars
        self.update_background_subtractor()

    def compute_centroid(self, bbox):
        x, y, w, h = bbox
        return int(x + w / 2), int(y + h / 2)

    def merge_overlapping_boxes(self, bboxes):
        merged_boxes = []
        merge_distance = int(self.config_vars[4])  # Use merge distance from config_vars

        while bboxes:
            box = bboxes.pop(0)
            x1, y1, w1, h1 = box
            merged = False

            for i in range(len(merged_boxes)):
                x2, y2, w2, h2 = merged_boxes[i]
                if (x1 < x2 + w2 + merge_distance and x1 + w1 + merge_distance > x2 and
                        y1 < y2 + h2 + merge_distance and y1 + h1 + merge_distance > y2):
                    x_min = min(x1, x2)
                    y_min = min(y1, y2)
                    x_max = max(x1 + w1, x2 + w2)
                    y_max = max(y1 + h1, y2 + h2)
                    merged_boxes[i] = (x_min, y_min, x_max - x_min, y_max - y_min)
                    merged = True
                    break

            if not merged:
                merged_boxes.append(box)

        return merged_boxes

    def smooth_bounding_box(self, prev_bbox, new_bbox):
        """Applies exponential smoothing to the bounding box dimensions."""
        alpha = 0.8
        x1, y1, w1, h1 = prev_bbox
        x2, y2, w2, h2 = new_bbox

        smoothed_x = int(alpha * x2 + (1 - alpha) * x1)
        smoothed_y = int(alpha * y2 + (1 - alpha) * y1)
        smoothed_w = int(alpha * w2 + (1 - alpha) * w1)
        smoothed_h = int(alpha * h2 + (1 - alpha) * h1)

        return smoothed_x, smoothed_y, smoothed_w, smoothed_h
    def update_tracked_objects(self, detected_bboxes, current_time, timeout=0.0, shrink_threshold=0.8):
        """Update tracked objects based on new detections, with a check to stop tracking if the box shrinks significantly."""
        if not detected_bboxes:
            # No detections found, clear the tracked objects
            self.tracked_objects.clear()
            self.next_object_id = 1  # Optional: reset object ID counter if needed
            return

        new_centroids = [(bbox, self.compute_centroid(bbox)) for bbox in detected_bboxes]

        object_ids = list(self.tracked_objects.keys())
        object_centroids = [data['centroid'] for data in self.tracked_objects.values()]

        matches = {}
        unmatched_detections = []

        if self.tracked_objects and new_centroids:
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - np.array([c for _, c in new_centroids]), axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows, used_cols = set(), set()

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols or D[row, col] > self.config_vars[4]:  # Use merge distance from config_vars
                    continue

                object_id = object_ids[row]
                if object_id not in self.tracked_objects:
                    # Skip if the object_id has already been removed
                    continue

                prev_bbox = self.tracked_objects[object_id]['bbox']
                new_bbox = new_centroids[col][0]

                # Check if the bounding box has shrunk significantly
                prev_width, prev_height = prev_bbox[2], prev_bbox[3]
                new_width, new_height = new_bbox[2], new_bbox[3]
                
                if new_width < shrink_threshold * prev_width or new_height < shrink_threshold * prev_height:
                    # Stop tracking this object if it has shrunk too much
                    del self.tracked_objects[object_id]
                    continue

                # Smooth the bounding box update if the size is valid
                smoothed_bbox = self.smooth_bounding_box(prev_bbox, new_bbox)

                # Update tracked object data
                self.tracked_objects[object_id] = {
                    'bbox': smoothed_bbox,
                    'centroid': new_centroids[col][1],
                    'last_seen': current_time
                }

                matches[object_id] = True
                used_rows.add(row)
                used_cols.add(col)

            # Process unused rows for removal of timed-out objects
            unused_rows = set(range(D.shape[0])) - used_rows
            for row in unused_rows:
                object_id = object_ids[row]
                # Check if object_id is still in tracked_objects before accessing it
                if object_id in self.tracked_objects and current_time - self.tracked_objects[object_id]['last_seen'] > timeout:
                    del self.tracked_objects[object_id]

            # Add unmatched detections as new objects
            unmatched_detections = [new_centroids[col][0] for col in set(range(D.shape[1])) - used_cols]
        else:
            unmatched_detections = [bbox for bbox, _ in new_centroids]

        for bbox in unmatched_detections:
            self.tracked_objects[self.next_object_id] = {
                'bbox': bbox,
                'centroid': self.compute_centroid(bbox),
                'last_seen': current_time
            }
            self.next_object_id += 1
    def detect_movement(self, frame):
        # Apply background subtraction
        fg_mask = self.backSub.apply(frame)

        # Get dynamic values from config_vars
        threshold_value = int(self.config_vars[2])  # Threshold for binary mask
        morph_kernel_size = int(self.config_vars[3])  # Kernel size for morphology operations
        min_contour_area = self.config_vars[5]  # Minimum area for detected contours

        # Apply threshold to get binary mask
        _, mask_thresh = cv2.threshold(fg_mask, threshold_value, 255, cv2.THRESH_BINARY)
        
        # Perform morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_kernel_size, morph_kernel_size))
        mask_cleaned = cv2.morphologyEx(mask_thresh, cv2.MORPH_CLOSE, kernel)  # Remove small holes in detected areas
        mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_OPEN, kernel)  # Erode small isolated spots

        # Additional dilation and erosion to stabilize detected objects
        mask_cleaned = cv2.dilate(mask_cleaned, kernel, iterations=2)  # Expand to merge close areas
        mask_cleaned = cv2.erode(mask_cleaned, kernel, iterations=1)  # Restore approximate size

        # Find contours in the cleaned-up mask
        contours, _ = cv2.findContours(mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_bboxes = []

        # Filter contours based on minimum area
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            contour_area = cv2.contourArea(cnt)

            if contour_area > min_contour_area:
                detected_bboxes.append((x, y, w, h))

        # Merge overlapping bounding boxes
        detected_bboxes = self.merge_overlapping_boxes(detected_bboxes)

        # Update tracked objects with the current detected bounding boxes
        current_time = time.time()
        self.update_tracked_objects(detected_bboxes, current_time)

        # Return processed mask and tracked objects
        return mask_cleaned, self.tracked_objects

class RealSenseApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # Define each constant separately
        MOG2_HISTORY = 200
        MOG2_VAR_THRESHOLD = 30
        THRESHOLD_VALUE = 200
        MORPH_KERNEL_SIZE = 3
        MERGE_DISTANCE = 35
        MIN_CONTOUR = 100

        # Initialize configuration variables list with values only
        self.config_vars = [
            MOG2_HISTORY,
            MOG2_VAR_THRESHOLD,
            THRESHOLD_VALUE,
            MORPH_KERNEL_SIZE,
            MERGE_DISTANCE,
            MIN_CONTOUR
        ]



        self.initUI()

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)
        self.pipeline.start(self.config)

        self.detector = MotionDetector(self.config_vars)  # Pass config_vars to MotionDetector

        # Variables list to hold the adjustable constants

        # Timer for updating frames
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)
    def initUI(self):
            # Main layout with three side-by-side columns
            self.setWindowTitle("RealSense Motion Detector with Adjustable Settings")
            main_layout = QtWidgets.QHBoxLayout()

            # Labels for video display
            self.color_frame_label = QtWidgets.QLabel(self)
            self.mask_frame_label = QtWidgets.QLabel(self)

            # Add video displays to the main layout directly as two side-by-side columns
            main_layout.addWidget(self.color_frame_label)
            main_layout.addWidget(self.mask_frame_label)

            # Control panel for sliders
            slider_panel = QtWidgets.QVBoxLayout()
            slider_panel.addWidget(QLabel("Adjustable Parameters"))

            # Add sliders for each configuration variable
            self.create_slider_group(slider_panel, "History", 0, 10, 5000, self.config_vars, 0, step=10)
            self.create_slider_group(slider_panel, "VarThreshold", 1, 1, 100, self.config_vars, 1)
            self.create_slider_group(slider_panel, "Threshold Value", 2, 0, 255, self.config_vars, 2)
            self.create_slider_group(slider_panel, "Morph Kernel Size", 3, 1, 10, self.config_vars, 3)
            self.create_slider_group(slider_panel, "Merge Distance", 4, 0, 100, self.config_vars, 4)
            self.create_slider_group(slider_panel, "Min Contour Size", 5, 0, 1000, self.config_vars, 5, step=10)

            # Add control panel as the third column
            main_layout.addLayout(slider_panel)

            self.setLayout(main_layout)
            self.setGeometry(100, 100, 1400, 480)

    def create_slider_group(self, layout, label_text, index, min_val, max_val, target_list, list_index, step=1):
        """Helper function to create a label, slider, and input field, and add them to the layout."""
        hbox = QHBoxLayout()
        
        scaled_min = int(min_val * 10) if step == 0.1 else min_val
        scaled_max = int(max_val * 10) if step == 0.1 else max_val
        scaled_value = int(target_list[list_index] * 10) if step == 0.1 else target_list[list_index]

        # Label and Slider configuration
        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(scaled_min)
        slider.setMaximum(scaled_max)
        slider.setValue(scaled_value)
        
        # Value display fields
        value_label = QLabel(f"{target_list[list_index]:.2f}")
        value_label.setAlignment(Qt.AlignRight)

        input_field = QLineEdit(f"{target_list[list_index]:.2f}")
        input_field.setFixedWidth(50)
        input_field.setAlignment(Qt.AlignCenter)

        # Event handling for updating display and values
        input_field.returnPressed.connect(lambda: self.update_slider_from_input(input_field, slider, min_val, max_val, step))
        slider.valueChanged.connect(lambda value, lbl=value_label, inp=input_field: self.update_value_display(lbl, inp, value, step))
        slider.valueChanged.connect(lambda value: self.update_value(index, target_list, value, step))

        # Layout updates
        hbox.addWidget(label)
        hbox.addWidget(slider)
        hbox.addWidget(value_label)
        hbox.addWidget(input_field)
        layout.addLayout(hbox)

    def update_value(self, index, target_list, value, step):
        """Update target list with the slider value."""
        scaled_value = value / (10 if step == 0.1 else 1)
        target_list[index] = scaled_value

    def update_slider_from_input(self, input_field, slider, min_val, max_val, step):
        """Update the slider value based on the input field."""
        try:
            input_value = float(input_field.text())
            input_value = min(max(input_value, min_val), max_val)
            slider.setValue(int(input_value * (10 if step == 0.1 else 1)))
        except ValueError:
            pass  # Ignore invalid input

    def update_value_display(self, label, input_field, value, step):
        """Update the label and input field showing the current value."""
        scaled_value = value / (10 if step == 0.1 else 1)
        display_value = f"{scaled_value:.2f}" if step == 0.1 else f"{int(scaled_value)}"
        label.setText(display_value)
        input_field.setText(display_value)

    def update_frames(self):
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            return

        color_image = np.asanyarray(color_frame.get_data())
        fg_mask, tracked_objects = self.detector.detect_movement(color_image)

        for obj_id, data in tracked_objects.items():
            x, y, w, h = data['bbox']
            cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(color_image, f'ID: {obj_id}', (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Convert frames to QImage and display in the labels
        color_qimage = QtGui.QImage(color_image.data, color_image.shape[1], color_image.shape[0], 
                                    color_image.strides[0], QtGui.QImage.Format_BGR888)
        mask_qimage = QtGui.QImage(fg_mask.data, fg_mask.shape[1], fg_mask.shape[0], 
                                   fg_mask.strides[0], QtGui.QImage.Format_Grayscale8)

        self.color_frame_label.setPixmap(QtGui.QPixmap.fromImage(color_qimage))
        self.mask_frame_label.setPixmap(QtGui.QPixmap.fromImage(mask_qimage))

    def closeEvent(self, event):
        # Stop the RealSense pipeline when closing the app
        self.pipeline.stop()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    realsense_app = RealSenseApp()
    realsense_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()