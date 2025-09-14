import os, sys, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
    
import database

@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    """
    Fresh SQLite file per *test function*.
    Prevents UNIQUE collisions and file locks.
    """
    database.DATABASE = str(tmp_path / "test.db")
    database.init_database()
    yield