import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_DIR = ROOT / 'Smart-Pay-main'

# Add Smart-Pay-main to sys.path so imports work
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

TARGET = PROJECT_DIR / 'streamlit_app.py'

spec = importlib.util.spec_from_file_location('smartpay_streamlit_app', str(TARGET))
module = importlib.util.module_from_spec(spec)
sys.modules['smartpay_streamlit_app'] = module
spec.loader.exec_module(module)

from smartpay_streamlit_app import *  # noqa: F401
