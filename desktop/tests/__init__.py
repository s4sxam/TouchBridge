"""TouchBridge Automated Test Suite."""

import sys
from pathlib import Path

# Automatically ensure desktop directory is in sys.path so tests can run from anywhere
desktop_dir = str(Path(__file__).resolve().parent.parent)
if desktop_dir not in sys.path:
    sys.path.insert(0, desktop_dir)
