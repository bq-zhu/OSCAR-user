"""
OSCAR - Customized Workflow (Level 2)
Action: Executes user-defined research projects through a gated 4-step pipeline.
"""
import yaml
import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path
from .._utils.load_config import load_config
from .._io.paths import resolve_project_path, get_bootstrap_dir
from .._io.handlers import compile_custom_forcing
from .._io._download import ensure_configured_library
from .._core.mod_process import OSCAR
from .._utils.metadata import apply_variable_metadata

def _validate_choice(value, allowed_list, name):
    """Internal validator that handles potential YAML nesting."""
    def flatten(nested):
        flat = []
        for item in nested:
            if isinstance(item, list): flat.extend(flatten(item))
            else: flat.append(item)
        return flat
    
    flat_allowed = flatten(allowed_list)
    if value not in flat_allowed:
        raise ValueError(f"Invalid {name}: '{value}'. Available: {flat_allowed}")

def run_customized(project=None, experiment=None, **kwargs):
    # --- 0. INITIALIZATION ---
    if not project:
        raise ValueError("[OSCAR] Mode 'customized' requires a project name.")
    
    p_path = resolve_project_path(project)
    exp_label = experiment if experiment else project
    settings_file = p_path / f"settings_{exp_label}.yaml"
    
    if not settings_file.exists():
        raise FileNotFoundError(f"[OSCAR] Missing settings file: {settings_file.name}")

    with open(settings_file, "r") as f:
        u_cfg = yaml.safe_load(f)
    
    # Load Source of Truth
    cfg_full = load_config()
    registry = cfg_full['registry']
    c_mode = cfg_full['customized_mode']
    # Tier 1 used for 'prebuilt' defaults
    t1_mode = cfg_full['configured_mode']
    
    experiment_id = u_cfg.get('experiment_name', exp_label)
    sci_setup = u_cfg.get('scientific_setup', {})

    # Resolve Selections (User Settings -> Registry/Tier Defaults)
    hist_t = sci_setup.get('hist_type', t1_mode['defaults']['hist_type'])
    reg_run = sci_setup.get('model_region', t1_mode['defaults']['region'])
    base_s = sci_setup.get('baseline_forcing', t1_mode['defaults']['scenario'][0])
    end_yr = sci_setup.get('projection_end_year', t1_mode['run_end'])
    connect_method = sci_setup.get('connect_method', 'raw')
    
    # Validation against Registry and Tier 2 Allowed Lists
    _validate_choice(hist_t, c_mode['allowed_hist'], "hist_type")
    _validate_choice(reg_run, c_mode['allowed_regions'], "model_region")
    _validate_choice(base_s, c_mode['allowed_baselines'], "baseline_forcing")

    # Timeline Validation
    y_min = c_mode['allowed_years']['min']
    y_max = c_mode['allowed_years']['max']
    if not (y_min <= int(end_yr) <= y_max):
        raise ValueError(f"Invalid projection_end_year: {end_yr}. Range: {y_min}-{y_max}.")

    # Resolved Scientific Data
    hist_specs = registry['hist_versions'][hist_t]
    hist_end = hist_specs['hist_end']
    scen_start = hist_specs['scen_start']
    n_mc = t1_mode['official_nMC']

    # Assets are loaded from the 'configured' library build
    lib_path = ensure_configured_library(hist_t, reg_run)
    marker_scenarios = c_mode.get('marker_scenarios', ['SSP2-4.5'])

    processed_forcing_file = p_path / f"forcing_processed_{experiment_id}.nc"
    results_file = p_path / "results" / f"{experiment_id}_results.nc"

    # -------------------------------------------------------------------------
    # STEP 1: PRE-PROCESSING FORCING
    # -------------------------------------------------------------------------
    audit_dir = p_path / "forcing_audit"
    registry_file = audit_dir / "source_registry.csv"

    if u_cfg.get('preprocess_forcing', True):
        print(f"[OSCAR] Step 1: Compiling forcing from user inputs...")
        
        user_file_map = u_cfg.get('user_files', {})
        if user_file_map.get('compiled_nc'):
            nc_name = user_file_map['compiled_nc']
            ds_user_raw = xr.open_dataset(p_path / nc_name).load()
        else:
            csv_map = user_file_map.get('csv_inputs', {})
            ds_user_raw = compile_custom_forcing(p_path, csv_map, mod_region=reg_run)

        # Temporal Connection using Tier 1 Prebuilts
        ds_lib_hist = xr.open_dataset(lib_path / "forcing_hist.nc").load()
        ds_lib_scen = xr.open_dataset(lib_path / "forcing_scen.nc").load()
        
        forcing_anchor = ds_lib_hist.sel(year=hist_end, drop=True)
        future_years = np.arange(scen_start, end_yr + 1)
        ds_base_template = ds_lib_scen.sel(scen=base_s, drop=True).sel(year=future_years)

        user_scenarios_expanded = []
        for sn in ds_user_raw.scen.values:
            user_sn = ds_user_raw.sel(scen=sn, drop=True)
            # If user provides overlap with hist_end, handle transition
            if hist_end in user_sn.year.values:
                if connect_method == 'scaling':
                    ratio = forcing_anchor / user_sn.sel(year=hist_end)
                    user_sn = user_sn * ratio
                user_sn = user_sn.sel(year=slice(scen_start, None))

            # Merge user data into baseline template
            full_sn_data = user_sn.combine_first(ds_base_template)
            full_sn_data = xr.concat([forcing_anchor.assign_coords(year=hist_end), full_sn_data], dim='year')
            full_sn_data = full_sn_data.interp(year=np.arange(hist_end, end_yr + 1), method="linear")
            user_scenarios_expanded.append(full_sn_data.sel(year=future_years).expand_dims(scen=[sn]))
        
        ds_user_filled = xr.concat(user_scenarios_expanded, dim='scen')

        # C. Merge with Reference Markers (-ref)
        ds_markers = ds_lib_scen.sel(scen=marker_scenarios, year=future_years)
        
        # Ensure the reference markers are clearly labeled to avoid coordinate conflicts
        ds_markers = ds_markers.assign_coords(scen=[f"{s}-ref" for s in marker_scenarios])
        
        # --- FIX: Use compat='override' to handle overlapping baseline variables (like RF_solar) ---
        print(f"  [OSCAR] Merging user scenarios with reference markers...")
        For_final = xr.merge([ds_user_filled, ds_markers], compat='override')
        
        # --- D. Save Processed Forcing & Source Registry ---
        For_final.to_netcdf(processed_forcing_file, engine="h5netcdf")
        
        # Save Source Registry for Audit
        audit_dir.mkdir(exist_ok=True)
        sources = [{'scenario': sn, 'variable': var} 
                   for sn in ds_user_raw.scen.values 
                   for var in ds_user_raw.data_vars]
        pd.DataFrame(sources).to_csv(registry_file, index=False)

    # -------------------------------------------------------------------------
    # STEP 2: AUDIT FORCING (Visual Check)
    # -------------------------------------------------------------------------
    if u_cfg.get('plot_user_forcing', True):
        from .._viz._plot_forcing import plot_forcing_audit
        print(f"[OSCAR] Step 2: Generating forcing audit check...")
        
        # Load the variable names from the registry file created in Step 1
        if not registry_file.exists():
            # Fallback if Step 1 was skipped: extract vars from the processed file
            ds_audit_ref = xr.open_dataset(processed_forcing_file)
            user_vars_list = [v for v in ds_audit_ref.data_vars if not v.endswith("-ref")]
        else:
            user_vars_df = pd.read_csv(registry_file)
            user_vars_list = user_vars_df['variable'].unique().tolist()
        
        # Load historical reference for the audit plots
        ds_lib_hist = xr.open_dataset(lib_path / "forcing_hist.nc").load()
        
        # Execute Audit (passing the list of variables, not the file path)
        plot_forcing_audit(
            xr.open_dataset(processed_forcing_file), 
            ds_lib_hist, 
            user_vars_list, 
            audit_dir
        )

    # -------------------------------------------------------------------------
    # STEP 3: RUN MODEL (Physics Engine)
    # -------------------------------------------------------------------------
    # Resolve the variables requested for output based on the Tier 2 theme
    theme_vars = _resolve_theme_vars(
        u_cfg.get('theme', 'climate'), 
        u_cfg.get('custom_vars')
    )
    
    if u_cfg.get('run_model', True):
        print(f"[OSCAR] Step 3: Starting simulation for {experiment_id}...")
        
        # Load Tier 1 prebuilt assets (anchors for the Tier 2 run)
        params = xr.open_dataset(lib_path / f"params_nMC{n_mc}.nc").load()
        ini_state = xr.open_dataset(lib_path / f"ini_state_nMC{n_mc}.nc").load()
        hist_results = xr.open_dataset(lib_path / f"hist_results_nMC{n_mc}.nc").load()
        
        # Execute the projection
        # nt=4 for parallel solver execution
        Out_scen = OSCAR(
            Ini=ini_state, 
            Par=params, 
            For=xr.open_dataset(processed_forcing_file), 
            nt=4, 
            var_keep=theme_vars, 
            **kwargs
        )
        
        # Combine historical pre-run results with the new customized projection
        print(f"  [OSCAR] Finalizing results and applying metadata...")
        Out_all = xr.concat(
            [hist_results[theme_vars], Out_scen[theme_vars]], 
            dim='year'
        )
        Out_all = apply_variable_metadata(Out_all)
        
        # Save to project results folder
        results_file.parent.mkdir(exist_ok=True)
        Out_all.to_netcdf(results_file, engine="h5netcdf")
        
    else:
        print(f"[OSCAR] Step 3: Skipping physics. Loading existing: {results_file.name}")
        if not results_file.exists():
            raise FileNotFoundError(
                f"Results file {results_file.name} missing. Set run_model: true."
            )
        Out_all = xr.open_dataset(results_file).load()
    
    # -------------------------------------------------------------------------
    # STEP 4: PLOT
    # -------------------------------------------------------------------------
    if u_cfg.get('plot_outputs', True):
        from .._viz._plot_regional import plot_regional_comparison
        plot_regional_comparison(xr.open_dataset(results_file), theme_vars, results_file.parent, hist_end)

    return xr.open_dataset(results_file)

def _resolve_theme_vars(theme, custom_list):
    cfg = load_config()
    themes = cfg['customized_mode']['output_themes']
    if theme == "custom": return custom_list
    
    raw_vars = themes.get(theme, themes['climate'])
    def flatten(nested):
        flat = []
        for item in nested:
            if isinstance(item, list): flat.extend(flatten(item))
            else: flat.append(item)
        return flat
    return flatten(raw_vars)