# 🔬 Mode: Configured (Scientific Library)

## 💡 Design Logic
This is the **"Official Science"** mode. It provides high-precision, peer-reviewed projections.
- **Efficiency:** The data library is downloaded on-demand by region to save bandwidth.
- **Frozen History:** Simulations from 1750 to 2014 are pre-calculated to allow instant experimentation for pre-configured scenarios.

## 📂 Data & Metadata
- **Storage Location:** `{USER_DATA_ROOT}/library/configured/{hist_type}/{region}/`
- **Metadata Source:** `config.yaml` -> `configured_options`
- **Variable Definitions:** `oscar/_resources/variables.yaml`
- **Core Files:**
    - `forcing_hist.nc`: Time-series historical drivers.
    - `forcing_scen.nc`: Multi-scenario  drivers.
    - `hist_results_nMC500.nc`: Plottable historical baseline.
    - `ini_state_nMC500.nc`: Full restart state (for seamless transition).
    - `params_nMC500.nc`: Complete physics + regional constants.


## 👤 User Input Level
**Level 1 (Applied Scientist):** Choice-based input.
- Users select from the `configured_options` menu (Scenario, Region, Hist_type).
- Technical settings (nMC, time-steps) are fixed by the developer to ensure scientific rigor.

## 🛠 Production Pipeline (Step-by-Step)
1. **01_make_params.py:** Creates the physical MC ensemble.
2. **02_make_forcing.py:** Aggregates raw data (from `input_data`); **Overwrites** Params with `Aland_0`.
3. **03_make_hist_runs.py:** Solves 1750-2014. **TODO:** Add scientific constraint step.
4. **04_make_bundle.py:** Validates, injects version attributes, and zips for Zenodo.