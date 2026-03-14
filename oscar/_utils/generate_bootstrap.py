"""
OSCAR - Bootstrap Generator
Internal utility to freeze the 'standard' run state.
"""
import xarray as xr
from .._io.paths import get_bootstrap_dir
from .._core.fct_genMC import generate_config
from .._core.mod_process import OSCAR
from .load_config import load_config

def generate_bootstrap():
    # 1. LOAD CONFIGURATION
    full_cfg = load_config()
    
    # Tier 0 specific specs
    cfg = full_cfg['standard_mode']
    
    # NEW: Historical versions are now inside the registry
    registry = full_cfg['registry']
    time_reg = full_cfg['metadata'] # build_end/hist_start now here
    
    hist_type = cfg['hist_type'] # e.g., "CMIP6"
    
    # Resolve dynamic years from the new Registry location
    h_start = time_reg['hist_start']
    h_end = registry['hist_versions'][hist_type]['hist_end']
    s_start = registry['hist_versions'][hist_type]['scen_start']
    s_end = cfg['run_range'][1] # pulls 2100 from the anchor

    b_dir = get_bootstrap_dir()
    b_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. LOAD PARAMETERS
    from .._core.fct_loadP import load_all_param
    # Use region from standard_mode
    Par0 = load_all_param(mod_region=cfg['region'])
    # Use nMC from standard_mode
    Par = generate_config(Par0, nMC=cfg['nMC'])

    # 3. COMPILE For_hist
    from .get_SSP_drivers import For_hist
    print(f"Compiling {hist_type} historical forcings up to {h_end}...")
    
    # Move static parameters from For to Par
    Par = xr.merge([
        Par, 
        For_hist.drop_vars([VAR for VAR in For_hist if 'year' in For_hist[VAR].dims])
    ])
    
    # Filter For_hist for year-dimension variables only
    For_hist = For_hist.drop_vars([VAR for VAR in For_hist if 'year' not in For_hist[VAR].dims])
    For_hist = For_hist.sel(year=slice(h_start, h_end)).fillna(0.)
    
    # 4. SAVE PARAMETERS & HISTORICAL FORCINGS
    Par.to_netcdf(b_dir / "parameters_mc_standard.nc")
    For_hist.to_netcdf(b_dir / "forcing_hist_standard.nc")
    print(f"Par and For_hist saved (Years: {h_start}-{h_end}).")

    # 5. PREPARE & SAVE SCENARIO FORCINGS
    from .get_SSP_drivers import For_scen
    # Scenario starts at the dynamic scen_start (e.g., 2015 for CMIP6)
    For_scen = For_scen.sel(year=slice(s_start, s_end))
    For_scen.to_netcdf(b_dir / "forcing_scen_standard.nc")
    print(f"For_scen saved (Years: {s_start}-{s_end}).")

    # 6. RUN HISTORICAL & FREEZE STATE    
    print(f"Running historical simulation ({h_start} to {h_end})...")
    Out_hist = OSCAR(Ini=None, Par=Par, For=For_hist)
    
    # Save a subset of variables (Tier 0 Core variables) to reduce size
    # This uses the 'var_select' defined in standard_mode
    Out_hist_select = Out_hist[cfg['var_select']]
    Out_hist_select.to_netcdf(b_dir / "output_hist_standard.nc")
    
    # Save last year state as initial condition for future scenario runs
    Ini = Out_hist.isel(year=-1, drop=True)
    Ini.to_netcdf(b_dir / "scen_initial_state_standard.nc")

    print(f"Bootstrap generation complete in {b_dir}")

if __name__ == "__main__":
    print("Initializing bootstrap generation using standard_mode config...")
    generate_bootstrap()