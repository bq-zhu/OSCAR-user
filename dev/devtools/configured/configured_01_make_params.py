"""
OSCAR DevTool: configured_01_make_params.py
Internal utility to generate official regional parameter sets 
supporting all operation tiers (Configured & Customized).

Action: Generates the official nMC parameter sets for all regions 
        defined in config.yaml. 
        #TODO: implement the standard scientific constrain step here later.
Output: params_nMC{n}.nc
-------------
To run: 
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/configured/configured_01_make_params.py
-------------
"""
import xarray as xr
from oscar._utils.load_config import load_config
from oscar._io.paths import get_configured_library_dir
from oscar._core.fct_loadP import load_all_param
from oscar._core.fct_genMC import generate_config

def build_parameter_library():
    # 1. Load the Full Config (The Source of Truth)
    cfg_full = load_config()
    
    # Use Registry for 'What is possible' (Covers both Configured & Customized)
    registry = cfg_full['registry']
    # Use Mode for 'How to build' (Ensemble size)
    cfg_mode = cfg_full['configured_mode']
    
    # Build for all regions and all active historical versions in the registry
    regions = registry['all_regions']
    hist_types = registry['hist_versions'].keys() 
    n_mc = cfg_mode['official_nMC']

    print(f"--- OSCAR LIBRARY BUILD: Step 01 - Parameters (nMC={n_mc}) ---")
    print(f"Building for all regions to support Standard, Configured, and Customized Tiers.")

    for hist_type in hist_types:
        for region in regions:
            # 2. Path Setup
            out_folder = get_configured_library_dir() / hist_type / region
            out_folder.mkdir(parents=True, exist_ok=True)
            
            # The official filename template
            out_file = out_folder / f"params_nMC{n_mc}.nc"
            
            if out_file.exists():
                print(f"  [SKIPPED] {hist_type} | {region}: File already exists.")
                continue

            print(f"  [WORKING] {hist_type} | {region}: Generating official parameter set...")

            # 3. Scientific Logic
            try:
                # Load primary parameters for the specific region
                par0 = load_all_param(mod_region=region)
                
                # Generate Monte Carlo ensemble
                par_mc = generate_config(par0, nMC=n_mc)
                
                # 4. Save to Library
                # Switched to NETCDF4 (HDF5) for better performance and compression
                # Optional: use encoding={'var': {'zlib': True, 'complevel': 4}} for compression
                par_mc.to_netcdf(out_file, format="NETCDF4", engine="netcdf4")
                print(f"  [SUCCESS] Saved to {out_file} (HDF5 format)")
                
            except Exception as e:
                print(f"  [ERROR] {hist_type} | {region}: Build failed. Reason: {e}")

    print("\nStep 01 Complete: Parameter sets are built for all scientific tiers.")

if __name__ == "__main__":
    build_parameter_library()