"""
OSCAR - Standard Workflow
Description: Fast verification using bootstrap starter-kit.
"""
import xarray as xr
from .._core.mod_process import OSCAR
from .._io.paths import get_bootstrap_dir, get_out_dir
from .._utils.load_config import load_config
from .._utils.metadata import apply_variable_metadata
from .._viz import plot_timeseries_summary

def run_standard(show_plot=True, run_model=True, **kwargs):
    # 1. Load instructions from YAML
    cfg_full = load_config()
    cfg = cfg_full['standard_mode']
    registry = cfg_full['registry']
    
    # Resolve split year and range from the registry/mode
    hist_type = cfg['hist_type']
    hist_end_year = registry['hist_versions'][hist_type]['hist_end']
    scen_start_year = registry['hist_versions'][hist_type]['scen_start']
    run_end_year = cfg['run_range'][1]
    
    b_dir = get_bootstrap_dir()
    out_dir = get_out_dir() / "standard_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "oscar_standard_results.nc"

    if run_model:
        # 2. Load the "Starter Kit" from internal package resources
        print(f"Loading bootstrap data ({hist_type} baseline)...")
        Par = xr.open_dataset(b_dir / "parameters_mc_standard.nc").load()
        For = xr.open_dataset(b_dir / "forcing_scen_standard.nc").load()
        Out_hist = xr.open_dataset(b_dir / "output_hist_standard.nc").load()
        Ini = xr.open_dataset(b_dir / "scen_initial_state_standard.nc").load()
        
        # Slicing forcing based on the resolved years
        For = For.sel(year=slice(scen_start_year, run_end_year))
        
        # 3. Run the model projection
        print(f"Running OSCAR projection (Standard Mode)...")
        Out_scen = OSCAR(Ini=Ini, Par=Par, For=For, nt=4)
        
        # Select variables defined in the standard_mode
        vars_to_save = _flatten_list(cfg['var_select'])
        Out_scen_sel = Out_scen[vars_to_save]
        
        # Ensure historical results match the variable selection
        Out_all = xr.concat([Out_hist[vars_to_save], Out_scen_sel], dim='year')

        # 4. Apply Metadata Registration
        print("Applying scientific metadata...")
        Out_all = apply_variable_metadata(Out_all)

        # 5. Save results
        Out_all.to_netcdf(out_file, engine="h5netcdf")
        print(f"Success! Data saved to: {out_file}")
        
    else:
        # --- PLOT ONLY MODE ---
        if not out_file.exists():
            raise FileNotFoundError(f"No results found. Run with run_model=True first.")
        Out_all = xr.open_dataset(out_file).load()

    # 6. Generate Summary Plots
    plot_timeseries_summary(
        ds=Out_all, 
        split_year=hist_end_year, 
        var_list=_flatten_list(cfg['var_select']), 
        out_dir=out_dir, 
        show_plot=show_plot
    )
    
    return Out_all

def _flatten_list(nested):
    """Helper to handle YAML anchor nesting."""
    flat = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(_flatten_list(item))
        else:
            flat.append(item)
    return flat