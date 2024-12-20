import threading

class DetectionData:
    _instance = None
    _lock = threading.Lock()  # Lock to ensure thread safety for singleton

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.init_data()  # Initialize the data here
        return cls._instance

    def init_data(self):
        self.person_moving_status = {}
        self.bounding_boxes = []
        self.non_person_movement_boxes = []
        self.object_boxes = []
        self.persons_with_ids = []
        self.objects_outside_thresholds = []  # Store objects outside thresholds
        self.active_movement_id = None  # ID of the currently active movement
        self.active_movement_type = None  # Type of the currently active movement
        self._is_dark = False  # Boolean indicating if it is currently dark
        self.lock = threading.Lock()

    # Setter and getter for is_dark
    def set_is_dark(self, is_dark):
        with self.lock:
            self._is_dark = is_dark

    def get_is_dark(self):
        with self.lock:
            return self._is_dark

    # Existing methods with locking for thread safety
    def set_person_moving_status(self, person_moving_status):
        with self.lock:
            self.person_moving_status = person_moving_status

    def get_person_moving_status(self):
        with self.lock:
            return self.person_moving_status
        
    def set_bounding_boxes(self, boxes):
        with self.lock:
            self.bounding_boxes = boxes

    def get_bounding_boxes(self):
        with self.lock:
            return self.bounding_boxes
    
    def set_object_boxes(self, boxes):
        with self.lock:
            self.object_boxes = boxes

    def get_object_boxes(self):
        with self.lock:
            return self.object_boxes
        
    def set_non_person_movement_boxes(self, non_person_movement_boxes):
        with self.lock:
            self.non_person_movement_boxes = non_person_movement_boxes

    def get_non_person_movement_boxes(self):
        with self.lock:
            return self.non_person_movement_boxes

    def set_persons_with_ids(self, persons_with_ids):
        with self.lock:
            self.persons_with_ids = persons_with_ids

    def get_persons_with_ids(self):
        with self.lock:
            return self.persons_with_ids

    # Setters and getters for objects outside thresholds
    def set_objects_outside_thresholds(self, objects_outside_thresholds):
        with self.lock:
            self.objects_outside_thresholds = objects_outside_thresholds

    def get_objects_outside_thresholds(self):
        with self.lock:
            return self.objects_outside_thresholds

    # Setters and getters for active movement ID and type
    def set_active_movement_id(self, active_movement_id):
        with self.lock:
            self.active_movement_id = active_movement_id

    def get_active_movement_id(self):
        with self.lock:
            return self.active_movement_id

    def set_active_movement_type(self, active_movement_type):
        with self.lock:
            self.active_movement_type = active_movement_type

    def get_active_movement_type(self):
        with self.lock:
            return self.active_movement_type
