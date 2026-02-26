"""
OSCAR DevTool 04: Zenodo Bundler
Action: Injects version metadata and Zips regional library components.
Target: data/export/bundles/

-------------
To run: 
$env:PYTHONPATH="."; python dev/devtools/configured/configured_04_make_zenodo_bundle.py
-------------
"""
import shutil
import os
import xarray as xr
from pathlib import Path
from oscar._utils.load_config import load_config
from oscar._io.paths import get_configured_library_dir, resolve_data_root

def bundle_library():
    # 1. Load Specs from Single Source of Truth
    cfg_full = load_config()
    registry = cfg_full['registry']
    cfg_mode = cfg_full['configured_mode']
    
    # Get the official version string from metadata
    version_str = cfg_full['metadata']['configured']['version']
    
    # Registry defines all potential regions and histories
    regions = registry['all_regions']
    hist_list = registry['hist_versions'].keys()
    n_mc = cfg_mode['official_nMC']

    # 2. Setup Export Paths
    data_root = resolve_data_root()
    export_root = data_root / "export" / "bundles"
    export_root.mkdir(parents=True, exist_ok=True)

    print(f"--- OSCAR ZENODO BUNDLING (Version: {version_str}) ---")
    print(f"Targeting HDF5 metadata injection for {n_mc} member ensembles.")

    for hist_name in hist_list:
        for region in regions:
            print(f"Processing: {hist_name} | {region}")
            
            lib_base = get_configured_library_dir() / hist_name
            source_dir = lib_base / region
            
            # 3. Validation List (The Contract of Required Assets)
            # We use the official naming convention established in earlier steps
            required = [
                "forcing_hist.nc", 
                "forcing_scen.nc", 
                f"params_nMC{n_mc}.nc", 
                f"hist_results_nMC{n_mc}.nc",
                f"ini_state_nMC{n_mc}.nc"
            ]
            
            missing = [f for f in required if not (source_dir / f).exists()]
            if missing:
                # We only bundle what exists in the registry
                print(f"  [SKIPPED] {region}: Missing {missing}")
                continue

            # 4. INJECT VERSION METADATA (Scientific Signature)
            for filename in required:
                file_path = source_dir / filename
                print(f"    - Injecting metadata into {filename}...")
                
                # Use .load() inside the context manager to pull all data into RAM
                # then 'ds' is closed automatically at the end of the 'with' block
                with xr.open_dataset(file_path) as ds:
                    ds_loaded = ds.load()
                
                # NOW the file is closed. We can safely overwrite it.
                ds_loaded.attrs['configured_library_version'] = version_str
                ds_loaded.attrs['official_ensemble_size'] = n_mc
                
                # Overwrite using NETCDF4 (HDF5)
                ds_loaded.to_netcdf(file_path, format="NETCDF4", engine="netcdf4")

            # 5. ZIPPING
            # Format: OSCAR_configured_CMIP6_RCP_5reg.zip
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