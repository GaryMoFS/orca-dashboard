import sys
import os

# Add the project root to sys.path to ensure modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_orca_api():
    """Verify that orca_api.main can be imported without errors."""
    try:
        import orca_api.main
        assert orca_api.main.app is not None
    except ImportError as e:
        assert False, f"Failed to import orca_api.main: {e}"

def test_import_orca_runtime():
    """Verify that orca_runtime.main can be imported without errors."""
    try:
        import orca_runtime.main
        assert orca_runtime.main.app is not None
    except ImportError as e:
        assert False, f"Failed to import orca_runtime.main: {e}"
