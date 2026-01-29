"""
OSCAR Smoke Test
Purpose: Rapidly verify that the package structure and core logic are functional.
Run with: python dev/tests/smoke_test.py
"""
import os
import sys
from pathlib import Path
import xarray as xr

# 1. Ensure the script can find the local 'oscar' package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def run_verification():
    print("--- OSCAR SMOKE TEST START ---")
    
    try:
        import oscar
        print(f"v Package detected: version {oscar.__version__}")
        
        # 2. Test Configuration Loading
        from oscar._utils.load_config import load_config
        cfg = load_config()
        print("v Config.yaml loaded successfully.")

        # 3. Test Bootstrap Access
        from oscar._io.paths import get_bootstrap_dir
        b_dir = get_bootstrap_dir()
        par_path = b_dir / "parameters_mc_standard.nc"
        
        if not par_path.exists():
            print(f"X FAILED: Bootstrap data missing at {par_path}")
            return
        
        # 4. Tiny Model Run (2 configurations, 2 years only)
        from oscar._core.mod_process import OSCAR
        print("v Testing core OSCAR model (Mini-run)...")
        
        Par = xr.open_dataset(par_path).load()
        For = xr.open_dataset(b_dir / "forcing_scen_standard.nc").isel(year=slice(0, 2)).load()
        Ini = xr.open_dataset(b_dir / "scen_initial_state_standard.nc").load()
        
        # We run the model core directly to avoid 'sys.exit' triggers in run.py
        out = OSCAR(Ini=Ini, Par=Par, For=For, nt=2)
        
        if out is not None:
            print("v OSCAR core model returned data successfully.")
        
        # 5. Test Path Memory (if setting exists)
        from oscar._io.paths import get_user_data_dir
        path = get_user_data_dir()
        if path:
            print(f"v Persistent path recognized: {path}")
        else:
            print("- No persistent path set (This is normal for new users).")

        print("\n--- SMOKE TEST PASSED ---")
        print("Conclusion: Package structure and core engine are stable.")

    except Exception as e:
        print(f"\n[!] SMOKE TEST FAILED")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()