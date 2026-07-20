"""Shared ingest helpers: paths, downloads, logging."""
from __future__ import annotations

import sys
import time
import zipfile
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings()

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PARQUET = ROOT / "data" / "parquet"
WAREHOUSE_DB = ROOT / "data" / "warehouse.duckdb"

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}


def log(msg: str) -> None:
    print(f"[ingest] {msg}", flush=True)


def download_file(url: str, dest: Path, *, retries: int = 3, timeout: int = 600,
                  ok_404: bool = False) -> bool:
    """Stream url to dest. Returns False on 404 when ok_404 (missing vintage)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        log(f"cached: {dest.name}")
        return True
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, headers=UA, stream=True, verify=False,
                              timeout=timeout) as r:
                if r.status_code == 404 and ok_404:
                    log(f"404 (accepted): {url}")
                    return False
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
                tmp.rename(dest)
                log(f"downloaded: {dest.name} ({dest.stat().st_size >> 20} MB)")
                return True
        except Exception as e:  # noqa: BLE001
            log(f"attempt {attempt}/{retries} failed for {url}: {e}")
            if attempt == retries:
                raise
            time.sleep(5 * attempt)
    return False


def unzip_all(zip_path: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        z.extractall(out_dir)
    return [out_dir / n for n in names]


def main_guard(fn):
    if __name__ != "__main__":
        return
    sys.exit(fn())
