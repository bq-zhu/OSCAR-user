"""
OSCAR - Standard Workflow
Description: Fast verification (2014-2100) using bootstrap starter-kit.
Author: Biqing Zhu
"""
import xarray as xr
from .._core.mod_process import OSCAR
from .._io.paths import get_bootstrap_dir, get_out_dir
from .._utils.load_config import load_config
from .._utils.metadata import apply_variable_metadata
from .._viz import plot_timeseries_summary

def run_standard(show_plot=True, run_model=True,**kwargs):
    # 1. Load instructions from YAML
    cfg = load_config()['bootstrap_specs']
    b_dir = get_bootstrap_dir()
    out_dir = get_out_dir() / "standard_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "oscar_standard_results.nc"

    if run_model:
        # 2. Load the "Starter Kit" from internal package resources
        print("Loading forcing data and parameters...")
        Par = xr.open_dataset(b_dir / "parameters_mc_standard.nc").load()
        For = xr.open_dataset(b_dir / "forcing_scen_standard.nc").load()
        Out_hist = xr.open_dataset(b_dir / "output_hist_standard.nc").load()
        Ini = xr.open_dataset(b_dir / "scen_initial_state_standard.nc").load()
        
        # Slicing forcing based on YAML years
        For = For.sel(year=slice(cfg['scen_start_year'], cfg['scen_end_year']))
        
        # 3. Run the model projection
        print(f"Running OSCAR projection (Standard Mode)...")
        Out_scen = OSCAR(Ini=Ini, Par=Par, For=For, nt=4)
        
        # Select subset of variables and combine into a single timeline
        Out_scen_sel = Out_scen[cfg['var_select']]
        Out_all = xr.concat([Out_hist, Out_scen_sel], dim='year')

        # 4. Apply Metadata Registration (Bridge to variables.yaml)
        print("Applying scientific metadata...")
        Out_all = apply_variable_metadata(Out_all)

        # 5. Save results
        Out_all.to_netcdf(out_file, engine="h5netcdf")
        print(f"Success! Data saved to: {out_file}")
        
    else:
        # --- PLOT ONLY MODE ---
        print(f"Loading existing results for plotting from: {out_file}")
        if not out_file.exists():
            raise FileNotFoundError(f"No results found. Run with run_model=True first.")
        Out_all = xr.open_dataset(out_file).load()

    # 6. Generate Summary Plots (Using centralized viz module)
    # Passed variables: dataset, split_year, var_list, output_dir, show_toggle
    plot_timeseries_summary(
        ds=Out_all, 
        split_year=cfg['hist_end_year'], 
        var_list=cfg['var_select'], 
        out_dir=out_dir, 
        show_plot=show_plot
    )
    
    return Out_all