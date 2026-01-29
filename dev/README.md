# 🛠 OSCAR-user Developer Workshop

This directory contains the internal infrastructure for data generation, model calibration, and release management.

⚠️ **CONFIDENTIALITY NOTICE**
This folder contains internal research notes and server paths. 
**NEVER push this directory to the public `oscar-user` repository.**

---

## 🏗 Data Pipeline Architecture
To handle different scientific needs, the data generation is split by model mode:

### 0. Standard Mode (Bootstrap)
- **Purpose:** To allow quick verification of the model.
- **Location:** `oscar/_resources/bootstrap/`
- **Manual:** See `dev/docs/standard_mode.md`.

### 1. Configured Mode (Official Library)
- **Purpose:** Builds the pre-calculated 30GB regional library (CMIP6/7).
- **Location:** `dev/devtools/configured/`
- **Manual:** See `dev/docs/configured_mode.md` for the 4-step process.

### 2. Customized Mode (User Assets)
- **Purpose:** Prepares templates and background forcing for independent users.
- **Location:** `dev/devtools/customized/`
- **Manual:** See `dev/docs/customized_mode.md`.

---

## ⚙️ Development Standards

### search Path
To run any script in this folder, you must execute from the **Project Root** and set the `PYTHONPATH`:
```powershell
# Windows PowerShell example
$env:PYTHONPATH="."
python dev/devtools/configured/01_make_params.py
```

### Shared Logic
Reusable code (like YAML loaders or specific OSCAR aggregators) used by multiple devtools should be placed in `dev/devtools/_common/`.

### Branching Strategy
- `main` : Team collaboration (Private).
- `release` : Public showroom (Cleaned/Scrubbed).
- `feat/*` : New model features or data versions.

---

## 📅 Roadmap & TODOs
- [ ] Move CSV-to-NC handler to `oscar/_io/`.
- [ ] Complete CMIP7 historical aggregation (Step 02).
- [ ] Automate checksum verification for Zenodo bundles.

---
*Maintained by: Biqing Zhu and the OSCAR Development Team*