import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    requirements = [
        'opencv-python',
        'mediapipe',
        'pyautogui',
        'pycaw',
        'comtypes',
        'PyQt6',
        'keyboard',
        'numpy',
        'winshell'  # Added this for Windows shortcut creation
    ]
    
    print("Installing required packages...")
    
    for package in requirements:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {e}")
            # Continue with other packages even if one fails
    
    print("\nInstallation complete!")

def create_shortcut():
    """Create desktop shortcut (Windows only)"""
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError as e:
        print(f"Cannot create shortcut: {e}")
        print("Shortcut creation requires 'winshell' and 'pywin32' modules.")
        print("You can install them with: pip install winshell pypiwin32")
        return False
    
    try:
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Gesture Media Player.lnk")
        
        target = sys.executable
        w_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check if icon file exists
        icon = os.path.join(w_dir, "icon.ico")
        if not os.path.exists(icon):
            icon = ""  # Leave empty if icon doesn't exist
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.Arguments = f'"{os.path.join(w_dir, "main_app.py")}"'
        shortcut.WorkingDirectory = w_dir
        
        if icon:
            shortcut.IconLocation = icon
        
        shortcut.save()
        
        print(f"✓ Shortcut created on desktop: {path}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create shortcut: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 50)
    print("Gesture Media Player Setup")
    print("=" * 50)
    
    # Install requirements
    install_requirements()
    
    # Ask about shortcut creation
    print("\n" + "-" * 50)
    print("Shortcut Creation")
    print("-" * 50)
    
    response = input("\nCreate desktop shortcut? (y/n): ").lower().strip()
    
    if response == 'y':
        print("\nAttempting to create shortcut...")
        success = create_shortcut()
        
        if not success:
            print("\nManual setup options:")
            print("1. Run the application directly: python main_app.py")
            print("2. Create a batch file to launch the app")
    else:
        print("\nSkipping shortcut creation.")
    
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print("\nTo run the application:")
    print("1. Activate virtual environment:")
    print("   .\\gesture_env\\Scripts\\Activate.ps1")
    print("2. Run: python main_app.py")
    print("\nOr for minimal version: python minimal_gesture_player.py")
    
    # Create a simple batch file for easy launching
    create_launch_bat()

def create_launch_bat():
    """Create a batch file to launch the application"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(script_dir, "launch.bat")
    
    with open(bat_path, 'w') as f:
        f.write('@echo off\n')
        f.write('echo Starting Gesture Media Player...\n')
        f.write('cd /d "%~dp0"\n')
        f.write('if exist "gesture_env\\Scripts\\activate.bat" (\n')
        f.write('    call gesture_env\\Scripts\\activate.bat\n')
        f.write('    python main_app.py\n')
        f.write(') else (\n')
        f.write('    echo Virtual environment not found.\n')
        f.write('    echo Please run setup.py first.\n')
        f.write('    pause\n')
        f.write(')\n')
    
    print(f"\n✓ Created launch batch file: {bat_path}")

if __name__ == "__main__":
    main()