import os
import sys
import streamlit.web.cli as stcli

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # When running as a PyInstaller binary, we need to point to the bundled ui.py
    # The src folder should be bundled.
    
    # Add src directory to Python path so imports work
    src_path = os.path.join(os.path.dirname(__file__), "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Check if running frozen
    if getattr(sys, 'frozen', False):
        # In frozen mode, src/ui.py should be in _MEIPASS/src/ui.py
        app_path = resolve_path(os.path.join("src", "ui.py"))
    else:
        app_path = os.path.join(os.path.dirname(__file__), "src", "ui.py")

    # Start background watcher agent
    try:
        from watcher import start_watcher
        print("Starting background watcher agent...")
        start_watcher()
    except Exception as e:
        print(f"Failed to start watcher: {e}")

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.address=0.0.0.0",
        "--server.headless=true",
    ]
    
    sys.exit(stcli.main())
