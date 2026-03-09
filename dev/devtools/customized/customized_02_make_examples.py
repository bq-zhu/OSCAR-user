"""
OSCAR DevTool: customized_02_make_examples.py
Action: Converts the first scenario of the bootstrap forcing into 
        a single set of clean CSV examples.
Target: data/library/customized/examples/

-------------
To run: 
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/customized/customized_02_make_examples.py
-------------
"""

import xarray as xr
import pandas as pd
from oscar._io.paths import get_bootstrap_dir, get_customized_library_dir

def build_example_data():
    # 1. Setup Paths
    example_dir = get_customized_library_dir() / "examples"
    example_dir.mkdir(parents=True, exist_ok=True)
    
    boot_path = get_bootstrap_dir() / "forcing_scen_standard.nc"
    if not boot_path.exists():
        print(f"[ERROR] Bootstrap forcing missing at {boot_path}")
        return

    print(f"--- Generating Strict Long-Format Reference Examples ---")
    ds = xr.open_dataset(boot_path).load()
    
    # Pick the first scenario
    first_scen = str(ds.scen.values[0])
    print(f"  Source Scenario: {first_scen}")

    # ==========================================================
    # 2. ATMOSPHERIC EXAMPLE (Strict Long Format)
    # ==========================================================
    atm_vars = ["Eff", "E_CH4", "E_N2O", "E_NOX"]
    all_atm_rows = []

    # A. Process standard emissions (Dynamic regional data)
    for code in atm_vars:
        if code not in ds: continue
        # Load exactly what is in the NetCDF dimensions (scen, year, reg_land)
        df = ds[code].sel(scen=first_scen).squeeze().to_dataframe().reset_index()
        
        # Melt to keep internal variable ID while preserving reg_land as found
        df = df.melt(id_vars=['scen', 'year', 'reg_land'], 
                     value_vars=[code], 
                     var_name='variable', 
                     value_name='value')
        all_atm_rows.append(df)
    
    # B. Process halogens (Dynamic regional data, usually 0 in bootstrap)
    if 'E_Xhalo' in ds:
        df_h = ds['E_Xhalo'].sel(scen=first_scen).squeeze().to_dataframe().reset_index()
        # Preserve original dimensions (year, spc_halo)
        # Note: If reg_land isn't in halogen coords, it will be added as 0 for file consistency
        if 'reg_land' not in df_h.columns:
            df_h['reg_land'] = 0
            
        df_h = df_h.rename(columns={'spc_halo': 'variable', 'E_Xhalo': 'value'})
        all_atm_rows.append(df_h[['scen', 'year', 'reg_land', 'variable', 'value']])

    # Combine all Atmospheric and filter zeros
    df_atm_final = pd.concat(all_atm_rows, ignore_index=True)
    df_atm_final = df_atm_final[df_atm_final['value'] != 0].copy()
    
    atm_fname = "forcing_atmospheric_RCP_5reg_oscar-csv_example.csv"
    df_atm_final.to_csv(example_dir / atm_fname, index=False)
    print(f"    [CSV] Created {atm_fname}")

    # ==========================================================
    # 3. LULCC EXAMPLE (Strict Long Format)
    # ==========================================================
    if 'd_Acover' in ds:
        # Extract native LULCC transitions (scen, year, reg_land, bio_from, bio_to)
        df_lu = ds['d_Acover'].sel(scen=first_scen).squeeze().to_dataframe().reset_index()
        
        df_lu = df_lu.rename(columns={'d_Acover': 'value'})
        df_lu['variable'] = 'd_Acover'
        
        # Filter and reorder using original NetCDF naming
        df_lu = df_lu[df_lu['value'] != 0].copy()
        cols = ['scen', 'year', 'reg_land', 'variable', 'bio_from', 'bio_to', 'value']
        df_lu = df_lu[cols]
        
        lu_fname = "lulcc_RCP_5reg_oscar-csv_example.csv"
        df_lu.to_csv(example_dir / lu_fname, index=False)
        print(f"    [CSV] Created {lu_fname}")

    print(f"\nStep 02 Complete. Reference examples saved in {example_dir}")

if __name__ == "__main__":
    build_example_data()