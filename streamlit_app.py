import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
TARGET = ROOT / 'Smart-Pay-main' / 'streamlit_app.py'

spec = importlib.util.spec_from_file_location('smartpay_streamlit_app', str(TARGET))
module = importlib.util.module_from_spec(spec)
sys.modules['smartpay_streamlit_app'] = module
spec.loader.exec_module(module)

from smartpay_streamlit_app import *  # noqa: F401
