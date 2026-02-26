"""
OSCAR DevTool: configured_02_make_forcing.py
Action: Aggregates raw drivers and completes the regional parameter sets.
        Synchronized with '_list' naming convention in config.yaml.
Output: forcing_hist.nc, forcing_scen.nc, updated params_nMC{n}.nc

-------------
To run:
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/configured/configured_02_make_forcing.py
-------------
"""

import xarray as xr
import os
from oscar._utils.load_config import load_config
from oscar._io.paths import get_configured_library_dir
from oscar._utils.get_drivers import compile_ar6_hist_drivers, compile_ssp_scen_drivers

def build_forcing_library():
    # 1. Load instructions from Single Source of Truth
    cfg_full = load_config()
    
    # Use Registry for scientific dimensions (Histories/Regions)
    registry = cfg_full['registry']
    # Use Mode for build specifications
    cfg_mode = cfg_full['configured_mode']
    # Use Metadata for universal time boundaries
    meta = cfg_full['metadata']
    
    regions = registry['all_regions']
    hist_specs = registry['hist_versions']
    n_mc = cfg_mode['official_nMC']
    scen_end = cfg_mode['run_end'] # Pulls 2100 from the YAML anchor

    print(f"--- OSCAR LIBRARY BUILD: Step 02 - Forcing & Parameter Sync ---")

    for region in regions:
        print(f"\nProcessing Region: {region}")
        
        # 2. LOAD DATA USING UTILITIES
        # Compiles raw aggregations for this specific region
        # Note: These are usually massive and contain all years/scenarios
        For_hist_raw = compile_ar6_hist_drivers(region)
        For_scen_raw = compile_ssp_scen_drivers(region, For_hist_raw)

        # 3. LOOP THROUGH ACTIVE HISTORICAL VERSIONS
        for hist_name, years in hist_specs.items():
            h_end = years['hist_end']
            s_start = years['scen_start']
            
            print(f"  [Action] Building {hist_name} (Timeline: 1750-{h_end} -> {s_start}-{scen_end})")
            
            lib_dir = get_configured_library_dir() / hist_name / region
            lib_dir.mkdir(parents=True, exist_ok=True)

            # --- A. SYNCHRONIZE PARAMETERS (Move static variables) ---
            # Identify variables that are NOT time-dependent (drivers like Land Area/etc)
            static_vars = [v for v in For_hist_raw if 'year' not in For_hist_raw[v].dims]
            
            param_file = lib_dir / f"params_nMC{n_mc}.nc"
            if param_file.exists():
                print(f"    - Merging {len(static_vars)} static drivers into {param_file.name}...")
                
                with xr.open_dataset(param_file) as ds_temp:
                    Par = ds_temp.load()
                
                # Merge logic with override to handle regional metadata conflicts
                Par_complete = xr.merge([Par, For_hist_raw[static_vars]], compat='override')
                
                # Overwrite using NETCDF4 (HDF5)
                # We remove the old file first to ensure a clean write
                os.remove(param_file)
                Par_complete.to_netcdf(param_file, format="NETCDF4", engine="netcdf4")
            else:
                print(f"    [Warning] {param_file.name} not found. Run Step 01 first.")

            # --- B. Historical Forcing Logic ---
            # Remove static variables so forcing file is purely time-series data
            for_h_final = For_hist_raw.drop_vars(static_vars)
            for_h_final = for_h_final.sel(year=slice(1750, h_end)).fillna(0.)

            # --- C. Scenario Forcing Logic ---
            # Slices the scenario drivers from the specific switch-over year to library ceiling
            for_s_final = For_scen_raw.sel(year=slice(s_start, scen_end))

            # 4. SAVE DRIVERS (Using HDF5 / NetCDF4)
            for_h_final.to_netcdf(
                lib_dir / "forcing_hist.nc", 
                format="NETCDF4", 
                engine="netcdf4"
            )
            for_s_final.to_netcdf(
                lib_dir / "forcing_scen.nc", 
                format="NETCDF4", 
                engine="netcdf4"
            )
            
            print(f"    [Success] {hist_name} forcings saved in {lib_dir}")

    print("\nStep 02 Complete: Library inputs (Forcing & Params) are synchronized in HDF5.")

if __name__ == "__main__":
    build_forcing_library()