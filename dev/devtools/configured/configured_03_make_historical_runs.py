"""
OSCAR DevTool: configured_03_make_historical_runs.py
Action: Executes historical simulations. Saves both the full historical 
        time-series and the final-year initial state for future runs.
Input:  params_nMC{n}.nc, forcing_hist.nc
Output: hist_results_nMC{n}.nc, ini_state_nMC{n}.nc

-------------
To run: 
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/configured/configured_03_make_historical_runs.py
-------------
"""
import xarray as xr
import time
from oscar._utils.load_config import load_config
from oscar._io.paths import get_configured_library_dir
from oscar._core.mod_process import OSCAR

def run_library_history():
    # 1. Load instructions from Single Source of Truth
    cfg_full = load_config()
    registry = cfg_full['registry']
    cfg_mode = cfg_full['configured_mode']
    
    n_mc = cfg_mode['official_nMC']
    regions = registry['all_regions']
    hist_specs = registry['hist_versions']

    # Identify the full variable scope for the build
    # We combine all 3 tiers to ensure historical outputs support Tier 2 themes
    full_var_list = (
        registry['v_core'] + 
        registry['v_official'] + 
        registry['v_research']
    )

    print(f"--- OSCAR LIBRARY BUILD: Step 03 - Historical Runs ---")
    print(f"Variable scope: {len(full_var_list)} variables (Tiers 0, 1, and 2)")

    for region in regions:
        for hist_name, years in hist_specs.items():
            h_end = years['hist_end']
            print(f"\n>>> Processing: {region} | {hist_name} (to {h_end})")
            
            lib_dir = get_configured_library_dir() / hist_name / region
            param_file = lib_dir / f"params_nMC{n_mc}.nc"
            for_file = lib_dir / "forcing_hist.nc"
            
            # --- TWO OUTPUT TARGETS ---
            out_file = lib_dir / f"hist_results_nMC{n_mc}.nc"
            ini_file = lib_dir / f"ini_state_nMC{n_mc}.nc"

            if out_file.exists() and ini_file.exists():
                print(f"  [SKIPPED] Files already exist.")
                continue

            # 2. LOAD INPUTS
            print(f"  [Action] Loading inputs (HDF5)...")
            Par = xr.open_dataset(param_file).load()
            For = xr.open_dataset(for_file).load()

            # 3. EXECUTION
            print(f"  [Action] Running OSCAR (1750-{h_end})...")
            run_start = time.time()
            
            # We run with the full variable list to ensure compatibility 
            # with customized mode themes (land, permafrost, etc.)
            Out_hist = OSCAR(Ini=None, Par=Par, For=For, var_keep=full_var_list)
            
            # 4. SAVE TIME-SERIES (HDF5)
            print(f"  [Action] Saving historical time-series...")
            # Slice only variables defined in the registry tiers
            Out_hist_sel = Out_hist[full_var_list]
            Out_hist_sel.to_netcdf(out_file, format="NETCDF4", engine="netcdf4")
            
            # 5. SAVE INITIAL STATE (HDF5)
            print(f"  [Action] Freezing state for year {h_end}...")
            # Take the last year. Ini needs EVERYTHING (all diagnostic/prognostic vars)
            # to restart the model correctly, so we save the full Out_hist slice.
            Ini_state = Out_hist.isel(year=-1, drop=True).load()
            Ini_state.to_netcdf(ini_file, format="NETCDF4", engine="netcdf4")
            
            elapsed = (time.time() - run_start) / 60
            print(f"  [SUCCESS] Finished in {elapsed:.1f} minutes.")

    print("\nStep 03 Complete: Historical library and initial states are frozen.")

if __name__ == "__main__":
    run_library_history()