"""
Runs the whole pipeline in order: ingest -> load -> dbt build.
Stops at the first failure and writes everything to logs/pipeline.log.

Usage:
    python run_pipeline.py
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
LOG_FILE = PROJECT_DIR / "logs" / "pipeline.log"

# dbt is installed next to python.exe inside .venv\Scripts
DBT = str(Path(sys.executable).with_name("dbt.exe" if os.name == "nt" else "dbt"))


def setup_logging() -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"),
                  logging.StreamHandler()],
    )


def run_step(name: str, command: list[str]) -> None:
    """Run one step as a separate program and stop the pipeline if it fails."""
    logging.info("Starting %s", name)
    result = subprocess.run(command, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        logging.info("  %s", line)
    if result.returncode != 0:
        logging.error("%s failed:\n%s", name, result.stderr)
        raise SystemExit(1)
    logging.info("Finished %s", name)


def main() -> None:
    os.chdir(PROJECT_DIR)          # so relative paths work from any start folder
    setup_logging()
    logging.info("===== Pipeline run started =====")
    run_step("ingest", [sys.executable, "ingest.py"])
    run_step("load", [sys.executable, "load.py"])
    run_step("dbt build", [DBT, "build", "--project-dir", "dbt", "--profiles-dir", "dbt"])
    run_step("export", [sys.executable, "export.py"])
    logging.info("===== Pipeline run finished successfully =====")


if __name__ == "__main__":
    main()