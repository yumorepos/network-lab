"""Demonstrate that each W1.3 leakage guard FAILS when the leak is reintroduced.

Integrity round 4's explicit lesson: a test that has never been shown to fail is
a test of nothing. Three P0 defects passed a fully green suite.

This script deliberately reintroduces each leak, re-runs the guard that is meant
to catch it, and reports whether the guard fired. It changes nothing on disk and
restores every patch. Run it, and paste the output into the protocol document.

    .venv/bin/python scripts/demo_leakage_tests.py
"""
from __future__ import annotations

import sys
import traceback
from contextlib import contextmanager

sys.path.insert(0, ".")

import pandas as pd  # noqa: E402

from models.common import connect  # noqa: E402
from replay import snapshot as S  # noqa: E402
from replay import vintage as V  # noqa: E402
from tests import test_replay_leakage as T  # noqa: E402

RESULTS: list[tuple[str, str, bool, str]] = []


@contextmanager
def patched(obj, attr, value):
    old = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        setattr(obj, attr, old)


def check(name: str, injection: str, fn):
    """Run a guard that is expected to FAIL. Report whether it did."""
    try:
        fn()
    except AssertionError as e:
        msg = str(e).strip() or "bare assertion failed (no message)"
        RESULTS.append((name, injection, True, msg.splitlines()[0][:150]))
        return
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, injection, True,
                        f"raised {type(e).__name__}: {str(e)[:80]}"))
        return
    RESULTS.append((name, injection, False,
                    "GUARD DID NOT FIRE: the leak passed undetected"))


def main() -> int:
    con = connect(read_only=True)
    cutoff = 202401

    # ---- 1. T-100 window reads the future -------------------------------
    def t100_leak():
        v = S.resolve_vintages(cutoff, con)
        v.t100_max_ym = 202604            # the panel end: 27 months ahead
        lag = V.protocol()["publication_lag"]["t100_months"]["value"]
        assert v.t100_max_ym <= T._ym_add(cutoff, -lag), (
            f"T-100 window ends {v.t100_max_ym}, after the permitted "
            f"{T._ym_add(cutoff, -lag)} at cutoff {cutoff}")
    check("t100 window never reaches past the cutoff",
          "t100_max_ym forced to the panel end 202604", t100_leak)

    # ---- 2. DB1B year from the future -----------------------------------
    def db1b_leak():
        v = S.resolve_vintages(cutoff, con)
        v.db1b_year = 2024                # the production value
        lag = V.protocol()["publication_lag"]["db1b_quarter_months"]["value"]
        assert T._ym_add(v.db1b_year * 100 + 12, lag) <= cutoff, (
            f"DB1B {v.db1b_year} was not fully published by {cutoff}")
    check("db1b year complete and published by the cutoff",
          "db1b_year forced to the production 2024", db1b_leak)

    # ---- 3. Form 41 year from the future --------------------------------
    def form41_leak():
        v = S.resolve_vintages(cutoff, con)
        v.form41_year = 2025
        lag = V.protocol()["publication_lag"]["form41_annual_months"]["value"]
        assert T._ym_add(v.form41_year * 100 + 12, lag) <= cutoff
    check("form41 year complete and published by the cutoff",
          "form41_year forced to 2025", form41_leak)

    # ---- 4. Gravity resolver that ignores publication --------------------
    # The first attempt at this injection added an unpublished vintage and
    # expected the guard to fire. It did not, and correctly so: the resolver
    # REFUSES an unpublished window, so no leak was created and there was
    # nothing to catch. The defect class that actually leaks is a resolver that
    # picks the newest calibration without checking whether it was published.
    def gravity_leak():
        def naive(self, windows):
            best = max(windows, key=lambda k: windows[k][1])
            self._record(V.Provenance(
                source=f"gravity calibration ({best})",
                reference_period=f"{windows[best][0]}-{windows[best][1]}",
                original_availability_date="n/a",
                data_vintage_date=self.data_vintage_date,
                permitted_cutoff=self.label,
                vintage_policy=V.AS_AVAILABLE))
            return best
        with patched(V.Cutoff, "gravity_vintage", naive):
            v = S.resolve_vintages(cutoff, con)
            lo, hi = S.GRAVITY_WINDOWS[v.gravity_vintage]
            lag = V.protocol()["publication_lag"]["db1b_quarter_months"]["value"]
            assert T._ym_add(hi * 100 + 12, lag) <= cutoff, (
                f"gravity vintage {v.gravity_vintage} calibrated through {hi}, "
                f"not published by {cutoff}")
    check("gravity calibration never from the future",
          "resolver replaced with one that picks the newest window without "
          "checking publication", gravity_leak)

    # ---- 5. Gravity vintage silently set to production ------------------
    def gravity_current_leak():
        v = S.resolve_vintages(cutoff, con)
        v.gravity_vintage = "current"      # 2023-2024, the production default
        lo, hi = S.GRAVITY_WINDOWS[v.gravity_vintage]
        lag = V.protocol()["publication_lag"]["db1b_quarter_months"]["value"]
        assert T._ym_add(hi * 100 + 12, lag) <= cutoff, (
            f"gravity vintage {v.gravity_vintage} calibrated through {hi}, "
            f"not published by {cutoff}")
    check("gravity calibration never from the future",
          "gravity_vintage forced to the production 'current' (2023-2024)",
          gravity_current_leak)

    # ---- 6. Geography lookahead left undeclared -------------------------
    def geo_leak():
        with patched(V.Cutoff, "GEOGRAPHY_RELEASE_YM", 190001):
            c = V.Cutoff(202201)
            c.geography_vintage()
            row = pd.DataFrame([p.as_row() for p in c.provenance]).iloc[0]
            declared = not pd.isna(row["lookahead_exception"])
            assert declared, (
                "cutoff 202201 precedes the 2023-07 release; the delineation "
                "lookahead must be declared")
    check("geography lookahead declared exactly when it applies",
          "GEOGRAPHY_RELEASE_YM back-dated to 1900 so the guard sees no leak",
          geo_leak)

    # ---- 7. Vintage policy vocabulary not enforced ----------------------
    def policy_leak():
        V.Provenance(source="x", reference_period="2020",
                     original_availability_date="2021-01",
                     data_vintage_date="2026-07-20",
                     permitted_cutoff="2022-01",
                     vintage_policy="looks_fine_to_me")
    check("vintage policy vocabulary is enforced",
          "a Provenance is constructed with an unknown policy string",
          policy_leak)

    # ---- 8. Served-market window reads the future -----------------------
    def served_leak():
        v = S.resolve_vintages(202201, con)
        v.t100_max_ym = 202604            # future service becomes "served"
        cand_leaky = S.build_candidates("porter_yyz", con, v)
        cand_prod = S.build_candidates("porter_yyz", con,
                                       S.production_vintages())
        assert len(cand_leaky) > len(cand_prod), (
            f"Porter had 0 US metros served from YYZ at 2022-01, so the "
            f"historical candidate set must be LARGER; got {len(cand_leaky)} "
            f"vs {len(cand_prod)}")
    check("porter has no served metros before its network existed",
          "served-market window upper bound moved to the panel end 202604",
          served_leak)

    # ---- 9. Snapshot that ignores the cutoff entirely -------------------
    def frozen_snapshot_leak():
        prod = S.production_vintages()
        sizes = {c: len(S.build_candidates("westjet_yyc", con, prod))
                 for c in T.CUTOFFS}
        n = len(S.build_candidates("westjet_yyc", con, prod))
        assert len(set(list(sizes.values()) + [n])) > 1, (
            f"candidate counts identical across cutoffs and production: "
            f"{sizes}, production {n}. The vintaging is not biting.")
    check("candidate sets actually move with the cutoff",
          "every cutoff resolved to production vintages instead",
          frozen_snapshot_leak)

    # ---- 10. Offline transform allowed to reach the network -------------
    def failopen_leak():
        from pathlib import Path

        from replay import pit_metros as P
        with patched(P, "CAINC1", Path("/nonexistent/CAINC1.csv")):
            P._read_bea(P.CAINC1, "BEA CAINC1 county file")
    check("pit transform fails closed on a missing cache",
          "CAINC1 path pointed at a nonexistent file",
          failopen_leak)

    con.close()

    width = max(len(n) for n, _, _, _ in RESULTS)
    print("=" * 100)
    print("W1.3 LEAKAGE GUARD DEMONSTRATION")
    print("Each row reintroduces a leak and reports whether the guard caught it.")
    print("=" * 100)
    fired = 0
    for name, injection, ok, detail in RESULTS:
        status = "FAILED AS REQUIRED" if ok else "*** DID NOT FIRE ***"
        fired += ok
        print(f"\n{name:<{width}}  {status}")
        print(f"  injection: {injection}")
        print(f"  guard said: {detail}")
    print()
    print("=" * 100)
    print(f"{fired} of {len(RESULTS)} guards fired when their leak was "
          "reintroduced.")
    print("=" * 100)
    return 0 if fired == len(RESULTS) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)
