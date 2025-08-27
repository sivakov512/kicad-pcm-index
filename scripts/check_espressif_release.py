#!/usr/bin/env python3
"""Check for new Espressif KiCad library releases"""
import json
import logging
import os
import sys
import urllib.request
import urllib.error
import tempfile
import zipfile
from pathlib import Path

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger('espressif-release-checker')

# Constants
ESPRESSIF_REPO = "espressif/kicad-libraries"
PLUGIN_IDENTIFIER = "com.github.espressif.kicad-libraries"
GITHUB_API_URL = f"https://api.github.com/repos/{ESPRESSIF_REPO}/releases/latest"

def get_current_version() -> str:
    """Get the current version of Espressif library from packages.json"""
    packages_file = Path("packages.json")

    if not packages_file.exists():
        log.error("packages.json not found")
        return ""

    try:
        with open(packages_file, "r") as f:
            packages_data = json.load(f)

        for package in packages_data.get("packages", []):
            if package["identifier"] == PLUGIN_IDENTIFIER:
                versions = package.get("versions", [])
                if versions:
                    # Return the latest version (assuming they are sorted)
                    return versions[-1]["version"]
                break

        return ""  # Plugin not found or no versions
    except Exception as e:
        log.error(f"Error reading packages.json: {e}")
        return ""


def get_latest_release() -> dict:
    """Get the latest release info from GitHub API"""
    try:
        with urllib.request.urlopen(GITHUB_API_URL, timeout=30) as response:
            if response.getcode() != 200:
                log.error(f"HTTP error: {response.getcode()}")
                return {}
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except Exception as e:
        log.error(f"Error fetching release info: {e}")
        return {}


def extract_metadata_from_archive(download_url: str) -> dict:
    """Download archive and extract metadata.json"""
    log.info(f"Downloading and extracting metadata from {download_url}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / "archive.zip"

        try:
            urllib.request.urlretrieve(download_url, archive_path)
        except Exception as e:
            log.error(f"Download error: {e}")
            return {}

        if not archive_path.exists() or archive_path.stat().st_size == 0:
            log.error("Downloaded file is empty or does not exist")
            return {}

        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Look for metadata.json in the archive
                metadata_files = [f for f in zip_ref.namelist() if f.endswith('metadata.json')]
                if not metadata_files:
                    log.error("No metadata.json found in archive")
                    return {}

                # Use the first metadata.json found
                metadata_file = metadata_files[0]
                with zip_ref.open(metadata_file) as f:
                    metadata = json.loads(f.read().decode('utf-8'))
                    return metadata
        except Exception as e:
            log.error(f"Error extracting metadata: {e}")
            return {}

    return {}


def set_github_output(name: str, value: str):
    """Set GitHub Actions output variable"""
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        # Create directory if it doesn't exist and dirname is not empty
        dirname = os.path.dirname(github_output)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(github_output, 'a') as f:
            f.write(f"{name}={value}\n")


def main():
    log.info("Checking for new Espressif KiCad library releases...")

    current_version = get_current_version()
    log.info(f"Current version: {current_version if current_version else 'Not found'}")

    release_info = get_latest_release()
    if not release_info:
        log.error("Failed to get release information")
        sys.exit(1)

    latest_version = release_info.get("tag_name", "").lstrip("v")
    if not latest_version:
        log.error("No tag name found in release info")
        sys.exit(1)

    log.info(f"Latest version: {latest_version}")

    # Check if we have a new version
    if current_version and latest_version == current_version:
        log.info("No new version available")
        set_github_output("new_release", "false")
        return

    # Find download URL for the ZIP file
    download_url = ""
    for asset in release_info.get("assets", []):
        if asset["name"].endswith(".zip"):
            download_url = asset["browser_download_url"]
            break

    if not download_url:
        log.error("No ZIP file found in release assets")
        sys.exit(1)

    # Extract metadata from the archive
    metadata = extract_metadata_from_archive(download_url)
    if not metadata:
        log.error("Failed to extract metadata from archive")
        sys.exit(1)

    # Get KiCad version from metadata
    kicad_version = metadata.get("kicad_version", "8.0.0")
    # Convert to major.minor format if needed (e.g., "8.0.0" -> "8.0")
    if kicad_version.count('.') > 1:
        kicad_version = '.'.join(kicad_version.split('.')[:2])

    log.info(f"New release found: {latest_version}")
    log.info(f"Download URL: {download_url}")
    log.info(f"KiCad version from metadata: {kicad_version}")

    # Set GitHub Actions outputs
    set_github_output("new_release", "true")
    set_github_output("identifier", PLUGIN_IDENTIFIER)
    set_github_output("version", latest_version)
    set_github_output("status", "stable")
    set_github_output("kicad_version", kicad_version)
    set_github_output("download_url", download_url)


if __name__ == "__main__":
    main()
