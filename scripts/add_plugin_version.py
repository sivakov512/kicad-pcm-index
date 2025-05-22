#!/usr/bin/env python3
"""KiCad PCM plugin version updater"""
import argparse
import json
import logging
import sys
import tempfile
import time
import typing
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger('pcm-updater')

def fatal(msg: str, exit_code: int = 1) -> typing.NoReturn:
    log.error(msg)
    sys.exit(exit_code)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add or update a plugin version in KiCad PCM index"
    )
    parser.add_argument("identifier", help="Plugin identifier (e.g. com.github.username.plugin)")
    parser.add_argument("version", help="Version of the plugin (e.g. 1.0.0)")
    parser.add_argument("status", choices=["stable", "testing", "development", "deprecated"],
                      help="Status of the version (stable, testing, development, deprecated)")
    parser.add_argument("kicad_version", help="Minimum KiCad version required (e.g. 8.0)")
    parser.add_argument("download_url", help="URL to download the plugin archive")
    return parser.parse_args()


def download_and_calculate_metrics(url: str) -> typing.Dict[str, typing.Any]:
    """Calculate download_size, download_sha256, and install_size metrics for plugin"""
    log.info(f"Downloading plugin from {url}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / "plugin.zip"
        
        try:
            urllib.request.urlretrieve(url, archive_path)
        except Exception as e:
            fatal(f"Download error: {e}")
            
        if not archive_path.exists() or archive_path.stat().st_size == 0:
            fatal("Downloaded file is empty or does not exist")
        
        download_size = archive_path.stat().st_size
        
        file_hash = sha256()
        with open(archive_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        download_sha256 = file_hash.hexdigest()
        
        extract_dir = temp_path / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as e:
            fatal(f"Error extracting ZIP archive: {e}")
        
        install_size = get_directory_size(extract_dir)
        log.info(f"Plugin metrics - Size: {download_size} bytes, SHA256: {download_sha256[:8]}...")
        
        return {
            "download_size": download_size,
            "download_sha256": download_sha256,
            "install_size": install_size
        }


def get_directory_size(directory: Path) -> int:
    return sum(f.stat().st_size for f in directory.glob('**/*') if f.is_file())


def update_packages_json(args, metrics: typing.Dict[str, typing.Any]) -> None:
    """Find plugin by identifier and add/update version information in packages.json"""
    log.info("Updating packages.json")
    packages_file = Path("packages.json")
    
    if not packages_file.exists():
        fatal("packages.json not found")
    
    try:
        with open(packages_file, "r") as f:
            packages_data = json.load(f)
        
        if "packages" not in packages_data:
            fatal("Invalid packages.json structure - 'packages' key not found")
        
        plugin_found = False
        for package in packages_data["packages"]:
            if package["identifier"] == args.identifier:
                plugin_found = True
                
                new_version = {
                    "version": args.version,
                    "status": args.status,
                    "kicad_version": args.kicad_version,
                    "download_url": args.download_url,
                    "download_sha256": metrics["download_sha256"],
                    "download_size": metrics["download_size"],
                    "install_size": metrics["install_size"]
                }
                
                for i, version in enumerate(package.get("versions", [])):
                    if version["version"] == args.version:
                        package["versions"][i] = new_version
                        log.info(f"Updated existing version {args.version}")
                        break
                else:
                    if "versions" not in package:
                        package["versions"] = []
                    package["versions"].append(new_version)
                    log.info(f"Added new version {args.version}")
                break
        
        if not plugin_found:
            fatal(f"Plugin '{args.identifier}' not found")
        
        with open(packages_file, "w") as f:
            json.dump(packages_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        fatal(f"Error updating packages.json: {e}")


def update_repository_json() -> None:
    """Update UTC time and Unix timestamp for packages and resources in repository.json"""
    log.info("Updating repository.json timestamps")
    repo_file = Path("repository.json")
    
    if not repo_file.exists():
        fatal("repository.json not found")
    
    try:
        timestamp = int(time.time())
        time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        with open(repo_file, "r") as f:
            repo_data = json.load(f)
        
        if "packages" not in repo_data or "resources" not in repo_data:
            fatal("Invalid repository.json structure - required sections missing")
            
        for section in ["packages", "resources"]:
            repo_data[section]["update_time_utc"] = time_utc
            repo_data[section]["update_timestamp"] = timestamp
        
        with open(repo_file, "w") as f:
            json.dump(repo_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        fatal(f"Error updating repository.json: {e}")


def main() -> None:
    try:
        args = parse_arguments()
        metrics = download_and_calculate_metrics(args.download_url)
        update_packages_json(args, metrics)
        update_repository_json()
        log.info(f"Successfully updated plugin {args.identifier} to version {args.version}")
    except KeyboardInterrupt:
        log.warning("Operation cancelled")
        sys.exit(1)
    except Exception as e:
        fatal(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()