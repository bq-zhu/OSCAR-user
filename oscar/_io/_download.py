"""
OSCAR Data Downloader - Configured Mode specialization
Handles the retrieval of official pre-compiled CMIP6/7 regional libraries.
"""
import zipfile
import requests
from .paths import get_configured_library_dir
from .._utils.load_config import load_config

def ensure_configured_library(hist_type, region):
    """
    Checks for the existence of a specific regional library.
    If missing, downloads and extracts the official bundle from Zenodo.
    """
    # 1. Resolve local path: data/configured/CMIP6/RCP_5reg/
    target_dir = get_configured_library_dir() / hist_type / region
    
    # Representative file check to see if library is already there
    if (target_dir / "forcing_hist.nc").exists():
        return target_dir

    # 2. If not found, prepare for download
    full_cfg = load_config()
    paths = full_cfg['paths']
    record_id = full_cfg['metadata']['configured']['zenodo_id']
    zip_filename = f"OSCAR_configured_{hist_type}_{region}.zip"
    url = f"{paths['zenodo_base_url']}{record_id}/files/{zip_filename}/content"
    
    # Path to temporarily store the zip during download
    # (Put it one level up in the CMIP6 folder)
    zip_temp_path = target_dir.parent / zip_filename
    zip_temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[OSCAR] Official library for '{region}' ({hist_type}) not found locally.")
    print(f"[OSCAR] Please wait, fetching remote bundle from Zenodo...")
    
    try:
        # 3. Stream the download
        response = requests.get(url, stream=True)
        response.raise_for_status() # Ensure the Zenodo link is valid
        
        with open(zip_temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 4. Extraction
        # Because the Bundler script included the region folder in the zip,
        # we extract it into the CMIP6 directory.
        print(f"[OSCAR] Extracting: {zip_filename}")
        with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir.parent)

        print(f"[OSCAR] Setup complete. Library ready at {target_dir}")

    except Exception as e:
        raise RuntimeError(
            f"Failed to download scientific library for {region}.\n"
            f"Please check your internet connection or URL: {url}\n"
            f"Error: {e}"
        )
    finally:
        # Cleanup temporary zip
        if zip_temp_path.exists():
            zip_temp_path.unlink()

    return target_dir