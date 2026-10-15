import sys
import os
from pathlib import Path

# When launched via pythonw.exe (no console), redirect stdout/stderr so print() doesn't crash
if sys.stdout is None or not hasattr(sys.stdout, "write"):
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gui.app import JarvisApp

def main():
    print("=" * 60)
    print("   FRYDAY // TACTICAL DESKTOP ASSISTANT ONLINE")
    print("   Developed by Prateek Sharma // Stark Industries Architecture")
    print("=" * 60)
    
    app = JarvisApp()
    app.mainloop()

if __name__ == "__main__":
    main()
