"""
OSCAR DevTool: customized_01_make_templates.py
Action: Generates clean CSV templates and a strictly structured Instructional Manual.
Naming Pattern: ForcingType_RegionType_ScenarioName.csv

-------------
To run: 
In terminal, at project root, execute:
$env:PYTHONPATH="."; python dev/devtools/customized/customized_01_make_templates.py
-------------
"""
"""
OSCAR DevTool: customized_01_make_templates.py
Action: Generates IAMC-standard CSV templates for Atmospheric inputs.
"""
import pandas as pd
import yaml
from oscar._utils.load_config import load_config
from oscar._io.paths import get_customized_library_dir

def load_input_registry():
    from oscar._io.paths import PACKAGE_ROOT
    path = PACKAGE_ROOT / "oscar" / "_resources" / "input_species.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_iamc_templates():
    # 1. Setup Paths
    base_dir = get_customized_library_dir() / "templates"
    cfg_full = load_config()
    input_reg = load_input_registry()
    
    # 2. Define structures based on your new Settings Template
    # We focus on the Atmospheric IAMC format you requested
    f_type = "atmospheric"
    type_dir = base_dir / f_type
    type_dir.mkdir(parents=True, exist_ok=True)

    print(f"--- Generating IAMC-Standard Template for {f_type.upper()} ---")

    # --- A. DEFINE THE IAMC COLUMNS ---
    # IAMC format uses years as columns (pivoted)
    years = [2025, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]
    columns = ["Model", "Scenario", "Region", "Variable", "Unit"] + years

    # --- B. PREPARE EXAMPLE DATA ---
    # We create rows matching the specific format you requested
    data = [
        {
            "Model": "Model_Name",
            "Scenario": "Custom_Experiment",
            "Region": "World",
            "Variable": "Emissions|CO2|Energy and Industrial Processes",
            "Unit": "Mt CO2/yr",
            2025: 38000, 2050: 25000, 2100: 0
        },
        {
            "Model": "Model_Name",
            "Scenario": "Custom_Experiment",
            "Region": "World",
            "Variable": "Emissions|CH4",
            "Unit": "Mt CH4/yr",
            2025: 400, 2050: 320, 2100: 200
        },
        {
            "Model": "Model_Name",
            "Scenario": "Custom_Experiment",
            "Region": "World",
            "Variable": "Atmospheric Concentrations|CO2",
            "Unit": "ppm",
            2025: 415, 2050: 445, 2100: 475
        },
        {
            "Model": "Model_Name",
            "Scenario": "Custom_Experiment",
            "Region": "World",
            "Variable": "Emissions|HFC|HFC134a",
            "Unit": "kt HFC134a/yr",
            2025: 15, 2050: 10, 2100: 2
        }
    ]

    # Fill in missing years with 0 or interpolated values (logic can be simple for a template)
    for row in data:
        for y in years:
            if y not in row:
                row[y] = ""

    # --- C. SAVE THE IAMC TEMPLATE ---
    df = pd.DataFrame(data, columns=columns)
    fname = "forcing_atmospheric_Global_1reg_template.csv"
    df.to_csv(type_dir / fname, index=False)
    print(f"  [CSV] Created IAMC template: {f_type}/{fname}")

    # --- D. GENERATE THE README ---
    md = "# OSCAR User Guide: ATMOSPHERIC (IAMC-AR6 Format)\n\n"
    md += "## 📋 OVERVIEW\n"
    md += "This template follows the official IAMC standard used by the IPCC. \n"
    md += "In `settings_experiment.yaml`, ensure you set `format: 'iamc-ar6-public'`.\n\n"
    
    md += "## 🏗 Structure\n"
    md += "- **Model**: Internal ID (e.g., `My_Experiment`).\n"
    md += "- **Scenario**: Name of your experiment.\n"
    md += "- **Region**: Use `World` for global, or standard R5/AR6 region names.\n"
    md += "- **Variable**: The IAMC string (e.g., `Emissions|CO2`).\n"
    md += "- **Unit**: Standard units (Mt CO2/yr, ppm, etc.).\n"
    md += "- **Years**: Numerical values as column headers.\n\n"

    md += "## 🧪 Supported Variables Examples\n"
    md += "| Variable Category | IAMC String Pattern |\n"
    md += "| :--- | :--- |\n"
    md += "| Fossil CO2 | `Emissions|CO2|Energy and Industrial Processes` |\n"
    md += "| Methane | `Emissions|CH4` |\n"
    md += "| Halogens | `Emissions|HFC|{Compound}` or `Emissions|CFC|{Compound}` |\n"

    with open(type_dir / "README_IAMC_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  [DOC] Created {f_type}/README_IAMC_GUIDE.md")

    # --- E. LULCC (Maintain oscar-csv format) ---
    # LULCC is usually too complex for IAMC public format (biomes), 
    # so we keep it as a standard OSCAR transition CSV.
    # [Insert previous LULCC logic here if needed]

    print(f"\nStep 01 Complete. IAMC-Ready templates in {base_dir}")

if __name__ == "__main__":
    build_iamc_templates()