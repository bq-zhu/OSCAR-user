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
    f_type = "atmospheric"
    type_dir = base_dir / f_type
    type_dir.mkdir(parents=True, exist_ok=True)

    print(f"--- Generating IAMC-Standard Template for {f_type.upper()} ---")

    # 2. Structure & Example Data
    years = [2025, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]
    columns = ["Model", "Scenario", "Region", "Variable", "Unit"] + years

    data = [
        {"Model": "IAMC_Source", "Scenario": "Custom_Scenario", "Region": "World", 
         "Variable": "Emissions|CO2|Energy and Industrial Processes", "Unit": "Mt CO2/yr", 2025: 38000, 2100: 0},
        {"Model": "IAMC_Source", "Scenario": "Custom_Scenario", "Region": "World", 
         "Variable": "Emissions|CH4", "Unit": "Mt CH4/yr", 2025: 400, 2100: 200},
        {"Model": "IAMC_Source", "Scenario": "Custom_Scenario", "Region": "World", 
         "Variable": "Emissions|HFC|HFC134a", "Unit": "kt HFC134a/yr", 2025: 15, 2100: 2},
        {"Model": "IAMC_Source", "Scenario": "Custom_Scenario", "Region": "World", 
         "Variable": "Atmospheric Concentrations|CO2", "Unit": "ppm", 2025: 415, 2100: 475}
    ]

    # 3. Save CSV
    df = pd.DataFrame(data, columns=columns).fillna("")
    fname = "forcing_atmospheric_iamc-ar6-public_template.csv"
    df.to_csv(type_dir / fname, index=False)
    print(f"  [CSV] Created IAMC template: {f_type}/{fname}")

    # 4. Generate Standardized README
    md = "# OSCAR User Guide: ATMOSPHERIC (IAMC-AR6 Format)\n\n"
    md += "## 📋 OVERVIEW\n"
    md += "This template follows the official **IAMC-AR6** public nomenclature.\n"
    md += "In your `settings_my-experiment.yaml`, ensure you set:\n"
    md += "```yaml\natmospheric:\n  file: 'your_file.csv'\n  format: 'iamc-ar6-public'\n```\n\n"
    
    md += "## 🏗 Structure\n"
    md += "- **Wide Format**: Years are represented as columns.\n"
    md += "- **Region**: Use `World` for global or standard R5/AR6 region names.\n"
    md += "- **Variables**: Must match standard IAMC strings.\n\n"

    md += "## 🔬 Registry Mapping Used\n"
    md += "For full list of variables and units supported, see: `oscar/resources/vars_iamc-ar6_map.yaml`\n"


    with open(type_dir / "README_IAMC_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  [DOC] Created {f_type}/README_IAMC_GUIDE.md")

def build_ceds_templates():
    from oscar._io.paths import PACKAGE_ROOT
    base_dir = get_customized_library_dir() / "templates"
    f_type = "atmospheric"
    type_dir = base_dir / f_type
    type_dir.mkdir(parents=True, exist_ok=True)

    reg_path = PACKAGE_ROOT / "oscar" / "_resources" / "vars_ceds_map.yaml"
    if not reg_path.exists(): return
    with open(reg_path, "r", encoding="utf-8") as f: ceds_mapping = yaml.safe_load(f)

    print(f"--- Generating CEDS-Standard Template for {f_type.upper()} ---")

    years = [2025, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]
    columns = ["Model", "Scenario", "Region", "Variable", "Unit"] + years
    
    template_data = []
    flat_map = {**ceds_mapping.get('emissions', {}), **ceds_mapping.get('halogens', {})}
    
    # Select sample keys for the template
    sample_keys = list(ceds_mapping.get('emissions', {}).keys())[:8] + \
                  list(ceds_mapping.get('halogens', {}).keys())[:4]

    for var_string in sample_keys:
        data = flat_map[var_string]
        template_data.append({
            "Model": "CEDS_Source", "Scenario": "Custom_Scenario", "Region": "World",
            "Variable": var_string, "Unit": data[3] if len(data) > 3 else "units",
            2025: 100, 2100: 10
        })

    # Save CSV
    df = pd.DataFrame(template_data, columns=columns).fillna("")
    fname = "forcing_atmospheric_ceds_template.csv"
    df.to_csv(type_dir / fname, index=False)
    print(f"  [CSV] Created CEDS template: {f_type}/{fname}")

    # 5. Generate Standardized README
    md = "# OSCAR User Guide: ATMOSPHERIC (CEDS Format)\n\n"
    md += "## 📋 OVERVIEW\n"
    md += "This template follows the **CEDS** format.\n"
    md += "In your `settings_my-experiment.yaml`, ensure you set:\n"
    md += "```yaml\natmospheric:\n  file: 'your_file.csv'\n  format: 'ceds'\n```\n\n"
    
    md += "## 🏗 Structure\n"
    md += "- **Wide Format**: Years are represented as columns.\n"
    md += "- **Variables**: Must match CEDS registry strings (OSCAR uses total emissions, names include `|Total`).\n"
    md += "- **Units**: Note CEDS uses **kt** for N2O and Halogens, but **Mt** for others.\n\n"

    md += "## 🔬 Registry Mapping Used\n"
    md += "For full list of variables and units supported, see: `oscar/resources/vars_ceds_map.yaml`\n"

    with open(type_dir / "README_CEDS_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  [DOC] Created {f_type}/README_CEDS_GUIDE.md")

# Update main execution block
if __name__ == "__main__":
    build_iamc_templates()
    build_ceds_templates()