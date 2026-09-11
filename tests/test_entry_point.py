import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

ENTRY_PATH = Path(__file__).resolve().parent.parent / "packaging" / "windows" / "entry.py"
spec = importlib.util.spec_from_file_location("win_entry", ENTRY_PATH)
win_entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(win_entry)
run = win_entry.run


def test_entry_run_calls_interactive_main_when_deps_ok():
    """Test that entry run() calls main() when dependencies are satisfied."""
    with patch("smart_dl.main.main") as mock_main:
        result = run()
        assert result == 0
        mock_main.assert_called_once()


def test_entry_frozen_skips_deps_check():
    """Test that frozen executable runs bypass dependency availability checks."""
    with patch.object(sys, "frozen", True, create=True), patch("smart_dl.main.main") as mock_main:
        result = run()
        assert result == 0
        mock_main.assert_called_once()
