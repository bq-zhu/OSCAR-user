"""
OSCAR DevTool 04: Zenodo Bundler
Action: Validates and Zips regional library components for Zenodo upload.
Target: data/export/bundles/

-------------
To run: 
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/configured_04_make_zenodo_bundle.py
-------------
"""

"""
OSCAR DevTool 04: Zenodo Bundler
Action: Injects version metadata and Zips regional library components.
"""
import shutil
import os
import xarray as xr
from pathlib import Path
from oscar._utils.load_config import load_config
from oscar._io.paths import get_configured_dir, resolve_data_root

def bundle_library():
    # 1. Load Specs from YAML
    full_cfg = load_config()
    cfg = full_cfg['configured_options']
    # Get the  version string (e.g., 2026.con.rc1)
    version_str = full_cfg['metadata']['configured']['version']
    
    regions = cfg['region_list']
    hist_list = cfg['hist_list'] 
    nMC = cfg['official_nMC']

    # 2. Setup Export Paths
    data_root = resolve_data_root()
    export_root = data_root / "export" / "bundles"
    export_root.mkdir(parents=True, exist_ok=True)

    print(f"--- OSCAR ZENODO BUNDLING (Version: {version_str}) ---")

    for region in regions:
        for hist_name in hist_list:
            print(f"Processing: {region} ({hist_name})")
            
            lib_base = get_configured_dir() / hist_name
            source_dir = lib_base / region
            
            # 3. Validation List
            required = ["forcing_hist.nc", "forcing_scen.nc", 
                        f"params_nMC{nMC}.nc", f"hist_results_nMC{nMC}.nc",
                        f"ini_state_nMC{nMC}.nc"]
            
            missing = [f for f in required if not (source_dir / f).exists()]
            if missing:
                print(f"  [ERROR] Skipping {region}: Missing {missing}")
                continue

            # 4. INJECT VERSION METADATA (Scientific Signature)
            # This ensures the NetCDF "remembers" its version forever
            for filename in required:
                file_path = source_dir / filename
                with xr.open_dataset(file_path) as ds:
                    ds_loaded = ds.load()
                    ds_loaded.attrs['configured_library_version'] = version_str
                    # Use NETCDF3 for speed/robustness on network drives
                    ds_loaded.to_netcdf(file_path, format="NETCDF3_64BIT")

            # 5. ZIPPING
            zip_filename = f"OSCAR_configured_{hist_name}_{region}"
            zip_path = export_root / zip_filename
            
            shutil.make_archive(
                base_name=str(zip_path),
                format='zip',
                root_dir=str(lib_base),
                base_dir=region
            )
            print(f"  [SUCCESS] Metadata injected and {zip_filename}.zip created.")

    print(f"\nFinal bundles are ready for upload in:\n{export_root}")

if __name__ == "__main__":
    bundle_library()