"""
OSCAR Data Handlers
Architecture: Specialized Variable Handlers + Specialized Regional Handlers
"""
import pandas as pd
import xarray as xr
import numpy as np
import yaml
from .paths import PACKAGE_ROOT
from .._core.fct_loadP import load_all_param
from .._core.fct_misc import aggreg_region

# --- SHARED UTILS ---

def load_var_mapping(format_type):
    """Loads the translation registry from resources."""
    map_name = f"vars_{format_type}_map.yaml"
    path = PACKAGE_ROOT / "oscar" / "_resources" / map_name
    if not path.exists():
        raise FileNotFoundError(f"[OSCAR] Missing mapping registry: {map_name}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _melt_and_clean(csv_path):
    """Standardizes Wide/Long CSV into a clean Tidy DataFrame."""
    df = pd.read_csv(csv_path)
    year_cols = [c for c in df.columns if str(c).replace('.','').isdigit()]
    if year_cols:
        id_vars = [c for c in df.columns if c not in year_cols]
        df = df.melt(id_vars=id_vars, value_vars=year_cols, var_name='Year', value_name='Value')
    else:
        df.columns = [str(c).capitalize() for c in df.columns]
    
    df['Year'] = df['Year'].astype(float).astype(int)
    df['Value'] = df['Value'].astype(float)
    return df

# --- STEP 1: VARIABLE TRANSLATORS ---

def handle_atmospheric_vars(csv_path, format_type):
    """
    Step 1A: Chemical and Unit Translation for Emissions and RF.
    (Note: Concentration anomaly logic removed as per request)
    """
    df = _melt_and_clean(csv_path)
    mapping = load_var_mapping(format_type)

    df['oscar_var'] = None
    df['oscar_id'] = None

    # Categories limited to non-concentration drivers here
    for cat in ['emissions', 'radiative_forcing']:
        if cat not in mapping: continue
        for iamc_name, data in mapping[cat].items():
            mask = df['Variable'] == iamc_name
            if mask.any():
                o_var, o_id, math_str = data[0], data[1], data[2]
                df.loc[mask, 'Value'] *= pd.eval(math_str)
                df.loc[mask, 'oscar_var'] = o_var
                df.loc[mask, 'oscar_id'] = o_id

    df = df.dropna(subset=['oscar_var'])
    ds = df.pivot_table(index=['Scenario', 'Year', 'Region', 'oscar_id'], 
                        columns='oscar_var', values='Value').to_xarray()
    
    ds = ds.rename({'Scenario': 'scen', 'Year': 'year', 'Region': 'reg_input', 'oscar_id': 'species'})
    if 'E_Xhalo' in ds: ds = ds.rename({'species': 'spc_halo'})
    return ds

def handle_lulcc_vars(csv_path):
    """
    Step 1B: Translates LULCC variables into a 5D pivot structure.
    """
    df = _melt_and_clean(csv_path)
    ds = df.pivot_table(index=['Scenario', 'Year', 'Region', 'Bio_from', 'Bio_to'], 
                        columns='Variable', values='Value').to_xarray()
    
    return ds.rename({'Scenario': 'scen', 'Year': 'year', 'Region': 'reg_input'})

# --- STEP 2: REGIONAL HANDLERS ---

# --- SHARED REGIONAL UTILS ---

def _load_allowed_regions(mod_region):
    """
    Retrieves the official list of region names for a specific resolution.
    Preserves the 0, 1, 2... order from the CSV rows.
    """
    from .paths import get_in_dir
    import csv
    
    reg_meta_path = get_in_dir() / "regions" / "regions_long_name.csv"
    with open(reg_meta_path, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        
        if mod_region not in header:
            raise ValueError(f"[OSCAR] Resolution '{mod_region}' not found in metadata.")
        
        col_idx = header.index(mod_region)
        allowed = []
        for row in reader:
            name = row[col_idx].strip()
            # Preserve order and ensure uniqueness
            if name and name not in allowed:
                allowed.append(name)
    return allowed

# --- REGIONAL HANDLERS ---

def handle_atmospheric_reg(ds, mod_region):
    """
    Step 2A: Regional aggregation for Atmospheric drivers.
    Logic: 
    1. Filter out regions NOT in the official list and NOT 'World'.
    2. Sum the remaining valid rows into Index 0.
    3. Alert the user about any data that was excluded.
    """
    allowed_list = _load_allowed_regions(mod_region)
    user_regions = [str(r) for r in ds.reg_input.values]
    world_aliases = ['World', 'Global', 'Globe', 'Unknown']

    # --- 1. SEPARATE VALID AND MISMATCHED ---
    # Valid = Official names OR any Global name
    valid_names = [r for r in user_regions if r in allowed_list or r in world_aliases]
    mismatched = [r for r in user_regions if r not in valid_names]

    if mismatched:
        print(f"\n[!] WARNING: Data for these regions was EXCLUDED from the total:")
        print(f"    >> {', '.join(mismatched)}")
        print(f"    Reason: They do not match the '{mod_region}' official list.")

    if not valid_names:
        raise ValueError(f"[OSCAR ERROR] No valid regions found for {mod_region} in Atmospheric data.")

    # --- 2. THE TOTAL SUM (of valid data only) ---
    # This turns (Reg_Input, ...) -> (Global_Total, ...)
    ds_valid = ds.sel(reg_input=valid_names)
    ds_glob = ds_valid.sum('reg_input', min_count=1)

    # --- 3. ALIGN WITH MODEL RESOLUTION ---
    # Set the reg_land axis to the correct length for the model
    full_indices = np.arange(len(allowed_list))
    ds_out = ds_glob.expand_dims(reg_land=full_indices).copy()
    
    for var in ds_out.data_vars:
        # Put the sum in Index 0, ensure others are 0.0
        mask = ds_out.reg_land != 0
        ds_out[var] = ds_out[var].where(~mask, 0.0)

    # --- 4. TEMPORAL INTERPOLATION ---
    year_range = np.arange(int(ds_out.year.min()), int(ds_out.year.max()) + 1)
    return ds_out.interp(year=year_range, method="linear").fillna(0.0)


def handle_lulcc_reg(ds, mod_region):
    """
    Step 2B: Regional alignment for LULCC drivers.
    Logic: STRICT MATCHING. Reindexes to full model shape.
    """
    allowed_list = _load_allowed_regions(mod_region)
    user_regions = [str(r) for r in ds.reg_input.values]
    
    # --- MISMATCH CHECK ---
    valid_names = [r for r in user_regions if r in allowed_list]
    mismatched = [r for r in user_regions if r not in allowed_list]

    if mismatched:
        print(f"\n[!] WARNING: LULCC data for these regions was NOT used:")
        print(f"    >> {', '.join(mismatched)}")
        print(f"    Reason: Names do not match the '{mod_region}' official list.")

    if not valid_names:
        raise ValueError(f"[OSCAR ERROR] No valid regions found in LULCC data for {mod_region}.")

    # 1. Map names to official numeric indices
    name_to_idx = {name: i for i, name in enumerate(allowed_list)}
    numeric_coords = [name_to_idx[r] for r in valid_names]
    
    # 2. Slice and reindex
    ds_final = (ds.sel(reg_input=valid_names)
                  .assign_coords(reg_input=numeric_coords)
                  .rename({'reg_input': 'reg_land'})
                  .reindex(reg_land=np.arange(len(allowed_list)), fill_value=0.0))

    # 3. Yearly Interpolation
    year_range = np.arange(int(ds_final.year.min()), int(ds_final.year.max()) + 1)
    return ds_final.interp(year=year_range, method="linear").fillna(0.0)

# --- MASTER COMPILER ---

def compile_custom_forcing(project_path, user_csv_map, mod_region):
    """
    Master orchestrator for Level-2 runs.
    Chains Var Handlers and Reg Handlers.
    """
    ds_final = xr.Dataset()

    # 1. Process Atmosphere
    atmo_cfg = user_csv_map.get('atmospheric', {})
    if atmo_cfg.get('file'):
        print(f"- Compiling atmospheric forcing...")
        ds_atmo_raw = handle_atmospheric_vars(
            project_path / atmo_cfg['file'],
            format_type=atmo_cfg.get('format', 'iamc-ar6-public')
        )
        ds_atmo_final = handle_atmospheric_reg(ds_atmo_raw, mod_region)
        ds_final = xr.merge([ds_final, ds_atmo_final])

    # 2. Process Land-use
    lulcc_cfg = user_csv_map.get('lulcc', {})
    if lulcc_cfg.get('file'):
        print(f"- Compiling land-use forcing...")
        ds_lulcc_raw = handle_lulcc_vars(project_path / lulcc_cfg['file'])
        ds_lulcc_final = handle_lulcc_reg(ds_lulcc_raw, mod_region)
        ds_final = xr.merge([ds_final, ds_lulcc_final])

    return ds_final