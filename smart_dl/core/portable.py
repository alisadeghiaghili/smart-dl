"""Portable mode — run from USB stick without touching system directories."""
import os
from pathlib import Path


def is_portable() -> bool:
    """Check if portable mode is active."""
    # Check for portable.txt or .portable next to the script
    script_dir = Path(__file__).resolve().parent.parent.parent
    return (script_dir / "portable.txt").exists() or (script_dir / ".portable").exists()


def get_data_dir() -> Path:
    """Get the data directory based on portable mode."""
    if is_portable():
        script_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = script_dir / "data"
    else:
        data_dir = Path(os.environ.get("APPDATA", Path.home())) / "SmartDL"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_path() -> Path:
    """Get the config file path."""
    return get_data_dir() / "config.json"


def get_db_dir() -> Path:
    """Get the database directory."""
    d = get_data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def enable_portable_mode():
    """Create portable.txt to enable portable mode."""
    script_dir = Path(__file__).resolve().parent.parent.parent
    (script_dir / "portable.txt").touch()


def disable_portable_mode():
    """Remove portable.txt to disable portable mode."""
    script_dir = Path(__file__).resolve().parent.parent.parent
    p = script_dir / "portable.txt"
    if p.exists():
        p.unlink()
    p2 = script_dir / ".portable"
    if p2.exists():
        p2.unlink()
