import cv2
import numpy as np
import time
import pyautogui
import os
import sys

# Add the current directory to path to import your working gesture_detector
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your working gesture detector
try:
    from gesture_detector import GestureDetector
    print("✓ Using your existing GestureDetector")
except ImportError:
    print("✗ Could not import GestureDetector")
    exit(1)

class SimpleGesturePlayer:
    def __init__(self):
        # Use your existing working GestureDetector
        self.detector = GestureDetector()
        
        # Start camera
        if not self.detector.start_camera():
            print("Failed to start camera")
            exit(1)
        
        self.last_action = time.time()
        self.action_cooldown = 1.0
        
        print("\n" + "="*50)
        print("Simple Gesture Player Started!")
        print("="*50)
        print("Gestures:")
        print("  🤏 Pinch - Play/Pause")
        print("  👍 Thumb Up - Volume Up")
        print("  👎 Thumb Down - Volume Down")
        print("  ✌️ Peace - Next Track")
        print("  👆 Point - Previous Track")
        print("  👊 Fist - Mute")
        print("\nPress 'q' to quit")
        print("="*50 + "\n")
    
    def execute_action(self, gesture):
        """Execute media action using pyautogui"""
        actions = {
            'play_pause': lambda: pyautogui.press('playpause'),
            'volume_up': lambda: pyautogui.press('volumeup'),
            'volume_down': lambda: pyautogui.press('volumedown'),
            'next_track': lambda: pyautogui.press('nexttrack'),
            'prev_track': lambda: pyautogui.press('prevtrack'),
            'mute': lambda: pyautogui.press('volumemute')
        }
        
        current_time = time.time()
        if gesture in actions and current_time - self.last_action > self.action_cooldown:
            try:
                actions[gesture]()
                print(f"✓ Action: {gesture}")
                self.last_action = current_time
                return True
            except Exception as e:
                print(f"✗ Failed to execute action: {e}")
                return False
        return False
    
    def run(self):
        """Main loop"""
        try:
            while True:
                # Process frame using your existing detector
                frame, gestures = self.detector.process_frame()
                
                if frame is None:
                    print("No frame received")
                    break
                
                # Execute action if any gesture detected
                if gestures:
                    # Take the first gesture
                    gesture = gestures[0]
                    self.execute_action(gesture)
                    
                    # Display gesture on screen
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Gesture: {gesture}", (12, 52),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1)
                
                # Display FPS
                if not hasattr(self, 'last_fps_time'):
                    self.last_fps_time = time.time()
                    self.frame_count = 0
                    self.fps = 0
                
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_time = current_time
                
                cv2.putText(frame, f"FPS: {self.fps}", (10, frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # Show frame
                cv2.imshow('Simple Gesture Media Player', frame)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nQuitting...")
                    break
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            # Cleanup
            self.detector.release()
            cv2.destroyAllWindows()
            print("✓ Application closed")

if __name__ == "__main__":
    # Check if pyautogui is installed
    try:
        import pyautogui
        print("✓ pyautogui is installed")
    except ImportError:
        print("✗ pyautogui is not installed")
        print("Install it with: pip install pyautogui")
        exit(1)
    
    player = SimpleGesturePlayer()
    player.run()