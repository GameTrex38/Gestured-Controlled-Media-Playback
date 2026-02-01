import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os

def test_mediapipe():
    print("Testing MediaPipe Hand Detection...")
    
    # Check if model file exists
    model_path = "hand_landmarker.task"
    if not os.path.exists(model_path):
        print(f"ERROR: Model file not found at: {model_path}")
        print("Downloading model...")
        import urllib.request
        try:
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            urllib.request.urlretrieve(url, model_path)
            print("Model downloaded successfully!")
        except Exception as e:
            print(f"Failed to download: {e}")
            return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    # Create hand detector
    try:
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        detector = vision.HandLandmarker.create_from_options(options)
        print("✓ HandLandmarker created successfully")
    except Exception as e:
        print(f"✗ Failed to create detector: {e}")
        cap.release()
        return
    
    print("\nPress 'q' to quit")
    print("Show your hand to the camera...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Detect hands
        result = detector.detect(mp_image)
        
        # Draw results
        if result.hand_landmarks:
            print(f"✓ Hand detected! Landmarks: {len(result.hand_landmarks[0])}")
            
            # Draw simple landmarks
            h, w, _ = frame.shape
            for hand_landmarks in result.hand_landmarks:
                for landmark in hand_landmarks:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        else:
            print("No hand detected")
        
        # Show hand count
        hand_count = len(result.hand_landmarks) if result.hand_landmarks else 0
        cv2.putText(frame, f"Hands: {hand_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('MediaPipe Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    detector.close()
    cap.release()
    cv2.destroyAllWindows()
    print("\nTest completed.")

if __name__ == "__main__":
    test_mediapipe()