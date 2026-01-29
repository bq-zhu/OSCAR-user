"""
OSCAR DevTool: configured_03_make_historical_runs.py
Action: Executes historical simulations. Saves both the full historical 
        time-series and the final-year initial state for future runs.
Input:  params_nMC{n}.nc, forcing_hist.nc
Output: hist_results_nMC{n}.nc, ini_state_nMC{n}.nc

-------------
To run: 
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/configured_03_make_historical_runs.py
-------------
"""
import xarray as xr
import time
from oscar._utils.load_config import load_config
from oscar._io.paths import get_configured_dir
from oscar._core.mod_process import OSCAR

def run_library_history():
    full_cfg = load_config()
    cfg = full_cfg['configured_options']
    
    nMC = cfg['official_nMC']
    regions = cfg['region_list']
    hist_specs = cfg['hist_list'] 
    var_list = cfg['var_list']

    print(f"--- OSCAR LIBRARY BUILD: Historical Runs ---")

    for region in regions:
        for hist_name, hist_end in hist_specs.items():
            print(f"\n>>> Processing: {region} | {hist_name} (to {hist_end})")
            
            lib_dir = get_configured_dir() / hist_name / region
            param_file = lib_dir / f"params_nMC{nMC}.nc"
            for_file = lib_dir / "forcing_hist.nc"
            
            # --- TWO OUTPUT TARGETS ---
            out_file = lib_dir / f"hist_results_nMC{nMC}.nc"
            ini_file = lib_dir / f"ini_state_nMC{nMC}.nc"

            if out_file.exists() and ini_file.exists():
                print(f"  [SKIPPED] Files already exist.")
                continue

            print(f"  [Action] Loading inputs...")
            Par = xr.open_dataset(param_file).load()
            For = xr.open_dataset(for_file).load()

            # 5. EXECUTION
            print(f"  [Action] Running OSCAR (1750-{hist_end})...")
            run_start = time.time()
            
            # var_keep=None would only keep prognostic vars. 
            # We use var_list to ensure fluxes like D_Focean are kept.
            Out_hist = OSCAR(Ini=None, Par=Par, For=For, var_keep=var_list)
            
            # 6. SAVE TIME-SERIES (Reduced variables for library size)
            print(f"  [Action] Saving historical time-series...")
            Out_hist_sel = Out_hist[var_list]
            Out_hist_sel.to_netcdf(out_file, format="NETCDF3_64BIT")
            
            # 7. SAVE INITIAL STATE (All variables, but only the last year)
            print(f"  [Action] Freezing state for year {hist_end}...")
            # We take the last year. Ini needs EVERYTHING (all diagnostic/prognostic vars)
            # to restart the model correctly, so we don't slice var_list here.
            Ini_state = Out_hist.isel(year=-1, drop=True).load()
            Ini_state.to_netcdf(ini_file, format="NETCDF3_64BIT")
            
            elapsed = (time.time() - run_start) / 60
            print(f"  [SUCCESS] Finished in {elapsed:.1f} minutes.")

if __name__ == "__main__":
    run_library_history()