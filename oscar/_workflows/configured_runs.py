"""
OSCAR - Configured Workflow
Scientific projections using official pre-compiled CMIP libraries.
"""
import xarray as xr
from .._utils.load_config import load_config
from .._io.paths import get_configured_dir, get_out_dir
from .._io._download import ensure_configured_library
from .._core.mod_process import OSCAR
from .._utils.metadata import apply_variable_metadata

def run_configured(
    scenario=None,  # user-selected scenario(s)
    region=None,    # user-selected region aggregation (at which level OSCAR runs)
    hist_type=None, # user-selected historical dataset
    variables=None, # user-selected output variables
    show_plot=True, # whether to display summary plots
    run_model=True, # whether to run the model (set False to only plot)
    **kwargs
):
    """
    Scientific projections using official OSCAR library.

    -------------------------------------------------------------------------
    DATA REQUIREMENTS:
    This mode expects a structured library in your specified data directory:
    - {data_root}/configured/{hist_type}/{region}/params_nMC500.nc
    - {data_root}/configured/{hist_type}/{region}/forcing_scen.nc
    - {data_root}/configured/{hist_type}/{region}/hist_results_nMC500.nc
    - {data_root}/configured/{hist_type}/{region}/ini_state_nMC500.nc
    -------------------------------------------------------------------------
    """
    # 1. LOAD CONFIGURATION SPECIFICATIONS
    full_cfg = load_config()
    menu = full_cfg['configured_options']
    defaults = menu['defaults']
    
    # 2. RESOLVE FINAL SELECTIONS
    hist_final   = hist_type or defaults['hist_type']
    region_final = region    or defaults['region']
    
    scen_input   = scenario or defaults['scenario']
    scen_final   = [scen_input] if isinstance(scen_input, str) else list(scen_input)
    
    vars_input   = variables or defaults['variables']
    vars_final   = [vars_input] if isinstance(vars_input, str) else list(vars_input)

    hist_end_year   = menu['hist_list'][hist_final]
    scen_start_year = hist_end_year + 1
    scen_end_year   = menu['projection_end_year']
    
    nMC = menu['official_nMC']

    # Setup Output Path
    out_dir = get_out_dir() / "configured_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"oscar_configured_{hist_final}_{region_final}.nc"

    if run_model:
        # 3. VALIDATION
        _validate_choice(hist_final, menu['hist_list'].keys(), "hist_type")
        _validate_choice(region_final, menu['region_list'], "region")
        for s in scen_final:
            _validate_choice(s, menu['scen_list'], "scenario")
        for v in vars_final:
            _validate_choice(v, menu['var_list'], "variable")

        # 4. LOAD LIBRARY COMPONENTS
        print(f"Loading official library for {region_final} ({nMC} members)...")
        lib_path = ensure_configured_library(hist_final, region_final)
        
        # Load time-series results (for plotting) and the frozen state (for simulation)
        hist_results = xr.open_dataset(lib_path / f"hist_results_nMC{nMC}.nc").load()
        ini_state    = xr.open_dataset(lib_path / f"ini_state_nMC{nMC}.nc").load()
        scen_forcing = xr.open_dataset(lib_path / "forcing_scen.nc").load()
        params       = xr.open_dataset(lib_path / f"params_nMC{nMC}.nc").load()

        # 5. ENSURE COMPLETE LIBRARY
        lib_path = ensure_configured_library(hist_final, region_final)
        print(f"Library components loaded successfully, in : {lib_path}")
        
        # 6. PREPARE INPUTS
        For_scen = scen_forcing.sel(scen=scen_final, year=slice(scen_start_year, scen_end_year))
        # Use the specialized ini_state file which contains all required restart variables
        Ini = ini_state
        
        # 7. EXECUTE PROJECTION
        print(f"Running OSCAR (configured mode) for scenarios: {scen_final}")
        Out_scen = OSCAR(Ini=Ini, Par=params, For=For_scen, nt=4, var_keep=vars_final, **kwargs) #always specify vars_final to make sure rquested variables are saved
        
        # 8. COMBINE & APPLY METADATA
        print("Cleaning results and applying metadata...")
        Out_all = xr.concat([hist_results[vars_final], Out_scen[vars_final]], dim='year')
        Out_all = apply_variable_metadata(Out_all)

        # 9. SAVE
        Out_all.to_netcdf(out_file, format="NETCDF3_64BIT")
        print(f"Success! Data saved to: {out_file}")
    
    else:
        # --- PLOT ONLY MODE ---
        if not out_file.exists():
            raise FileNotFoundError(f"No results found. Run with run_model=True first.")
        Out_all = xr.open_dataset(out_file).load()

    # 10. PLOT SUMMARY
    from .._viz import plot_timeseries_summary
    plot_timeseries_summary(Out_all, hist_end_year, vars_final, out_dir=out_dir, show_plot=show_plot)
    
    return Out_all

def _validate_choice(value, allowed_list, name):
    if value not in allowed_list:
        raise ValueError(f"Invalid {name}: '{value}'. Available: {list(allowed_list)}")