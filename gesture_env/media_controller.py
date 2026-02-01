# media_controller.py
import pyautogui
import time
from typing import Optional

class MediaController:
    """Control media playback on the system"""
    
    def __init__(self):
        self.current_app = self.detect_active_media_app()
        self.last_command_time = 0
        self.command_cooldown = 0.5  # seconds
        
    def detect_active_media_app(self) -> str:
        """Detect which media app is active"""
        # This is a simplified version
        # You could use pygetwindow to detect active window
        try:
            import pygetwindow as gw
            active_window = gw.getActiveWindow()
            if active_window:
                title = active_window.title.lower()
                if 'youtube' in title or 'chrome' in title or 'firefox' in title or 'edge' in title:
                    return "youtube"
                elif 'spotify' in title:
                    return "spotify"
                elif 'vlc' in title:
                    return "vlc"
        except:
            pass
        return "system"  # Default to system media keys
    
    def can_send_command(self) -> bool:
        """Check if enough time has passed since last command"""
        current_time = time.time()
        return current_time - self.last_command_time > self.command_cooldown
    
    def send_command(self, gesture: str):
        """Send media command based on gesture"""
        if not self.can_send_command():
            return False
        
        self.last_command_time = time.time()
        
        try:
            if self.current_app == "youtube":
                return self._youtube_commands(gesture)
            elif self.current_app == "spotify":
                return self._spotify_commands(gesture)
            else:
                return self._system_commands(gesture)
                
        except Exception as e:
            print(f"✗ Failed to send command: {e}")
            return False
    
    def _system_commands(self, gesture: str):
        """System-level media controls (works with Spotify, VLC, etc.)"""
        try:
            if gesture == 'play_pause':
                pyautogui.press('playpause')
            elif gesture == 'volume_up':
                pyautogui.press('volumeup')
            elif gesture == 'volume_down':
                pyautogui.press('volumedown')
            elif gesture == 'next_track':
                pyautogui.press('nexttrack')
            elif gesture == 'prev_track':
                pyautogui.press('prevtrack')
            elif gesture == 'mute':
                pyautogui.press('volumemute')
            elif gesture == 'open_hand':
                pyautogui.press('stop')
            else:
                return False
            return True
        except:
            return False
    
    def _youtube_commands(self, gesture: str):
        """YouTube-specific keyboard shortcuts"""
        try:
            if gesture == 'play_pause':
                pyautogui.press('space')  # or 'k'
            elif gesture == 'volume_up':
                for _ in range(3):  # Increase volume faster
                    pyautogui.press('up')
                    time.sleep(0.05)
            elif gesture == 'volume_down':
                for _ in range(3):  # Decrease volume faster
                    pyautogui.press('down')
                    time.sleep(0.05)
            elif gesture == 'next_track':
                pyautogui.hotkey('shift', 'n')
            elif gesture == 'prev_track':
                pyautogui.hotkey('shift', 'p')
            elif gesture == 'mute':
                pyautogui.press('m')
            elif gesture == 'open_hand':
                pyautogui.press('k')  # Stop/Play in YouTube
            else:
                return False
            return True
        except:
            return False
    
    def _spotify_commands(self, gesture: str):
        """Spotify-specific controls"""
        try:
            if gesture == 'play_pause':
                pyautogui.press('space')
            elif gesture == 'volume_up':
                pyautogui.hotkey('ctrl', 'up')
            elif gesture == 'volume_down':
                pyautogui.hotkey('ctrl', 'down')
            elif gesture == 'next_track':
                pyautogui.hotkey('ctrl', 'right')
            elif gesture == 'prev_track':
                pyautogui.hotkey('ctrl', 'left')
            elif gesture == 'mute':
                pyautogui.hotkey('ctrl', 'shift', 'down')
            elif gesture == 'open_hand':
                pyautogui.press('stop')
            else:
                return False
            return True
        except:
            return False
    
    def get_current_app(self):
        """Get current media app"""
        self.current_app = self.detect_active_media_app()
        return self.current_app