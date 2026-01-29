"""
OSCAR DevTool: configured_02_make_forcing.py
Action: Aggregates raw drivers and completes the regional parameter sets.
        Synchronized with '_list' naming convention in config.yaml.
Output: forcing_hist.nc, forcing_scen.nc, updated params_nMC{n}.nc

-------------
To run:
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/configured_02_make_forcing.py
-------------
"""
import xarray as xr
import os
from oscar._utils.load_config import load_config
from oscar._io.paths import get_configured_dir
from oscar._utils.get_drivers import compile_ar6_hist_drivers, compile_ssp_scen_drivers

def build_forcing_library():
    # 1. Load instructions from YAML
    full_cfg = load_config()
    cfg = full_cfg['configured_options']
    
    # Updated keys from config.yaml
    hist_specs = cfg['hist_list']  
    regions = cfg['region_list']
    scen_end = cfg['projection_end_year']
    nMC = cfg['official_nMC']

    print(f"--- OSCAR LIBRARY BUILD: Forcing & Parameter Synchronization ---")

    for region in regions:
        print(f"\nProcessing Region: {region}")
        
        # 2. LOAD DATA USING UTILITIES
        # Compiles fresh aggregation for this specific region
        For_hist_raw = compile_ar6_hist_drivers(region)
        For_scen_raw = compile_ssp_scen_drivers(region, For_hist_raw)

        # 3. LOOP THROUGH HISTORICAL VERSIONS
        for hist_name, hist_end_year in hist_specs.items():
            print(f"  [Action] Building {hist_name} (Timeline: 1750-{hist_end_year})...")
            
            lib_dir = get_configured_dir() / hist_name / region
            lib_dir.mkdir(parents=True, exist_ok=True)

            # --- A. SYNCHRONIZE PARAMETERS (Move static variables) ---
            # Identify variables that are NOT time-dependent (like Aland_0)
            static_vars = [v for v in For_hist_raw if 'year' not in For_hist_raw[v].dims]
            
            param_file = lib_dir / f"params_nMC{nMC}.nc"
            if param_file.exists():
                print(f"    - Merging {len(static_vars)} static variables into {param_file.name}...")
                
                with xr.open_dataset(param_file) as ds_temp:
                    Par = ds_temp.load()
                
                # Merge logic with override to handle regional metadata conflicts
                Par_complete = xr.merge([Par, For_hist_raw[static_vars]], compat='override')
                
                # Clear network lock and overwrite with complete set
                os.remove(param_file)
                Par_complete.to_netcdf(param_file, format="NETCDF3_64BIT")
            else:
                print(f"    [Warning] {param_file.name} not found. Run Step 01 first.")

            # --- B. Historical Forcing Logic ---
            # Remove static variables so forcing is purely time-series
            for_h_final = For_hist_raw.drop_vars(static_vars)
            for_h_final = for_h_final.sel(year=slice(1750, hist_end_year)).fillna(0.)

            # --- C. Scenario Forcing Logic ---
            actual_scen_start = hist_end_year + 1
            for_s_final = For_scen_raw.sel(year=slice(actual_scen_start, scen_end))

            # 4. SAVE DRIVERS
            for_h_final.to_netcdf(lib_dir / "forcing_hist.nc", format="NETCDF3_64BIT")
            for_s_final.to_netcdf(lib_dir / "forcing_scen.nc", format="NETCDF3_64BIT")
            
            print(f"    [Success] Drivers saved for {hist_name} in {lib_dir}")

    print("\nStep 02 Complete: Library inputs (Forcing & Params) are synchronized.")

if __name__ == "__main__":
    build_forcing_library()