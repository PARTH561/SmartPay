import os
import sys

BASE_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.join(BASE_DIR, 'Smart-Pay-main')
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from streamlit_app import *  # noqa: F401
