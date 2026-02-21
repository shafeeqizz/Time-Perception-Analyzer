import sys
from pathlib import Path

# Add the backend directory to Python path so "import app..." works in CI
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))