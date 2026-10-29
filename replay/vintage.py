"""Vintage policy: what a decision at time t was allowed to see.

W1.3. Every historical observation a snapshot reads carries a provenance record
answering six questions, and the snapshot fails closed if any of them is
unanswerable:

  reference_period            the period the value describes
  original_availability_date  when the publisher first released that period
  data_vintage_date           the vintage of the file we actually hold
  permitted_cutoff            the decision date; nothing later may be read
  vintage_policy              one of the three policies below
  lookahead_exception         null, or a named and explained residual leak

The three vintage policies are distinct claims and must not be blurred:

  as_available_by_cutoff        the value we read is the value a planner could
                                have read at the cutoff, from a source that does
                                not revise (T-100 counts, EIA spot prices)
  latest_revised_historical_value
                                the reference period is correct for the cutoff,
                                but the value is a later revision of it. BEA and
                                StatCan revise; we hold one file. This is a
                                genuine residual lookahead and is recorded as
                                one, not hidden.
  stale_historical_anchor       the source stopped publishing before the cutoff,
                                so the latest available reference period is older
                                than the lag alone would imply. The StatCan
                                transborder table is the case that matters.

The opening claim was false when written: the corridor-growth year and the EIA
fuel `as_of` were resolved inside `replay/snapshot.py` and recorded nowhere,
which is finding P1-1 of the Milestone A independent review. Both are resolved
and recorded here now, and the T-100 seats year with them.

Nothing in this module reads the network, and nothing writes to the warehouse.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import yaml

from ingest.common import ROOT

PROTOCOL_PATH = ROOT / "config" / "replay_protocol.yaml"

AS_AVAILABLE = "as_available_by_cutoff"
LATEST_REVISED = "latest_revised_historical_value"
STALE_ANCHOR = "stale_historical_anchor"
POLICIES = (AS_AVAILABLE, LATEST_REVISED, STALE_ANCHOR)


@lru_cache(maxsize=1)
def protocol() -> dict:
    if not PROTOCOL_PATH.exists():
        raise FileNotFoundError(
            f"replay protocol config missing: {PROTOCOL_PATH}. The replay "
            "fails closed rather than inventing publication lags.")
    return yaml.safe_load(PROTOCOL_PATH.read_text())


def _lag(name: str) -> int:
    return int(protocol()["publication_lag"][name]["value"])


def excluded_data_years() -> set[int]:
    return set(protocol()["exclusions"]["excluded_data_years"]["value"])


def excluded_decision_vintages() -> set[int]:
    return set(protocol()["exclusions"]["excluded_decision_vintages"]["value"])


def structural_break_years() -> set[int]:
    """Years the project has declared a structural break.

    Distinct from `excluded_decision_vintages` in use, not in value. That entry
    governs which years may be a DECISION or a LAUNCH COHORT and leaves 2021
    admissible as input data, because a planner at 2023-01 did hold 2021 data.
    This one governs which years may be an ENDPOINT OF A GROWTH RATIO, where
    the same year is not admissible: a two-point trend anchored on a break year
    and applied as a permanent level shift is a specification error rather than
    a point-in-time fact. See `config/replay_protocol.yaml`.
    """
    return set(protocol()["exclusions"]["structural_break_years"]["value"])


@dataclass(frozen=True)
class Provenance:
    """One source, resolved against one cutoff. Immutable by design."""
    source: str
    reference_period: str
    original_availability_date: str
    data_vintage_date: str
    permitted_cutoff: str
    vintage_policy: str
    lookahead_exception: str | None = None

    def __post_init__(self):
        if self.vintage_policy not in POLICIES:
            raise ValueError(
                f"unknown vintage_policy {self.vintage_policy!r}; "
                f"must be one of {POLICIES}")

    def as_row(self) -> dict:
        return {
            "source": self.source,
            "reference_period": self.reference_period,
            "original_availability_date": self.original_availability_date,
            "data_vintage_date": self.data_vintage_date,
            "permitted_cutoff": self.permitted_cutoff,
            "vintage_policy": self.vintage_policy,
            "lookahead_exception": self.lookahead_exception,
        }


def _add_months(ym: int, n: int) -> int:
    """ym is yyyymm."""
    y, m = divmod(ym, 100)
    t = y * 12 + (m - 1) + n
    return (t // 12) * 100 + (t % 12) + 1


@dataclass
class Cutoff:
    """A decision date, and every vintage question answered against it.

    `ym` is yyyymm. `data_vintage_date` is the date the frozen cache was
    downloaded, which is what makes the revision lookahead explicit rather than
    implicit.
    """
    ym: int
    data_vintage_date: str = "2026-07-20"
    provenance: list[Provenance] = field(default_factory=list)

    # ---------------------------------------------------------------- helpers
    @property
    def label(self) -> str:
        y, m = divmod(self.ym, 100)
        return f"{y}-{m:02d}"

    @property
    def year(self) -> int:
        return self.ym // 100

    def _record(self, p: Provenance) -> Provenance:
        self.provenance.append(p)
        return p

    def _latest_complete_year(self, lag_months: int, cached: set[int],
                              exclude: set[int]) -> int:
        """Latest calendar year whose Q4 plus lag precedes the cutoff, that is
        cached and not excluded. Raises rather than guessing."""
        y = self.year
        while y >= min(cached) - 1:
            if (y not in exclude and y in cached
                    and _add_months(y * 100 + 12, lag_months) <= self.ym):
                return y
            y -= 1
        raise LookupError(
            f"no admissible calendar year at cutoff {self.label}: cached "
            f"{sorted(cached)}, excluded {sorted(exclude)}, lag {lag_months}mo. "
            "The replay fails closed rather than reaching for a later vintage.")

    # -------------------------------------------------------------- resolvers
    def t100_max_ym(self) -> int:
        """Latest T-100 month a decision at the cutoff could have seen."""
        m = _add_months(self.ym, -_lag("t100_months"))
        self._record(Provenance(
            source="BTS T-100 Segment",
            reference_period=f"months through {m//100}-{m%100:02d}",
            original_availability_date=self.label,
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=AS_AVAILABLE,
            lookahead_exception=None))
        return m

    def _t100_complete_year(self, cached: set[int], max_ym: int,
                            exclude: set[int] | None = None) -> int:
        """Latest complete T-100 calendar year inside the permitted window.

        Shared by the two callers below rather than duplicated, because two
        independent computations of the same selection are precisely how the
        corridor-growth year came to disagree with nothing and be recorded
        nowhere. One selection, one rule, two declared uses.

        `exclude` is the D1 repair. Every other vintage resolver in this file
        goes through `_latest_complete_year`, which has taken an exclusion set
        since it was written; this helper was the one selection that took none,
        and the corridor-growth year is the one use where that matters. The two
        callers below pass different sets on purpose: seats are a level input
        and admit a break year, a growth ratio is not and does not.
        """
        exclude = exclude or set()
        ok = [y for y in cached if y * 100 + 12 <= max_ym and y not in exclude]
        if not ok:
            raise LookupError(
                f"no complete T-100 calendar year within {_fmt(max_ym)} at "
                f"cutoff {self.label}: cached {sorted(cached)}, excluded "
                f"{sorted(exclude)}. The replay fails closed rather than "
                "reaching for a later year.")
        return max(ok)

    def t100_seats_year(self, cached: set[int], max_ym: int) -> int:
        """Airport seat totals. Feeds the candidate seat floor and the
        satellite rule.

        **Deliberately keeps structural-break years.** A seat total is a level
        the decision genuinely read, and it is the level that was there: 2021
        airports really did handle 2021 seats. Excluding break years here would
        move the candidate set at 2023-01, which is a different change from D1
        and is not made. See `structural_break_years` for why the growth ratio
        is treated differently.
        """
        y = self._t100_complete_year(cached, max_ym)
        self._record(Provenance(
            source="BTS T-100 Segment (annual seats)",
            reference_period=str(y),
            original_availability_date=_fmt(
                _add_months(y * 100 + 12, _lag("t100_months"))),
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=AS_AVAILABLE,
            lookahead_exception=None))
        return y

    def t100_corridor_growth_year(self, cached: set[int], max_ym: int) -> int:
        """Numerator year of the corridor growth ratio in `build_transfer`.

        The single largest lever on transborder demand: the ratio is applied
        to every anchored and every capped row, so taking this year from the
        panel end rather than the permitted window multiplies 2023-01 YYC
        demand by 5.73.

        **D1 repair**, `docs/change_reports/D1_corridor_growth_vintage.md`.
        A structural-break year is admissible as a level input and is not
        admissible as an endpoint of a growth ratio, so this resolver skips
        them and `t100_seats_year` does not. Before the repair the two shared
        one selection and returned the same year; they are now genuinely two
        rules with two declared uses, which is what the docstring below always
        claimed.
        """
        y = self._t100_complete_year(cached, max_ym, structural_break_years())
        self._record(Provenance(
            source="BTS T-100 Segment (corridor growth year)",
            reference_period=str(y),
            original_availability_date=_fmt(
                _add_months(y * 100 + 12, _lag("t100_months"))),
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=AS_AVAILABLE,
            lookahead_exception=None))
        return y

    def eia_fuel_as_of(self) -> str:
        """EIA jet fuel spot, trailing 365 days ending at the decision date.

        `models.economics.fuel_price_base` falls back to the panel end when it
        receives None, which at a 2022-01 cutoff reads a price 43.0% above the
        vintaged one and feeds `margin_pct` directly. Resolving the date here
        rather than at the call site means the fallback cannot be taken
        silently at a historical cutoff.
        """
        as_of = f"{self.year}-{self.ym % 100:02d}-01"
        self._record(Provenance(
            source="EIA jet fuel spot price",
            reference_period=f"365 days ending {as_of}",
            original_availability_date=as_of,
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=AS_AVAILABLE,
            lookahead_exception=(
                "fact_fuel is a weekly series and the window ends on the "
                "decision date itself, so the final weekly observation would "
                "in practice have been published a few days after it. One "
                "observation of roughly 52 in a trailing average, in the only "
                "direction the frozen model can be run offline. EIA spot "
                "prices do not revise, so nothing earlier in the window is "
                "affected.")))
        return as_of

    def db1b_year(self, cached: set[int]) -> int:
        y = self._latest_complete_year(
            _lag("db1b_quarter_months"), cached, excluded_data_years())
        self._record(Provenance(
            source="BTS DB1B Market",
            reference_period=str(y),
            original_availability_date=_fmt(
                _add_months(y * 100 + 12, _lag("db1b_quarter_months"))),
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=AS_AVAILABLE,
            lookahead_exception=None))
        return y

    def form41_year(self, cached: set[int]) -> int:
        y = self._latest_complete_year(
            _lag("form41_annual_months"), cached, excluded_data_years())
        self._record(Provenance(
            source="BTS Form 41 P-5.2 / P-1.2",
            reference_period=str(y),
            original_availability_date=_fmt(
                _add_months(y * 100 + 12, _lag("form41_annual_months"))),
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=AS_AVAILABLE,
            lookahead_exception=None))
        return y

    def bea_year(self, cached: set[int]) -> int:
        y = self._latest_complete_year(
            _lag("bea_annual_months"), cached, set())
        self._record(Provenance(
            source="BEA CAINC1 / CAGDP2",
            reference_period=str(y),
            original_availability_date=_fmt(
                _add_months(y * 100 + 12, _lag("bea_annual_months"))),
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=LATEST_REVISED,
            lookahead_exception=(
                f"BEA revises. The {y} value read here is the revision present "
                f"in the {self.data_vintage_date} file, not the estimate "
                "published at the time. Irreducible without archived vintages; "
                "W1.3 audit residual.")))
        return y

    def statcan_cma_year(self, cached: set[int]) -> int:
        lag = _lag("statcan_cma_pop_months")
        y = self._latest_complete_year(lag, cached, set())
        stale = _add_months(self.ym, -lag) // 100 > y
        self._record(Provenance(
            source="StatCan 17-10-0135 CMA population",
            reference_period=str(y),
            original_availability_date=_fmt(_add_months(y * 100 + 12, lag)),
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=STALE_ANCHOR if stale else LATEST_REVISED,
            lookahead_exception=(
                None if stale else
                f"StatCan revises population estimates; the {y} value is the "
                f"revision present in the {self.data_vintage_date} file.")))
        return y

    def statcan_transborder_year(self, cached: set[int]) -> int:
        """The anchor. Stopped publishing after reference year 2018, so every
        cutoff at or after 2020 resolves to a stale 2018 anchor."""
        lag = _lag("statcan_transborder_months")
        y = self._latest_complete_year(lag, cached, set())
        would_have = _add_months(self.ym, -lag) // 100
        stale = would_have > y
        self._record(Provenance(
            source="StatCan 23-10-0256 transborder O&D",
            reference_period=str(y),
            original_availability_date=_fmt(_add_months(y * 100 + 12, lag)),
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=STALE_ANCHOR if stale else LATEST_REVISED,
            lookahead_exception=(
                f"Table discontinued after reference year {max(cached)}. A "
                f"planner at {self.label} would have wanted {would_have} and "
                f"could only have had {y}. This is the frozen model's own "
                "anchor limitation, reproduced faithfully at vintage."
                if stale else None)))
        return y

    def gravity_vintage(self, windows: dict[str, tuple[int, int]]) -> str:
        """Latest gravity calibration vintage fully published by the cutoff.

        `windows` maps vintage name to (first_year, last_year). A vintage is
        admissible when its last year is complete and published as DB1B. This
        is a vintage SELECTION over the frozen model's existing estimators; no
        refit and no new specification.
        """
        lag = _lag("db1b_quarter_months")
        ok = {v: w for v, w in windows.items()
              if _add_months(w[1] * 100 + 12, lag) <= self.ym}
        if not ok:
            raise LookupError(
                f"no gravity vintage published by {self.label}; windows "
                f"{windows}. Fails closed rather than using future calibration.")
        best = max(ok, key=lambda v: ok[v][1])
        self._record(Provenance(
            source=f"gravity calibration ({best})",
            reference_period=f"{ok[best][0]}-{ok[best][1]}",
            original_availability_date=_fmt(
                _add_months(ok[best][1] * 100 + 12, lag)),
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=AS_AVAILABLE,
            lookahead_exception=None))
        return best

    # Census released the 2023 delineation in July 2023, not in January.
    # Keying the lookahead test off the calendar year rather than the release
    # month would have called a 2023-01 cutoff clean when it is not.
    GEOGRAPHY_RELEASE_YM = 202307

    def geography_vintage(self) -> str:
        """Census CBSA delineation. Only the 2023 file is cached, so every
        snapshot uses it. Whether that is a lookahead depends on the cutoff.

        Before 2023-07 the file did not exist yet, so using it is genuine
        future information and is declared as such. At or after 2023-07 it is
        the delineation a planner actually held, and no exception is claimed.
        Either way, the vintage is recorded rather than applied silently.
        """
        future = self.ym < self.GEOGRAPHY_RELEASE_YM
        self._record(Provenance(
            source="Census CBSA delineation",
            reference_period="2023",
            original_availability_date="2023-07",
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=STALE_ANCHOR if future else AS_AVAILABLE,
            lookahead_exception=(
                "Published 2023-07, after this cutoff. Only list1_2023.xlsx is "
                "cached; historical delineations are not available offline, so "
                "counties are rolled up to 2023 metro boundaries anyway. W1.3 "
                "audit vector L4, irreducible under the no-network rule."
                if future else None)))
        return "2023"

    def carrier_brand_vintage(self) -> str:
        """models.carriers resolves multi-brand regionals from a fixed DB1B
        year and applies the map to all years. Not effective-dated."""
        self._record(Provenance(
            source="carrier operating-to-brand map",
            reference_period="not effective-dated",
            original_availability_date="n/a",
            data_vintage_date=self.data_vintage_date,
            permitted_cutoff=self.label,
            vintage_policy=LATEST_REVISED,
            lookahead_exception=(
                "carrier_families.csv and carrier_codes.csv carry no effective "
                "dates, and segment_brands() resolves from a fixed DB1B year. "
                "Air Wisconsin flew for United through early June 2023, then American March 2023-April 2025; "
                "Mesa's American agreement ended 2023. W1.3 audit vector L3, "
                "not fixed during Milestone A.")))
        return "not_effective_dated"


def _fmt(ym: int) -> str:
    return f"{ym//100}-{ym%100:02d}"


def admissible_decision_years(first_feasible: int, last_mature: int) -> list[int]:
    """Decision years that are feasible, mature and not an excluded vintage."""
    ex = excluded_decision_vintages()
    return [y for y in range(first_feasible, last_mature + 1) if y not in ex]
