# 🚀 Mode: Standard (Verification)

## 💡 Design Logic
The goal of this mode is **Immediate Success**. It allows a new user to verify their installation and the core physics engine without requiring external data setup.
- **Air-Gap:** It is logically isolated from the persistent data path (`set_data_dir`).
- **Speed:** It bypasses the historical simulation (1750-2014) by loading a "frozen" initial state.
- **Portability:** Everything is stored inside the `oscar/` package folder.

## 📂 Data & Metadata
- **Storage Location:** `oscar/_resources/bootstrap/`
- **Metadata Source:** `config.yaml` -> `bootstrap_specs`
- **Files:**
    - `forcing_hist_standard.nc`: historical forcing.
    - `forcing_scen_standard.nc`: scenario forcing.
    - `output_hist_standard.nc`: Historical results for plotting.
    - `params_mc_standard.nc`: (50 MC members) Physical constants.
    - `scen_initial_state_standard.nc`: All internal pool states at 2014.

## 👤 User Input Level: Standard Mode
**Level 0 (Verification):**
- **Inputs (LOCKED):** The user **cannot** specify where input data comes from. The model is hard-coded to use the internal `oscar/_resources/bootstrap/` files.
- **Outputs (FLEXIBLE):** The user **is allowed** to specify an output directory (but not recommended for first time users).
- **Priority:**
    1. If `out_dir` is provided in the command, use that.
    2. If `user_data_root` is provided in `.oscar_settings.json`, use `user_data_root/results/`.
    3. Fall back to `PACKAGE_ROOT/data/results/`.
- **Reasoning:** Result files are tiny (~1.7 MB). Allowing custom output paths lets users organize their tests without risking the integrity of the model's internal data.

## 🛠 Maintenance Pipeline
Run `python -m oscar._utils.generate_bootstrap` if:
1. The OSCAR core equations in `_core/` are modified.
2. The internal metadata standards (units/names) change.