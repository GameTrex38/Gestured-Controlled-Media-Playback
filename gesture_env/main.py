#!/usr/bin/env python3
"""
Gesture Controlled Media Player
"""

import os
import sys
import time
import threading
import json

# ============================================================================
# FIX FOR WINDOWS DPI ISSUES
# ============================================================================
if os.name == 'nt':  # Windows
    try:
        import ctypes
        # Try different DPI awareness methods
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(2)  # Per-monitor aware
        except:
            pass
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor aware
        except:
            pass
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # Legacy method
        except:
            pass
    except:
        pass

# Qt environment settings
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"

# ============================================================================
# IMPORTS
# ============================================================================
import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gesture_detector import GestureDetector
from media_controller import MediaController

class GestureMediaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing GestureMediaApp...")
        
        # Initialize variables
        self.detector = None
        self.camera_thread = None
        self.is_running = False
        self.current_gesture = None
        self.last_gesture_time = 0
        self.gesture_cooldown = 1.0  # seconds
        
        # Media control variables (placeholder)
        self.is_playing = False
        self.volume = 50
        self.is_muted = False
        
        # ADD THIS LINE:
        self.media_controller = MediaController()
        
        self.setup_ui()
        self.setup_detector()
        
        print("✓ GestureMediaApp initialized")
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Gesture Controlled Media Player")
        self.setGeometry(100, 100, 1200, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Camera display area
        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            QLabel {
                border: 2px solid #444;
                border-radius: 5px;
                background-color: #222;
                color: #888;
                font-size: 16px;
                min-height: 480px;
            }
        """)
        main_layout.addWidget(self.camera_label)
        
        # Status and controls layout
        controls_layout = QHBoxLayout()
        
        # Status display
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        controls_layout.addWidget(self.status_label)
        
        # Gesture display
        self.gesture_label = QLabel("Gesture: None")
        self.gesture_label.setStyleSheet("font-size: 14px; color: #4CAF50;")
        controls_layout.addWidget(self.gesture_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.clicked.connect(self.start_camera)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Camera")
        self.stop_btn.clicked.connect(self.stop_camera)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(self.stop_btn)
        
        controls_layout.addLayout(button_layout)
        main_layout.addLayout(controls_layout)
        
        # Media controls (visual representation)
        media_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_pause_btn = QPushButton("⏯ Play/Pause")
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        media_layout.addWidget(self.play_pause_btn)
        
        # Volume control
        volume_layout = QVBoxLayout()
        volume_layout.addWidget(QLabel("Volume"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setEnabled(False)
        volume_layout.addWidget(self.volume_slider)
        media_layout.addLayout(volume_layout)
        
        # Mute button
        self.mute_btn = QPushButton("🔇 Mute")
        self.mute_btn.setEnabled(False)
        self.mute_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        media_layout.addWidget(self.mute_btn)
        
        # Next/Previous buttons
        self.prev_btn = QPushButton("⏮ Previous")
        self.prev_btn.setEnabled(False)
        self.prev_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        media_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("⏭ Next")
        self.next_btn.setEnabled(False)
        self.next_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        media_layout.addWidget(self.next_btn)
        
        main_layout.addLayout(media_layout)
        
        # Instructions
        instructions = QLabel(
            "Gesture Controls:\n"
            "• Pinch thumb & index: Play/Pause\n"
            "• Thumb up: Volume Up\n"
            "• Thumb down: Volume Down\n"
            "• Peace sign (V): Next Track\n"
            "• Pointing finger: Previous Track\n"
            "• Fist: Mute/Unmute\n"
            "• Open hand: Stop"
        )
        instructions.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        main_layout.addWidget(instructions)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def setup_detector(self):
        """Initialize gesture detector"""
        print("Setting up gesture detector...")
        try:
            # Try to initialize detector
            self.detector = GestureDetector()
            print("✓ Gesture detector initialized")
            self.statusBar().showMessage("Gesture detector ready")
            
            # Try to start camera automatically
            QTimer.singleShot(1000, self.start_camera)
            
        except Exception as e:
            print(f"✗ Failed to initialize detector: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            self.statusBar().showMessage("Failed to initialize detector")
    
    def start_camera(self):
        """Start camera and processing thread"""
        if self.is_running:
            return
        
        print("Starting camera...")
        self.status_label.setText("Status: Starting camera...")
        
        if not self.detector:
            print("No detector available")
            self.status_label.setText("Status: No detector available")
            return
        
        # Start camera
        if not self.detector.start_camera():
            print("Failed to start camera")
            self.status_label.setText("Status: Failed to start camera")
            return
        
        print("✓ Camera started")
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Camera running")
        
        # Enable media controls
        self.play_pause_btn.setEnabled(True)
        self.volume_slider.setEnabled(True)
        self.mute_btn.setEnabled(True)
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        
        # Start processing thread
        self.camera_thread = threading.Thread(target=self.process_frames, daemon=True)
        self.camera_thread.start()
        
        self.statusBar().showMessage("Camera started - Show your hand to camera")
    
    def stop_camera(self):
        """Stop camera and processing"""
        if not self.is_running:
            return
        
        print("Stopping camera...")
        self.is_running = False
        
        # Wait for thread to finish
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=2.0)
        
        # Release detector resources
        if self.detector:
            self.detector.release()
        
        # Reset UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.camera_label.clear()
        self.camera_label.setText("Camera Stopped")
        self.status_label.setText("Status: Stopped")
        self.gesture_label.setText("Gesture: None")
        
        # Disable media controls
        self.play_pause_btn.setEnabled(False)
        self.volume_slider.setEnabled(False)
        self.mute_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        
        self.statusBar().showMessage("Camera stopped")
        print("✓ Camera stopped")
    
    def process_frames(self):
        """Process camera frames in a separate thread"""
        print("Frame processing thread started")
        frame_count = 0
        
        while self.is_running and self.detector:
            try:
                # Process frame
                frame, gestures = self.detector.process_frame()
                
                if frame is not None:
                    frame_count += 1
                    
                    # Convert frame for display
                    height, width, channel = frame.shape
                    bytes_per_line = 3 * width
                    qt_image = QImage(frame.data, width, height, bytes_per_line, 
                                     QImage.Format_RGB888).rgbSwapped()
                    
                    # Update UI in main thread
                    QMetaObject.invokeMethod(self, "update_camera_display", 
                                           Qt.QueuedConnection,
                                           Q_ARG(QImage, qt_image))
                    
                    # Process gestures
                    if gestures:
                        current_time = time.time()
                        if current_time - self.last_gesture_time > self.gesture_cooldown:
                            self.last_gesture_time = current_time
                            self.current_gesture = gestures[0]  # Take first gesture
                            
                            # Update gesture display in main thread
                            QMetaObject.invokeMethod(self, "update_gesture_display",
                                                   Qt.QueuedConnection,
                                                   Q_ARG(str, self.current_gesture))
                            
                            # Process gesture command
                            self.process_gesture_command(self.current_gesture)
                
                # Small delay to prevent CPU overload
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                print(f"Error in frame processing: {e}")
                if "detect" in str(e).lower():
                    print("Detection error - stopping camera")
                    self.is_running = False
                    QMetaObject.invokeMethod(self, "stop_camera", Qt.QueuedConnection)
                break
        
        print("Frame processing thread stopped")
    
    @pyqtSlot(QImage)
    def update_camera_display(self, image):
        """Update camera display (called from main thread)"""
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), 
                                     Qt.KeepAspectRatio, 
                                     Qt.SmoothTransformation)
        self.camera_label.setPixmap(scaled_pixmap)
    
    @pyqtSlot(str)
    def update_gesture_display(self, gesture):
        """Update gesture display (called from main thread)"""
        self.gesture_label.setText(f"Gesture: {gesture}")
        self.statusBar().showMessage(f"Gesture detected: {gesture}")
    
    def process_gesture_command(self, gesture):
        """Process gesture and perform media control action"""
        print(f"Processing gesture: {gesture}")
        
        # First, try to send media control command
        success = self.media_controller.send_command(gesture)
        
        if success:
            print(f"✓ Media command sent: {gesture}")
            
            # Also update UI to show feedback
            if gesture == 'play_pause':
                self.toggle_play_pause()
            elif gesture == 'volume_up':
                self.adjust_volume(10)
            elif gesture == 'volume_down':
                self.adjust_volume(-10)
            elif gesture == 'next_track':
                self.next_track()
            elif gesture == 'prev_track':
                self.previous_track()
            elif gesture == 'mute':
                self.toggle_mute()
            elif gesture == 'open_hand':
                self.stop_playback()
        else:
            print(f"✗ Could not send media command for: {gesture}")
            
            # Fallback: Just update UI
            if gesture == 'play_pause':
                self.toggle_play_pause()
            elif gesture == 'volume_up':
                self.adjust_volume(10)
            elif gesture == 'volume_down':
                self.adjust_volume(-10)
            elif gesture == 'next_track':
                self.next_track()
            elif gesture == 'prev_track':
                self.previous_track()
            elif gesture == 'mute':
                self.toggle_mute()
            elif gesture == 'open_hand':
                self.stop_playback()
                
    def toggle_play_pause(self):
        """Toggle play/pause state"""
        self.is_playing = not self.is_playing
        state = "Playing" if self.is_playing else "Paused"
        print(f"Play/Pause: {state}")
        self.play_pause_btn.setText(f"⏯ {'Pause' if self.is_playing else 'Play'}")
    
    def adjust_volume(self, delta):
        """Adjust volume by delta"""
        self.volume = max(0, min(100, self.volume + delta))
        self.volume_slider.setValue(self.volume)
        print(f"Volume: {self.volume}%")
    
    def next_track(self):
        """Go to next track"""
        print("Next track")
    
    def previous_track(self):
        """Go to previous track"""
        print("Previous track")
    
    def toggle_mute(self):
        """Toggle mute state"""
        self.is_muted = not self.is_muted
        state = "Muted" if self.is_muted else "Unmuted"
        print(f"Mute: {state}")
        self.mute_btn.setText(f"{'🔊 Unmute' if self.is_muted else '🔇 Mute'}")
    
    def stop_playback(self):
        """Stop playback"""
        self.is_playing = False
        print("Stop playback")
        self.play_pause_btn.setText("⏯ Play")
    
    def closeEvent(self, event):
        """Handle application close"""
        print("Closing application...")
        self.stop_camera()
        event.accept()
        print("Application closed")


def main():
    """Main function"""
    print("Starting Gesture Controlled Media Player...")
    print("=" * 60)
    
    # Create and run application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern style
    
    # Create and show main window
    window = GestureMediaApp()
    window.show()
    
    # Start application
    print("✓ Application started")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()