from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import requests
from polykit.env import PolyEnv
from polykit.log import PolyLog

from starfield_saver.version import CURRENT_VERSION

env = PolyEnv()
env.add_var("GITHUB_TOKEN")
token = env.get("GITHUB_TOKEN")

VERSION_URL = f"https://raw.githubusercontent.com/dannystewart/starfield-saver/refs/heads/main/version.json?token={token}"

OLD_FILENAME = "starfield_saver_old.exe"
NEW_FILENAME = "starfield_saver_new.exe"


class VersionUpdater:
    """Check for updates and prompt the user to update if a new version is available."""

    def __init__(self):
        self.logger = PolyLog.get_logger("version_updater")

    def check_for_updates(self) -> None:
        """Check for updates and prompt the user to update if a new version is available."""
        try:
            response = requests.get(VERSION_URL)
            data = json.loads(response.text)
            latest_version = data["version"]
            if latest_version > CURRENT_VERSION:
                self.logger.info("New version %s available!", latest_version)
                download_url = data["download_url"]

                if input("Do you want to update? (y/n): ").lower() == "y":
                    self.update_app(download_url)
            else:
                self.logger.info(
                    "Starting Starfield Saver v%s. You are on the latest version.", CURRENT_VERSION
                )
        except Exception as e:
            self.logger.warning("Failed to check for updates: %s", str(e))

    def update_app(self, url: str) -> None:
        """Download the new version and replace the current executable."""
        try:
            response = requests.get(url)
            with Path(NEW_FILENAME).open("wb") as f:
                f.write(response.content)

            # Create a batch file to handle the update
            with Path("update.bat").open("w", encoding="utf-8") as batch_file:
                batch_file.write(f"""
@echo off
timeout /t 1 /nobreak >nul
del "{sys.executable}"
move "{NEW_FILENAME}" "{sys.executable}"
start "" "{sys.executable}"
del "%~f0"
                """)

            self.logger.info("Update successful! Restarting application...")
            subprocess.Popen("update.bat", shell=True)
            sys.exit()
        except Exception as e:
            self.logger.error("Update failed: %s", str(e))

    def cleanup_old_version(self) -> None:
        """Remove the old version of the executable if it exists."""
        if Path(OLD_FILENAME).exists():
            try:
                Path(OLD_FILENAME).unlink()
                self.logger.info("Removed old version: %s", OLD_FILENAME)
            except Exception as e:
                self.logger.error("Failed to remove old version: %s", str(e))
