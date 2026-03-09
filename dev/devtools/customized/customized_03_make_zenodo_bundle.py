"""
Bundles the entire contents of data/library/customized into a single ZIP.
Target: data/export/bundles/OSCAR_library_customized.zip

-------------
To run: 
$env:PYTHONPATH="."; python dev/devtools/customized/customized_03_make_zenodo_bundle.py
-------------
"""

import shutil
import os
import xarray as xr
from pathlib import Path
from oscar._utils.load_config import load_config
from oscar._io.paths import get_customized_library_dir, resolve_data_root

def bundle_customized_library():
    # 1. Setup Paths
    data_root = resolve_data_root()
    # Path to data/library/customized
    custom_dir = data_root / "library" / "customized"
    
    # Path to data/export/bundles
    export_root = data_root / "export" / "customized_bundles"
    export_root.mkdir(parents=True, exist_ok=True)

    if not custom_dir.exists():
        print(f"[ERROR] Source directory not found: {custom_dir}")
        return

    print(f"--- OSCAR CUSTOMIZED BUNDLING ---")
    
    # 2. ZIPPING
    # base_name is the path of the zip without the .zip extension
    zip_filename = "OSCAR_library_customized"
    zip_path = export_root / zip_filename

    try:
        shutil.make_archive(
            base_name=str(zip_path),
            format='zip',
            root_dir=str(custom_dir)
        )
        print(f"  [SUCCESS] Created {zip_filename}.zip from {custom_dir}")
    except Exception as e:
        print(f"  [FAILURE] Could not create bundle: {e}")

    print(f"\nCustomized bundle is ready in:\n{export_root}")

if __name__ == "__main__":
    bundle_customized_library()