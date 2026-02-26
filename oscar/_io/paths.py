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
import shutil

# 1. IDENTIFY PACKAGE ROOT
# Path logic: oscar/_io/paths.py -> _io -> oscar -> OSCAR-user/
PACKAGE_ROOT = Path(__file__).parent.parent.parent

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
    Validates if the physical directory is still accessible.
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

# --- WAREHOUSE (The Source) ---

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

def get_library_dir(user_provided=None):
    """Points to {root}/library/"""
    root = resolve_data_root(user_provided)
    return root / "library" if root else None

def get_configured_library_dir(user_provided=None):
    """Points to {root}/library/configured/"""
    lib = get_library_dir(user_provided)
    return lib / "configured" if lib else None

def get_customized_library_dir(user_provided=None):
    """Points to {root}/library/customized/"""
    lib = get_library_dir(user_provided)
    return lib / "customized" if lib else None

def get_in_dir(user_provided=None):
    """
    Returns the Path to the raw input data (drivers, etc.).
    Points to {data_root}/library/input_data/
    Enforces a strict check to ensure the library is present.
    """
    """Points to {root}/library/input_data/ (The raw sources)"""
    lib = get_library_dir(user_provided)
    
    # 2. Point to the input_data subfolder
    path = lib / "input_data"

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

# --- SANDBOX (The Work) ---

def create_project(project_name):
    """
    Automates the creation of a research sandbox.
    Creates folder and copies standard templates for Customized mode.
    """
    # 1. Resolve Path
    from .paths import get_projects_dir, get_library_dir
    base = get_projects_dir()
    p_path = base / project_name
    
    # 2. Safety Check
    if p_path.exists():
        print(f"\n[OSCAR] Folder '{project_name}' already exists. No changes made.")
        return p_path

    # 3. Create structure
    print(f"\n[OSCAR] Initializing project: {project_name}")
    p_path.mkdir(parents=True, exist_ok=True)
    (p_path / "results").mkdir(exist_ok=True)

    # 4. Copy Templates
    lib_tpl = get_library_dir() / "customized" / "templates"
    if lib_tpl.exists():
        # Copy settings file with correct project suffix
        shutil.copy(lib_tpl / "settings_template.yaml", 
                    p_path / f"settings_{project_name}.yaml")
        print(f"[OSCAR] Setup complete! You can now edit your files in: {p_path}")
    else:
        print("[OSCAR] Warning: Library templates not found. Manual setup required.")
    
    return p_path

def get_projects_dir(user_provided=None):
    """Points to {root}/projects/ where user-defined research lives."""
    root = resolve_data_root(user_provided)
    return root / "projects" if root else None

def resolve_project_path(project_name):
    """
    Finds the SPECIFIC folder for a study by name.
    Location: {data_root}/projects/{project_name}
    """
    if project_name is None:
        return None
        
    base = get_projects_dir()
    if base:
        path = base / project_name
        # We don't auto-create here; we let the workflow handle 
        # validation (check if settings.yaml exists)
        return path
        
    return None

# --- ARCHIVE (The Output) ---

def get_bootstrap_dir():
    """Returns the internal path for 'standard' mode bootstrap files."""
    return INTERNAL_BOOTSTRAP_DIR.resolve()

def get_out_dir(user_provided=None):
    """
    Priority: 1. Argument | 2. UserRoot/results | 3. PackageRoot/data/results
    """
    if user_provided:
        path = Path(user_provided)
    else:
        user_root = get_user_data_dir()
        path = user_root / "results" if user_root else PACKAGE_ROOT / "data" / "results"

    path = path.expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


