"""Run every ingest step. Each source is isolated: a failure is recorded and
the run continues (blocker protocol), with a nonzero exit at the end if
anything failed so the Makefile surfaces it.
"""
from __future__ import annotations

import time
import traceback

from . import bts_db1b, bts_form41, bts_lookups, bts_t100, census_bea_eia, \
    ourairports, statcan
from .common import log


def main() -> int:
    t0 = time.time()
    failures: list[str] = []
    for name, mod in [("ourairports", ourairports), ("lookups", bts_lookups),
                      ("statcan", statcan), ("census/bea/eia", census_bea_eia),
                      ("t100", bts_t100), ("form41", bts_form41),
                      ("db1b", bts_db1b)]:
        log(f"=== {name} ===")
        try:
            mod.run()
        except Exception:  # noqa: BLE001
            failures.append(name)
            log(f"FAILED: {name}")
            traceback.print_exc()
    log(f"ingest finished in {(time.time()-t0)/60:.1f} min; "
        f"failures: {failures or 'none'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
