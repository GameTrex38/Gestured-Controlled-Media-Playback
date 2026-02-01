import cv2
import numpy as np
import time
import math
import mediapipe as mp
import os

class GestureDetector:
    def __init__(self):
        print("Initializing GestureDetector...")
        
        # First, let's check if we can import MediaPipe
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            print("✓ MediaPipe imports successful")
        except ImportError as e:
            print(f"✗ Failed to import MediaPipe: {e}")
            print("Try: pip install mediapipe")
            raise
        
        # Get the model path - FIXED FROM None
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "hand_landmarker.task")
        
        # If not found, try to download
        if not os.path.exists(model_path):
            print("Model file not found. Downloading...")
            try:
                import urllib.request
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
                urllib.request.urlretrieve(url, model_path)
                print("✓ Model downloaded")
            except Exception as e:
                print(f"✗ Download failed: {e}")
                print(f"Please download the model manually and place it at: {model_path}")
                raise FileNotFoundError(f"Model not found at {model_path}")
        
        print(f"✓ Using model: {model_path}")
        
        try:
            # Create detector
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=2,  # Changed from 1 to 2
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                running_mode=vision.RunningMode.IMAGE  # Use IMAGE mode, not LIVE_STREAM
            )
            
            self.detector = vision.HandLandmarker.create_from_options(options)
            print("✓ HandLandmarker created successfully")
            
        except Exception as e:
            print(f"✗ Failed to create detector: {e}")
            raise
        
        # Initialize other variables
        self.cap = None
        self.last_action_time = time.time()
        self.action_cooldown = 1.0
        self.frame_count = 0
        self.last_print_time = time.time()
        
        print("✓ GestureDetector initialized successfully")
    
    def start_camera(self, camera_index=0):
        """Initialize camera"""
        print(f"Starting camera {camera_index}...")
        
        # Release existing camera if any
        if self.cap is not None:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            # Try other camera indices
            for i in range(3):
                if i == camera_index:
                    continue
                self.cap = cv2.VideoCapture(i)
                if self.cap.isOpened():
                    camera_index = i
                    print(f"Switched to camera {i}")
                    break
        
        if not self.cap.isOpened():
            print(f"✗ Cannot open any camera")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Test camera
        ret, frame = self.cap.read()
        if not ret:
            print("✗ Cannot read from camera")
            return False
        
        print(f"✓ Camera {camera_index} started (640x480)")
        return True
    
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
    
    def detect_gesture(self, hand_landmarks):
        """Detect gestures from hand landmarks"""
        if not hand_landmarks or len(hand_landmarks) < 21:
            return []
        
        gestures = []
        
        try:
            # Hand landmark indices
            THUMB_TIP = 4
            THUMB_IP = 3
            THUMB_MCP = 2
            
            INDEX_TIP = 8
            INDEX_PIP = 6
            INDEX_MCP = 5
            
            MIDDLE_TIP = 12
            MIDDLE_PIP = 10
            MIDDLE_MCP = 9
            
            RING_TIP = 16
            RING_PIP = 14
            RING_MCP = 13
            
            PINKY_TIP = 20
            PINKY_PIP = 18
            PINKY_MCP = 17
            
            WRIST = 0
            
            # 1. PINCH GESTURE
            thumb_tip = hand_landmarks[THUMB_TIP]
            index_tip = hand_landmarks[INDEX_TIP]
            distance = self.calculate_distance(thumb_tip, index_tip)
            
            # Dynamic threshold based on hand size
            hand_size_ref = self.calculate_distance(hand_landmarks[WRIST], hand_landmarks[MIDDLE_MCP])
            pinch_threshold = hand_size_ref * 0.3  # Adjustable
            
            if distance < pinch_threshold:
                gestures.append('play_pause')
            
            # Check finger extension (simplified)
            # For front-facing camera with flip, lower y means higher up
            index_extended = hand_landmarks[INDEX_TIP].y < hand_landmarks[INDEX_PIP].y - 0.02
            middle_extended = hand_landmarks[MIDDLE_TIP].y < hand_landmarks[MIDDLE_PIP].y - 0.02
            ring_extended = hand_landmarks[RING_TIP].y < hand_landmarks[RING_PIP].y - 0.02
            pinky_extended = hand_landmarks[PINKY_TIP].y < hand_landmarks[PINKY_PIP].y - 0.02
            
            # Thumb check (different logic)
            thumb_vector_x = thumb_tip.x - hand_landmarks[THUMB_MCP].x
            thumb_vector_y = thumb_tip.y - hand_landmarks[THUMB_MCP].y
            thumb_magnitude = math.sqrt(thumb_vector_x**2 + thumb_vector_y**2)
            thumb_extended = thumb_magnitude > 0.1
            
            # Count extended fingers
            extended_count = sum([index_extended, middle_extended, ring_extended, pinky_extended])
            
            # 2. THUMB UP (Volume Up)
            if thumb_extended and extended_count == 0 and thumb_tip.y < hand_landmarks[WRIST].y:
                gestures.append('volume_up')
            
            # 3. THUMB DOWN (Volume Down)
            elif not thumb_extended and extended_count == 0 and thumb_tip.y > hand_landmarks[WRIST].y:
                gestures.append('volume_down')
            
            # 4. PEACE SIGN (Next Track)
            elif index_extended and middle_extended and not ring_extended and not pinky_extended:
                gestures.append('next_track')
            
            # 5. POINTING (Previous Track)
            elif index_extended and not middle_extended and not ring_extended and not pinky_extended:
                gestures.append('prev_track')
            
            # 6. FIST (Mute)
            elif extended_count == 0 and not thumb_extended:
                gestures.append('mute')
            
            # 7. OPEN HAND
            elif extended_count == 4 and thumb_extended:
                gestures.append('open_hand')
            
            # Debug: Print what's being detected
            if gestures:
                print(f"  Extended: I={index_extended}, M={middle_extended}, R={ring_extended}, P={pinky_extended}, T={thumb_extended}")
                print(f"  Distance: {distance:.3f}, Threshold: {pinch_threshold:.3f}")
                
        except Exception as e:
            print(f"Error in gesture detection: {e}")
            import traceback
            traceback.print_exc()
        
        return gestures
    
    def draw_landmarks_on_image(self, rgb_image, detection_result):
        """Draw hand landmarks and connections on the image"""
        hand_landmarks_list = detection_result.hand_landmarks
        annotated_image = np.copy(rgb_image)
        
        if not hand_landmarks_list:
            return annotated_image
        
        # Define hand connections
        HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (5, 9), (9, 13), (13, 17)  # Palm
        ]
        
        h, w, _ = annotated_image.shape
        
        # Loop through detected hands
        for idx, hand_landmarks in enumerate(hand_landmarks_list):
            # Choose color based on hand index
            if idx == 0:
                color = (0, 255, 0)  # Green for first hand
            else:
                color = (255, 0, 0)  # Blue for second hand
            
            # Draw connections
            for connection in HAND_CONNECTIONS:
                start_idx, end_idx = connection
                if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                    start_point = (int(hand_landmarks[start_idx].x * w), 
                                 int(hand_landmarks[start_idx].y * h))
                    end_point = (int(hand_landmarks[end_idx].x * w), 
                               int(hand_landmarks[end_idx].y * h))
                    cv2.line(annotated_image, start_point, end_point, color, 2)
            
            # Draw landmarks
            for landmark in hand_landmarks:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(annotated_image, (x, y), 5, color, -1)
                cv2.circle(annotated_image, (x, y), 6, (255, 255, 255), 1)
        
        return annotated_image
    
    def process_frame(self):
        """Process a camera frame and detect gestures"""
        if not self.cap or not self.cap.isOpened():
            return None, []
        
        success, frame = self.cap.read()
        if not success:
            return None, []
        
        # Flip for mirror view
        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # DEBUG: Print frame info occasionally
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_print_time > 2.0:  # Every 2 seconds
            print(f"Processing frame {self.frame_count}, shape: {frame.shape}")
            self.last_print_time = current_time
        
        # Convert to MediaPipe Image - FIXED: Use correct format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Detect hands
        try:
            detection_result = self.detector.detect(mp_image)
        except Exception as e:
            print(f"Detection error: {e}")
            return frame, []
        
        gestures = []
        hand_detected = False
        
        if detection_result.hand_landmarks:
            hand_detected = True
            hand_count = len(detection_result.hand_landmarks)
            print(f"✓ Hands detected: {hand_count}")
            
            # Draw landmarks
            annotated_image = self.draw_landmarks_on_image(rgb_frame, detection_result)
            frame = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
            
            # Detect gestures for each hand
            for hand_idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                print(f"  Processing hand {hand_idx + 1} with {len(hand_landmarks)} landmarks")
                hand_gestures = self.detect_gesture(hand_landmarks)
                if hand_gestures:
                    gestures.extend(hand_gestures)
                    print(f"  Gestures detected: {hand_gestures}")
        
        # Display gesture text
        if gestures:
            # Remove duplicates
            unique_gestures = []
            for g in gestures:
                if g not in unique_gestures:
                    unique_gestures.append(g)
            
            gesture_text = "Gesture: " + ", ".join(unique_gestures)
            
            # Draw text background
            text_size = cv2.getTextSize(gesture_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            cv2.rectangle(frame, (5, 5), (text_size[0] + 15, text_size[1] + 20), (0, 0, 0), -1)
            
            # Draw text
            cv2.putText(frame, gesture_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        elif hand_detected:
            # Show that hand is detected but no gesture recognized
            cv2.putText(frame, "Hand detected - No gesture", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        else:
            # Show that no hand is detected
            cv2.putText(frame, "No hand detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Display hand count
        hand_count = len(detection_result.hand_landmarks) if detection_result.hand_landmarks else 0
        cv2.putText(frame, f"Hands: {hand_count}", (width - 120, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Display instructions
        instructions = [
            "Pinch: Play/Pause | Thumb Up: Vol+",
            "Thumb Down: Vol- | Peace: Next",
            "Point: Previous | Fist: Mute",
            "Open hand: Stop"
        ]
        
        y_pos = height - 100
        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
        
        # Display FPS
        if not hasattr(self, 'fps_last_time'):
            self.fps_last_time = time.time()
            self.fps_counter = 0
            self.current_fps = 0
        
        self.fps_counter += 1
        if time.time() - self.fps_last_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_last_time = time.time()
        
        cv2.putText(frame, f"FPS: {self.current_fps}", (width - 120, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return frame, gestures
    
    def release(self):
        """Release resources"""
        print("Releasing resources...")
        if self.cap:
            self.cap.release()
            print("✓ Camera released")
        if hasattr(self, 'detector'):
            try:
                self.detector.close()
                print("✓ Detector closed")
            except:
                pass
        cv2.destroyAllWindows()
        print("✓ GestureDetector released")


# Test function
def test():
    """Test the gesture detector"""
    detector = GestureDetector()
    
    if not detector.start_camera():
        print("Failed to start camera")
        return
    
    print("\n" + "="*60)
    print("TESTING GESTURE DETECTOR")
    print("="*60)
    print("Show your hand to the camera")
    print("Look for green landmarks")
    print("Try different gestures")
    print("Press 'q' to quit")
    print("="*60 + "\n")
    
    try:
        while True:
            frame, gestures = detector.process_frame()
            
            if frame is None:
                break
            
            cv2.imshow('Gesture Detector Test', frame)
            
            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        detector.release()
        print("\nTest completed.")


if __name__ == "__main__":
    test()