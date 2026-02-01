import sys
import os
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_integration():
    """Test integration between main and gesture_detector"""
    print("Testing integration...")
    
    try:
        # Test 1: Import gesture_detector
        print("\n1. Testing import...")
        from gesture_detector import GestureDetector
        print("✓ Import successful")
        
        # Test 2: Create detector
        print("\n2. Creating detector...")
        detector = GestureDetector()
        print("✓ Detector created")
        
        # Test 3: Start camera
        print("\n3. Starting camera...")
        if detector.start_camera():
            print("✓ Camera started")
            
            # Test 4: Process a few frames
            print("\n4. Processing frames (5 frames)...")
            for i in range(5):
                frame, gestures = detector.process_frame()
                if frame is not None:
                    print(f"  Frame {i+1}: {frame.shape if frame is not None else 'None'}, "
                          f"Gestures: {gestures}")
                time.sleep(0.5)
            
            # Test 5: Release resources
            print("\n5. Releasing resources...")
            detector.release()
            print("✓ Resources released")
        else:
            print("✗ Failed to start camera")
            
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✓ All integration tests passed!")
    return True


def test_qt():
    """Test Qt without detector"""
    print("\nTesting Qt...")
    try:
        from PyQt5.QtWidgets import QApplication, QLabel
        import sys as sys_qt
        
        app = QApplication([])
        label = QLabel("Qt test - if you see this, Qt works")
        label.show()
        
        # Don't actually run the app, just test initialization
        print("✓ Qt initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ Qt test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DEBUG INTEGRATION TEST")
    print("=" * 60)
    
    # Run tests
    test_integration()
    test_qt()
    
    print("\n" + "=" * 60)
    print("If both tests pass, the issue is in the main app logic")
    print("If tests fail, fix those issues first")
    print("=" * 60)