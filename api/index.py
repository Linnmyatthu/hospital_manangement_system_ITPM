import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import app.py
sys.path.append(str(Path(__file__).parent.parent))

from app import app as flask_app

# Vercel requires a variable named 'app'
app = flask_app