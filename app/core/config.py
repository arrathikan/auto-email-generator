"""
Configuration settings and centralized directory paths for CareerLens.
"""
import os

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_DIR = os.path.abspath(os.path.join(APP_DIR, ".."))

DATA_DIR = os.path.join(APP_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

UPLOADS_DIR = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ASSETS_DIR = os.path.join(APP_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

DEFAULT_DB_PATH = os.path.join(DATA_DIR, "tracker.db")
SECRET_KEY_PATH = os.path.join(DATA_DIR, ".smtp_secret.key")
