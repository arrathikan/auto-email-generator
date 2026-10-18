import os
import sys
import tempfile
import pytest

# Ensure the 'app' directory is always in sys.path for test execution
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

@pytest.fixture
def temp_db(monkeypatch, tmp_path):
    """
    Provides an isolated SQLite database for testing authentication and database operations.
    """
    db_file = tmp_path / "test_tracker.db"
    key_file = tmp_path / ".smtp_secret.key"
    
    import tracker
    monkeypatch.setattr(tracker, "DB_PATH", str(db_file))
    monkeypatch.setattr(tracker, "DB_DIR", str(tmp_path))
    
    tracker.init_db()
    return db_file
