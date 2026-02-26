# 🧪 Mode: Customized (User Research)

## 💡 Design Logic
The goal of this mode is to provide a **"Scientific Sandbox"** where researchers can run OSCAR with their own experimental forcing data (e.g., a specific carbon tax scenario or a regional reforestation pulse) without modifying the model's core source code.

- **Forcing Assembler:** Uses a "Lazy Filling" logic. If a user provides only CO2 emissions, the model automatically "borrows" other drivers (CH4, Solar, etc.) from an official baseline scenario (SSP) to ensure the simulation remains stable.
- **Project Isolation:** Every study is self-contained in a `projects/{name}/` folder. This ensures custom data and results never mix with the official library.
- **Audit-First:** Automatically generates "Audit Dashboards" to let the researcher visually verify their inputs against official baselines before running the slow physics engine.

## 📂 Data & Metadata
- **User Location:** `{USER_DATA_ROOT}/projects/{project_name}/`
- **Metadata Sources:** 
    - `settings_{experiment}.yaml`: User-defined run instructions.
    - `vars_iamc_map.yaml`: Translation rules for unit conversion and naming.
    - `input_species.yaml`: Registry of allowed input variables and units.

## 👤 User Input Level
**Level 2 (Researcher):** High-flexibility input.
- Users must provide at least one driver file (CSV or NetCDF).
- Users manage their own project settings via YAML.
- **Required Skill:** Basic understanding of CSV formatting and OSCAR variable IDs.

## 🛠 The 6-Step Scientific Pipeline
The logic is implemented in `oscar/_workflows/customized_runs.py` and follows these sequential gates:

### Step 1: Input Acquisition & Translation
- Translates CSV/IAMC data into OSCAR-ready NetCDF using `oscar/_io/handlers.py`.
- Performs wide-to-long "melting" (years as columns → years as rows).
- Applies atomic mass unit conversions (e.g., Mt CO2 to PgC).

### Step 2: Scientific Connection (Scaling)
- Identifies the junction between official history and user scenario.
- If `connect_method: scaling`, it calculates the ratio between user-input and official-library forcing at the transition year and scales the future accordingly.

### Step 3: Baseline Filling & Audit
- Fills missing variables in the user scenario using a chosen baseline (e.g., SSP2-4.5).
- Generates `forcing_audit_*.png` dashboards in the project folder.
- Saves the compiled forcing to `forcing_processed_{experiment}.nc`.

### Step 4: Core Execution (The ODE Solver)
- Resolves the requested **Theme** (e.g., 'carbon' or 'climate').
- Loads the "frozen" model state (`ini_state`) from the official library.
- Executes the OSCAR physics engine.

### Step 5: Result Compilation
- Glues the pre-calculated historical baseline to the new projection.
- Applies metadata (Long Names, Units) from `variables.yaml`.
- Saves final results to `projects/{name}/results/{experiment}_results.nc`.

### Step 6: Diagnostic Visualization
- Generates regional vs. global comparison panels to show how the custom run performs against the official marker SSPs.

---
