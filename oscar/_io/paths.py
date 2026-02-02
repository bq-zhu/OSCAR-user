"""
OSCAR Path Management Utility
Location: oscar/_io/paths.py

Main Logic:
    1. PACKAGE_ROOT: Identifies the repository root (OSCAR-user/).
    2. Settings: Stores user preferences in PACKAGE_ROOT/.oscar_settings.json.
    3. Bootstrap: Fixed internal path for 'standard' mode (small files).
    4. Data Root: Resolved path for large scientific libraries (Configured mode).
"""

import os
import json
from pathlib import Path

# 1. IDENTIFY PACKAGE ROOT
# Path logic: oscar/_io/paths.py -> _io -> oscar -> OSCAR-user/
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent

# 2. PERMANENT SETTINGS CONFIG (Local to the repository)
# By saving here, deleting the repository removes all user traces.
SETTINGS_FILE = PACKAGE_ROOT / ".oscar_settings.json"

# 3. INTERNAL BOOTSTRAP LOCATION (Small files shipped with code)
# Used for 'standard' mode
INTERNAL_BOOTSTRAP_DIR = PACKAGE_ROOT / "oscar" / "_resources" / "bootstrap"

def set_data_dir(path=None):
    """
    Sets the global data directory permanently for this user.
    If no path is provided, it defaults to [Project Root]/data/
    """
    if path is None:
        # Default option: Create/use 'data' folder in the repo root
        target = PACKAGE_ROOT / "data"
    else:
        target = Path(path).expanduser().resolve()
    
    # Ensure the directory exists
    target.mkdir(parents=True, exist_ok=True)
    # Save to JSON
    settings = {"data_dir": str(target)}
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
        
    print(f"[OSCAR] User data directory set to: {target}")

def get_user_data_dir() -> Path:
    """
    Retrieves the saved data directory from the local settings file.
    Provides validation if the path is inaccessible.
    Returns None if never set. 
    """
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                path = Path(data["data_dir"])

            # --- THE VALIDATION CHECK ---
            if not path.exists():
                print(f"\n{'!'*60}")
                print(f"[!] WARNING: Your saved data directory is no longer accessible:")
                print(f"    Path: {path}")
                print("\nPlease review the path above or set a new one by running:")
                print("    oscar.set_data_dir('/new/path')")
                print(f"{'!'*60}\n")
                return None
            
            return path
        except (KeyError, json.JSONDecodeError):
            return None
    return None

# --- PUBLIC PATH RESOLVERS ---

def resolve_data_root(user_provided=None):
    """
    Finds the data library root.
    Order of priority: 
    1. Manual argument to function
    2. Setting in .oscar_settings.json
    3. Return None (Handled by run.py Welcome Guide)
    """
    root = user_provided or get_user_data_dir()
    
    if root is None:
        print("\n[OSCAR] No data directory configured. Please set one to proceed.\n")
        # DO NOT raise ValueError here anymore. 
        # Just return None so run.py can show the Welcome Guide.
        return None
        
    return Path(root)

def get_in_dir(user_provided=None):
    """
    Returns the Path to the raw input data (drivers, etc.).
    Points to {data_root}/input_data/
    Enforces a strict check to ensure the library is present.
    """
    # 1. Resolve the base data directory (saved setting or user arg)
    root = resolve_data_root(user_provided)
    
    # 2. Point to the input_data subfolder
    path = root / "input_data"

    # 3. STRICT CHECK: Ensure the library is present before proceeding
    if not path.exists():
        # Using a clear, bordered message for the user
        msg = (
            f"\n{'!'*60}\n"
            f"[OSCAR ERROR] Scientific input data missing.\n"
            f"Location: {path}\n\n"
            f"REQUIRED ACTION:\n"
            f"Please download the input library first. (Step to be finalized)\n"
            f"{'!'*60}\n"
        )
        raise FileNotFoundError(msg)
    
    return path.resolve()

def get_bootstrap_dir():
    """Returns the internal path for 'standard' mode bootstrap files."""
    return INTERNAL_BOOTSTRAP_DIR.resolve()

def get_out_dir(user_provided=None):
    """
    Determines where model results should be saved.
    Logic: User Argument > User Data Subfolder > Package Root Default.
    """
    if user_provided:
        path = Path(user_provided)
    else:
        # Check if a persistent data directory is set
        user_data_root = get_user_data_dir()
        if user_data_root:
            # Save results in the large data drive
            path = user_data_root / "results"
        else:
            # Default fallback to the project root
            print("\n[OSCAR] No data directory configured. Using default results path.\n") # this is likely never used
            path = PACKAGE_ROOT / "data" / "results"

    path = path.expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_configured_dir(data_dir=None):
    """Entry point for all files used in configured mode."""
    return resolve_data_root(data_dir) / "library" / "configured"