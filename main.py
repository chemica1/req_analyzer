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
    
    # Check if running frozen
    if getattr(sys, 'frozen', False):
        # In frozen mode, src/ui.py should be in _MEIPASS/src/ui.py
        app_path = resolve_path(os.path.join("src", "ui.py"))
    else:
        app_path = os.path.join(os.path.dirname(__file__), "src", "ui.py")

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.address=0.0.0.0",
        "--server.headless=true",
    ]
    
    sys.exit(stcli.main())
