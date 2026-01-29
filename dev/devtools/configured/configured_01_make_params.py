"""
OSCAR DevTool: configured_01_make_params.py

Action: Generates the official nMC parameter sets for all regions 
        defined in config.yaml. 
        #TODO: implement the standard scientific constrain step here later.
Output: params_nMC{n}.nc

-------------
To run: 
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/configured_01_make_params.py
-------------
"""
import os
import xarray as xr
from oscar._utils.load_config import load_config
from oscar._io.paths import get_configured_dir
from oscar._core.fct_loadP import load_all_param
from oscar._core.fct_genMC import generate_config

def build_parameter_library():
    # 1. Load specs from Single Source of Truth (YAML)
    full_cfg = load_config()
    cfg = full_cfg['configured_options']
    
    # Updated keys to match your new naming convention
    regions = cfg['region_list']
    n_mc = cfg['official_nMC']
    
    # Logic iterates through available history versions
    hist_types = cfg['hist_list'].keys()

    print(f"--- OSCAR LIBRARY BUILD: Parameters (nMC={n_mc}) ---")

    for hist_type in hist_types:
        for region in regions:
            # 2. Path Setup
            # Target: data/configured/CMIP6/RCP_5reg/
            out_folder = get_configured_dir() / hist_type / region
            out_folder.mkdir(parents=True, exist_ok=True)
            out_file = out_folder / f"params_nMC{n_mc}.nc"
            
            if out_file.exists():
                print(f"  [SKIPPED] {hist_type} | {region}: File already exists.")
                continue

            print(f"  [WORKING] {hist_type} | {region}: Generating official parameter set...")

            # 3. Scientific Logic
            try:
                # Load primary parameters for this specific region
                par0 = load_all_param(mod_region=region)
                
                # Generate Monte Carlo ensemble
                # NOTE: This is where the 'constrain' function will be inserted later
                par_mc = generate_config(par0, nMC=n_mc)
                
                # 4. Save to Library (using NetCDF3 for network drive stability)
                par_mc.to_netcdf(out_file, format="NETCDF3_64BIT")
                print(f"  [SUCCESS] Saved to {out_file}")
                
            except Exception as e:
                print(f"  [ERROR] {region}: Failed to generate params. Reason: {e}")

    print("\nStep 01 Complete: All regional parameters are ready.")

if __name__ == "__main__":
    build_parameter_library()