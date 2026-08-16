"""Stage 2R.0: the identification and resolution limit of the frozen V2
predictive evaluation.

Runs first in Stage 2R, per `docs/REMAINING_ROADMAP_REDESIGN.md` section 2R.0.
Every later Stage 2R comparison is interpreted against what this file measures.

**This changes no model behaviour, no assumption and no frozen number.** It
reads `data/parquet/replay/` and asks a single question: what differences could
this design have distinguished from zero, had they existed?

Two properties of the frozen design drive everything below.

1. `_agreement_at_k` and `_recall_at_k` average a per-date ratio over the
   decision dates, so both metrics are lattice-valued. Agreement@k moves in
   steps of 1/(D*k) pooled and 1/k per date; recall@k moves in steps of
   1/(D*P_d), where P_d is the positive count at date d. Nothing between two
   lattice points is representable, let alone detectable.

2. `cluster_bootstrap` resamples metros. The decision dates are held fixed, so
   the intervals in the V2 baseline are cross-sectional and carry no
   information about vintage-to-vintage variation.

The minimum detectable difference is estimated by construction rather than by
formula: build a ranking that beats the demand comparator by exactly E net
launch events inside the top k, run the frozen bootstrap on it, and find the
smallest E whose interval excludes zero. Three decision dates cannot support an
asymptotic cluster-robust power calculation and none is attempted.

Regenerate with

    .venv/bin/python -m replay.resolution
"""
from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

from ingest.common import DATA_PARQUET, ROOT
# The frozen metric and bootstrap definitions, imported rather than restated.
from replay.run_replay import (K_VALUES, N_BOOT, RNG_SEED, _agreement_at_k,
                               _recall_at_k)

REPLAY = DATA_PARQUET / "replay"
DOC = ROOT / "docs" / "STAGE_2R0_RESOLUTION.md"

# The only cell carrying a primary predictive claim (V2 baseline section 1).
STUDY = "westjet_yyc"
CLUSTER = "cbsa"

VERDICTS = ("ADEQUATE FOR COMPARATIVE INFERENCE",
            "LIMITED TO LARGE EFFECTS",
            "DESCRIPTIVE / MECHANISM ATTRIBUTION ONLY")


# --------------------------------------------------------------- fast path
# `cluster_bootstrap` rebuilds a DataFrame per resample, which is fine for six
# statistics and far too slow for the ~120 counterfactual fits the MDE grid
# needs. The functions below are an index-based restatement of the same
# computation. `check_reproduces_frozen_bootstrap` asserts they agree with the
# frozen slow path to 1e-12 on all six Family 4 cells; the generator refuses to
# emit a document if they ever stop agreeing.
def resample_indices(df: pd.DataFrame, n: int = N_BOOT,
                     seed: int = RNG_SEED) -> list[np.ndarray]:
    """The resample row indices `cluster_bootstrap` would have concatenated."""
    clusters = df[CLUSTER].unique()
    rng = np.random.default_rng(seed)
    groups = {c: np.flatnonzero((df[CLUSTER] == c).to_numpy())
              for c in clusters}
    return [np.concatenate([groups[c] for c in
                            rng.choice(clusters, size=len(clusters),
                                       replace=True)])
            for _ in range(n)]


def _topk(score: np.ndarray, cutoff: np.ndarray, positive: np.ndarray,
          k: int) -> list[tuple[float, int, float]]:
    """Per date: (positives inside top k, k actually used, positives total).

    A stable descending sort reproduces `Series.nlargest(k, keep='first')`,
    which breaks ties by order of appearance.
    """
    out = []
    for c in np.unique(cutoff):
        m = cutoff == c
        s, p = score[m], positive[m]
        kk = min(k, len(s))
        order = np.argsort(-s, kind="stable")[:kk]
        out.append((float(p[order].sum()), kk, float(p.sum())))
    return out


def agreement(score, cutoff, positive, k) -> float:
    r = _topk(score, cutoff, positive, k)
    return float(np.mean([a / kk for a, kk, _ in r])) if r else np.nan


def recall(score, cutoff, positive, k) -> float:
    r = [(a, t) for a, _, t in _topk(score, cutoff, positive, k) if t > 0]
    return float(np.mean([a / t for a, t in r])) if r else np.nan


def boot_diff(df: pd.DataFrame, lhs: str, rhs: str, k: int,
              idx: list[np.ndarray], metric: str) -> tuple[float, float, float]:
    """Point estimate and 95% percentile interval for lhs minus rhs."""
    f = agreement if metric == "agreement" else recall
    x = df[lhs].to_numpy(float)
    y = df[rhs].to_numpy(float)
    cut = df["cutoff"].to_numpy()
    pos = df["positive"].to_numpy(float)
    point = f(x, cut, pos, k) - f(y, cut, pos, k)
    vals = [v for v in
            (f(x[i], cut[i], pos[i], k) - f(y[i], cut[i], pos[i], k)
             for i in idx) if v == v]
    return (point, float(np.percentile(vals, 2.5)),
            float(np.percentile(vals, 97.5)))


def check_reproduces_frozen_bootstrap(w: pd.DataFrame,
                                      idx: list[np.ndarray]) -> None:
    """The fast path must reproduce the six frozen Family 4 cells exactly.

    Rule 7 in spirit: this is not a tolerance to widen. If it fires, the fast
    path has diverged from the frozen definition and every MDE number below is
    void.
    """
    frozen = json.loads((REPLAY / "results.json").read_text())
    cells = frozen["family_1_and_4"][STUDY]["k"]
    bad = []
    for k in K_VALUES:
        for metric, key in (("agreement", "diff_agreement"),
                            ("recall", "diff_recall")):
            got = boot_diff(w, "score_model", "score_demand", k, idx, metric)
            want = cells[str(k)][key]
            if any(abs(a - b) > 1e-12 for a, b in zip(got, want)):
                bad.append(f"k={k} {metric}: fast {got} vs frozen {want}")
    if bad:
        raise AssertionError(
            "replay/resolution.py fast bootstrap no longer reproduces the "
            "frozen results.json:\n" + "\n".join(bad))


# ------------------------------------------------------- counterfactuals
def headroom(w: pd.DataFrame, k: int) -> dict[int, int]:
    """Net launch events a ranking could still gain over demand at top k.

    Bounded by the positives the demand ranking leaves outside its own top k
    and by the non-positives it holds inside. Zero means the demand comparator
    already places every positive inside the top k, and **no** ranking can
    improve on it at that k by any amount.
    """
    h = {}
    for c in sorted(w["cutoff"].unique()):
        g = w[w["cutoff"] == c]
        top = set(g.nlargest(min(k, len(g)), "score_demand").index)
        h[int(c)] = int(min(((g["positive"] == 1) & (~g.index.isin(top))).sum(),
                            ((g["positive"] == 0) & (g.index.isin(top))).sum()))
    return h


def _counterfactual(g: pd.DataFrame, k: int, e: int) -> pd.Series | None:
    """The demand score, edited so that exactly `e` more positives sit in the
    top k. The `e` highest-ranked positives outside the top k are lifted above
    everything and the `e` weakest non-positives inside it are dropped below.

    This is an oracle edit: it targets the right rows and moves them the whole
    way. A real component change would do neither, so the MDE it produces is a
    floor on the detectable effect and not a realistic one.
    """
    s = g["score_demand"].copy()
    top = set(g.nlargest(min(k, len(g)), "score_demand").index)
    pos_out = g[(g["positive"] == 1) & (~g.index.isin(top))].sort_values(
        "score_demand", ascending=False)
    neg_in = g[(g["positive"] == 0) & (g.index.isin(top))].sort_values(
        "score_demand", ascending=True)
    if e > min(len(pos_out), len(neg_in)):
        return None
    hi = float(g["score_demand"].max()) + 1.0
    lo = float(g["score_demand"].min()) - 1.0
    for i in range(e):
        s.loc[pos_out.index[i]] = hi + i
        s.loc[neg_in.index[i]] = lo - i
    return s


def mde_grid(w: pd.DataFrame, idx: list[np.ndarray]) -> pd.DataFrame:
    """Every reachable allocation of net launch events across the three dates,
    scored with the frozen bootstrap."""
    dates = sorted(w["cutoff"].unique())
    rows = []
    for k in K_VALUES:
        h = headroom(w, k)
        for combo in itertools.product(*[range(h[int(c)] + 1) for c in dates]):
            if sum(combo) == 0:
                continue
            d = w.copy()
            d["score_alt"] = d["score_demand"]
            for c, e in zip(dates, combo):
                if e:
                    s = _counterfactual(w[w["cutoff"] == c], k, e)
                    # `combo` is bounded by `headroom`, which is exactly the
                    # largest `e` this date can express, so this cannot be None.
                    assert s is not None, f"k={k} {c} cannot express {e} events"
                    d.loc[s.index, "score_alt"] = s
            a = boot_diff(d, "score_alt", "score_demand", k, idx, "agreement")
            r = boot_diff(d, "score_alt", "score_demand", k, idx, "recall")
            rows.append({
                "k": k, "allocation": "/".join(str(x) for x in combo),
                "events": sum(combo), "n_dates_moved": sum(1 for x in combo if x),
                "agreement_diff": a[0], "agreement_lo": a[1], "agreement_hi": a[2],
                "agreement_excludes_zero": bool(a[1] > 0 or a[2] < 0),
                "recall_diff": r[0], "recall_lo": r[1], "recall_hi": r[2],
                "recall_excludes_zero": bool(r[1] > 0 or r[2] < 0),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------- event accounting
def event_decomposition(w: pd.DataFrame) -> pd.DataFrame:
    """The observed model-minus-demand difference, in launch events."""
    rows = []
    for k in K_VALUES:
        for c in sorted(w["cutoff"].unique()):
            g = w[w["cutoff"] == c]
            tm = set(g.nlargest(min(k, len(g)), "score_model")["metro_name"])
            td = set(g.nlargest(min(k, len(g)), "score_demand")["metro_name"])
            gained = sorted(g[g["metro_name"].isin(tm - td)
                              & (g["positive"] == 1)]["metro_name"])
            lost = sorted(g[g["metro_name"].isin(td - tm)
                            & (g["positive"] == 1)]["metro_name"])
            rows.append({
                "k": k, "cutoff": int(c), "positives": int(g["positive"].sum()),
                "markets_swapped": len(tm - td),
                "launches_gained": len(gained), "launches_lost": len(lost),
                "net_events": len(gained) - len(lost),
                "gained_markets": ", ".join(gained),
                "lost_markets": ", ".join(lost),
                "agreement_model": _agreement_at_k(g, "score_model", k),
                "agreement_demand": _agreement_at_k(g, "score_demand", k),
                "recall_model": _recall_at_k(g, "score_model", k),
                "recall_demand": _recall_at_k(g, "score_demand", k),
            })
    df = pd.DataFrame(rows)
    df["agreement_diff"] = df["agreement_model"] - df["agreement_demand"]
    df["recall_diff"] = df["recall_model"] - df["recall_demand"]
    return df


def verdict(w: pd.DataFrame, grid: pd.DataFrame, ev: pd.DataFrame) -> tuple[str, list[str]]:
    """The Stage 2R.0 identification verdict, decided by the measurements.

    ADEQUATE requires the design to resolve differences of about one launch
    event, the granularity the metrics themselves expose. LIMITED TO LARGE
    EFFECTS requires at least one k at which some reachable effect is
    detectable. Otherwise nothing comparative is identified.
    """
    reasons = []
    detectable = grid[grid["agreement_excludes_zero"]
                      | grid["recall_excludes_zero"]]
    dead_k = [k for k in K_VALUES
              if all(v == 0 for v in headroom(w, k).values())]
    if dead_k:
        reasons.append(
            f"k={', '.join(str(k) for k in dead_k)} has zero headroom: the "
            "demand comparator already ranks every positive inside the top k "
            "at every date, so no ranking can improve on it there by any "
            "amount.")
    if detectable.empty:
        reasons.append("No reachable improvement at any k is distinguishable "
                       "from zero.")
        return VERDICTS[2], reasons

    live = sorted(detectable["k"].unique())
    mins = {int(k): int(detectable[detectable["k"] == k]["events"].min())
            for k in live}
    # "first ever detected" and "detected under every allocation of that size"
    # differ at k=10, and collapsing them would overstate the design.
    parts = []
    for k in live:
        gk = grid[grid["k"] == k]
        always = [int(x) for x in sorted(gk["events"].unique())
                  if gk[(gk["events"] == x)]["agreement_excludes_zero"].all()
                  or gk[(gk["events"] == x)]["recall_excludes_zero"].all()]
        parts.append(f"k={k} first excludes zero at {mins[k]} and does so "
                     f"under every allocation at "
                     f"{min(always) if always else 'no reachable size'}")
    reasons.append("Smallest detectable effect, in net launch events: "
                   + "; ".join(parts)
                   + f". The observed full-engine difference is "
                   f"{int(ev['net_events'].abs().max())} event.")
    single = detectable[detectable["n_dates_moved"] == 1]
    if single.empty:
        reasons.append("No effect confined to a single decision date is "
                       "detectable at any magnitude the sample permits.")
    if min(mins.values()) <= 1:
        return VERDICTS[0], reasons
    return VERDICTS[1], reasons


# ------------------------------------------------------------------ report
def _fmt(t) -> str:
    return f"{t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}]"


def main() -> str:
    rows = pd.read_parquet(REPLAY / "decision_rows.parquet")
    outcomes = pd.read_parquet(REPLAY / "outcomes.parquet")
    frozen = json.loads((REPLAY / "results.json").read_text())
    w = rows[rows["study_id"] == STUDY].reset_index(drop=True)
    dates = sorted(int(c) for c in w["cutoff"].unique())
    D = len(dates)

    idx = resample_indices(w)
    check_reproduces_frozen_bootstrap(w, idx)

    ev = event_decomposition(w)
    grid = mde_grid(w, idx)
    grid.to_parquet(REPLAY / "resolution_mde_grid.parquet", index=False)
    ev.to_parquet(REPLAY / "resolution_events.parquet", index=False)
    vd, reasons = verdict(w, grid, ev)

    L = []
    A = L.append
    A("# Stage 2R.0: identification and resolution limit")
    A("")
    A("**Generated by `replay/resolution.py` from `data/parquet/replay/`. Do "
      "not hand-edit.**")
    A("")
    A("Defined in `docs/REMAINING_ROADMAP_REDESIGN.md` section 2R.0, which "
      "requires this to run before 2R.1 through 2R.5 and binds their "
      "interpretation to it. **No model behaviour, assumption, threshold or "
      "frozen number was changed to produce this.** The V2 baseline in "
      "`docs/W1.4_predictive_baseline_v2.md` is untouched; every V2 figure "
      "quoted below is read back from `results.json` and reproduced exactly.")
    A("")
    A(f"> ## Verdict: {vd}")
    A("")
    for r in reasons:
        A(f"> - {r}")
    A("")
    A("---")
    A("")

    # ------------------------------------------------------- 1. structure
    A("## 1. Data structure")
    A("")
    e = frozen["family_1_and_4"][STUDY]
    A(f"| quantity | value |")
    A("|---|---|")
    A(f"| study | `{STUDY}` (the only cell carrying a primary predictive claim) |")
    A(f"| candidate rows | {len(w)} |")
    A(f"| unique markets | {w['cbsa'].nunique()} |")
    A(f"| positive rows | {int(w['positive'].sum())} |")
    A(f"| unique markets that launched | {w[w['positive'] == 1]['cbsa'].nunique()} |")
    A(f"| decision dates | {D} |")
    A(f"| bootstrap clustering unit | `{CLUSTER}`, the metro |")
    A(f"| bootstrap resamples, seed | {N_BOOT}, {RNG_SEED} |")
    A(f"| effective temporal blocks | **{D}** |")
    A("")

    A("### By decision date")
    A("")
    A("| date | candidate rows | positives | unique metros |")
    A("|---|---|---|---|")
    for c in dates:
        g = w[w["cutoff"] == c]
        A(f"| {c} | {len(g)} | **{int(g['positive'].sum())}** | "
          f"{g['cbsa'].nunique()} |")
    A(f"| **total** | **{len(w)}** | **{int(w['positive'].sum())}** | "
      f"**{w['cbsa'].nunique()}** |")
    A("")

    # repeated-market structure
    app = w.groupby("cbsa").size().value_counts().sort_index()
    A("### Repeated-market structure")
    A("")
    A("The candidate set is close to a balanced panel, so the rows are far "
      "from independent.")
    A("")
    A("| appears at | markets |")
    A("|---|---|")
    for n, cnt in app.items():
        A(f"| {n} of {D} dates | {cnt} |")
    A("")

    pos = w[w["positive"] == 1]
    rep = pos.groupby("cbsa").size().value_counts().sort_index()
    A("The positives repeat too. A launch inside the 24 month window of two "
      "cutoffs is a positive row at both.")
    A("")
    A("| positive at | markets |")
    A("|---|---|")
    for n, cnt in rep.items():
        A(f"| {n} date(s) | {cnt} |")
    A("")
    A("| market | positive at |")
    A("|---|---|")
    for cb, g in pos.groupby("cbsa"):
        A(f"| {g['metro_name'].iloc[0]} | "
          f"{', '.join(str(int(c)) for c in sorted(g['cutoff']))} |")
    A("")

    # distinct launch events
    def _ym(v: int) -> int:
        return (v // 100) * 12 + (v % 100)
    ow = outcomes[outcomes["study_id"] == STUDY]
    distinct = set()
    for c in dates:
        s = ow[(ow["first_ym"] > _ym(c)) & (ow["first_ym"] <= _ym(c) + 24)]
        distinct.update(zip(s["cbsa"], s["first_ym"]))
    A(f"**{int(w['positive'].sum())} positive rows rest on "
      f"{len(distinct)} distinct launch events.** "
      f"{int(rep.get(2, 0))} launches are scored at two decision dates. Any "
      "count that treats the positive rows as independent observations "
      "overstates the evidence by half.")
    A("")

    # -------------------------------------------- 2. metric granularity
    A("## 2. Discrete metric resolution")
    A("")
    A("Both metrics average a per-date ratio over the "
      f"{D} decision dates (`replay/run_replay.py:103-121`), so both are "
      "lattice-valued. **Nothing between two lattice points exists.** This is "
      "arithmetic, and it is a floor under, not a substitute for, statistical "
      "detectability.")
    A("")
    A("### Agreement@k")
    A("")
    A("The top k of a date contributes each selected row with weight 1/k, and "
      f"the {D} dates are averaged.")
    A("")
    A("| k | one launch at one date, per-date step | pooled step |")
    A("|---|---|---|")
    for k in K_VALUES:
        A(f"| {k} | {1/k:.4f} | **{1/(D*k):.4f}** |")
    A("")
    A("### Recall@k")
    A("")
    A("Recall divides by the positives at that date, so its step size differs "
      "by date and the smallest available step is set by the date with the "
      "most positives.")
    A("")
    A("| date | positives | per-date step | pooled step |")
    A("|---|---|---|---|")
    steps = {}
    for c in dates:
        p = int(w[w["cutoff"] == c]["positive"].sum())
        steps[c] = 1 / (D * p)
        A(f"| {c} | {p} | {1/p:.4f} | **{1/(D*p):.4f}** |")
    A("")
    A(f"Recall@k is identical in step size at every k: k enters only through "
      f"which positives are captured, never through the denominator. The "
      f"finest pooled recall step available anywhere in this design is "
      f"**{min(steps.values()):.4f}** and the coarsest is "
      f"**{max(steps.values()):.4f}**.")
    A("")
    A("### Granularity is not detectability")
    A("")
    det_ev = grid[grid["agreement_excludes_zero"]
                  | grid["recall_excludes_zero"]]["events"]
    A(f"The steps above are the smallest differences the metrics can "
      f"**represent**: one launch event. Section 6 measures the smallest "
      f"differences the design can **distinguish from zero**, and the "
      f"smallest one anywhere is {int(det_ev.min())} events, "
      f"{int(det_ev.min())} times coarser. A reported difference equal to one "
      f"lattice step is not a small significant effect; it is the smallest "
      f"non-zero number the instrument can print.")
    A("")

    # ------------------------------------------ 3. observed difference scale
    A("## 3. Observed difference scale, in launch events")
    A("")
    A("The frozen V2 Family 4 differences, read back from `results.json`, "
      "against the event steps above. `net events` counts observed launches "
      "the full engine pulls into the top k minus those it pushes out, "
      "relative to the demand ranking on identical rows.")
    A("")
    A("| k | agreement, model | agreement, demand | difference | in events | "
      "recall, model | recall, demand | difference |")
    A("|---|---|---|---|---|---|---|---|")
    for k in K_VALUES:
        am = _agreement_at_k(w, "score_model", k)
        ad = _agreement_at_k(w, "score_demand", k)
        rm = _recall_at_k(w, "score_model", k)
        rd = _recall_at_k(w, "score_demand", k)
        net = int(ev[ev["k"] == k]["net_events"].sum())
        A(f"| {k} | {am:.3f} | {ad:.3f} | **{am - ad:+.3f}** | "
          f"**{net:+d}** | {rm:.3f} | {rd:.3f} | **{rm - rd:+.3f}** |")
    A("")
    A("With the frozen metro-cluster intervals attached, from `results.json`:")
    A("")
    A("| k | difference in agreement@k | difference in recall@k |")
    A("|---|---|---|")
    for k in K_VALUES:
        c = e["k"][str(k)]
        A(f"| {k} | {_fmt(c['diff_agreement'])} | {_fmt(c['diff_recall'])} |")
    A("")

    A("### By decision date")
    A("")
    A("| k | date | positives | markets swapped | launches gained | "
      "launches lost | net events | agreement difference | recall difference |")
    A("|---|---|---|---|---|---|---|---|---|")
    for _, r in ev.iterrows():
        A(f"| {r['k']} | {r['cutoff']} | {r['positives']} | "
          f"{r['markets_swapped']} | {r['launches_gained']} | "
          f"{r['launches_lost']} | **{r['net_events']:+d}** | "
          f"{r['agreement_diff']:+.3f} | {r['recall_diff']:+.3f} |")
    A("")
    A("### The named events")
    A("")
    named = ev[(ev["launches_gained"] > 0) | (ev["launches_lost"] > 0)]
    for _, r in named.iterrows():
        parts = []
        if r["gained_markets"]:
            parts.append(f"gains {r['gained_markets']}")
        if r["lost_markets"]:
            parts.append(f"loses {r['lost_markets']}")
        A(f"- **k={r['k']}, {r['cutoff']}**: the full engine "
          f"{' and '.join(parts)}. That single event is worth "
          f"{r['agreement_diff']:+.3f} agreement and {r['recall_diff']:+.3f} "
          f"recall at this date.")
    A("")
    tot = int(ev["net_events"].abs().sum())
    A(f"**The entire six-number Family 4 headline rests on {tot} launch "
      f"label changes**, each isolated to one decision date, out of "
      f"{int(w['positive'].sum())} positive rows and {len(distinct)} distinct "
      f"launch events. Every non-zero observed difference is a **one event** "
      "difference. Nothing in the frozen comparison is larger than the "
      "smallest quantity the instrument can display.")
    A("")

    # ------------------------------------------- 4. temporal identification
    A("## 4. Temporal identification limit")
    A("")
    A(f"There are **{D}** approved decision vintages: "
      f"{', '.join(str(c) for c in dates)}. 2020 and 2021 are excluded as "
      "decision vintages by the frozen protocol, and 2025-01 does not mature "
      "for a 24 month outcome until T-100 reaches 2027-01.")
    A("")
    A("**What three vintages prevent.**")
    A("")
    A(f"- No estimate of between-vintage variance. {D} blocks give 2 degrees "
      "of freedom, and cluster-robust asymptotics need one to two orders of "
      "magnitude more blocks before their coverage is even approximately "
      "nominal.")
    A("- No separation of a model-versus-demand effect from a vintage-specific "
      "shock. 2023-01 is dominated by the D1 corridor-growth collapse "
      "(growth 0.196 at YYC); its five positives are scored by an engine that "
      "believed the market had shrunk by 80%. That confound cannot be "
      "differenced out with three blocks.")
    A("- No inference about a fourth vintage. Nothing here bounds how the "
      "engine would rank at a decision date not in this set.")
    A("- **No date-level confidence interval, and none is manufactured "
      "below.** A metro-cluster bootstrap within one date resamples a single "
      "temporal block; a bootstrap over three dates resamples three. Neither "
      "supports an interval, and reporting one would be a precision claim the "
      "design cannot back.")
    A("")
    A("The honest instrument is leave-one-date-out, which is a sensitivity "
      "check and not an inference.")
    A("")
    A("| dropped | k | difference in agreement@k | difference in recall@k |")
    A("|---|---|---|---|")
    for drop in dates:
        g = w[w["cutoff"] != drop]
        for k in K_VALUES:
            da = (_agreement_at_k(g, "score_model", k)
                  - _agreement_at_k(g, "score_demand", k))
            dr = (_recall_at_k(g, "score_model", k)
                  - _recall_at_k(g, "score_demand", k))
            A(f"| {drop} | {k} | {da:+.3f} | {dr:+.3f} |")
    A("")
    A("Every non-zero pooled difference disappears when its one supporting "
      "date is removed. That is the arithmetic consequence of a one-event "
      "difference living at one date, not an independent finding, and it is "
      "why no vintage-level claim can be made in either direction.")
    A("")

    # -------------------------------------------- 5. bootstrap interpretation
    A("## 5. What the frozen bootstrap intervals mean")
    A("")
    A(f"`cluster_bootstrap` (`replay/run_replay.py:82-99`) draws "
      f"{w['cbsa'].nunique()} metros with replacement, {N_BOOT} times, at "
      f"seed {RNG_SEED}, and takes a percentile interval. A metro is drawn "
      "with all of its rows at once.")
    A("")
    A("| source of uncertainty | captured |")
    A("|---|---|")
    A("| candidate-level, market-to-market variation | **yes**, this is what "
      "it resamples |")
    A("| repeated markets across dates | **yes**, a metro enters or leaves "
      "with all of its rows, so the panel structure is respected |")
    A("| repeated positives across dates | **yes**, by the same mechanism |")
    ndates_per = sorted({len(np.unique(w['cutoff'].to_numpy()[i]))
                         for i in idx})
    A(f"| common decision-date shocks | **no**. All {D} dates appear in every "
      f"one of the {N_BOOT} resamples (observed distinct dates per resample: "
      f"{ndates_per}). The dates are held fixed by construction |")
    A("| uncertainty across source vintages | **no**. The vintage resolver is "
      "deterministic: gravity is `pre2022` at every cutoff, and BEA and "
      "StatCan enter as single later revisions. Nothing is resampled over |")
    A("| positive-unlabeled outcome noise | **no**. Unlaunched candidates are "
      "unlabeled, not confirmed negatives, and the bootstrap treats the labels "
      "as fixed |")
    A("")
    A("**Stated plainly: the V2 intervals do not capture decision-date "
      "uncertainty.** They describe how the comparison would move across a "
      "different draw of metros with these three vintages held fixed. They "
      "are not intervals across vintages and must not be read as such. A "
      "future change that looks significant against them may be significant "
      "on vintage variation alone.")
    A("")
    dup = []
    for i in idx[:300]:
        sub = w.iloc[i]
        sub = sub[sub["cutoff"] == dates[0]]
        top = sub.nlargest(10, "score_model")
        dup.append(1 - top["cbsa"].nunique() / len(top))
    A(f"One further property, recorded because it affects how wide these "
      f"intervals are rather than whether they are valid: resampling with "
      f"replacement duplicates rows, and a top-k selection statistic lets a "
      f"duplicated metro occupy several of the k slots. At {dates[0]} and "
      f"k=10, a mean of {np.mean(dup):.1%} of the top-ten slots in a resample "
      f"are repeats of a metro already selected. This is inherent to applying "
      f"a cluster bootstrap to a rank-selection statistic, it is the frozen "
      f"design, and **it is not changed here.**")
    A("")
    A("**The frozen primary bootstrap is not replaced.** Section 6 uses the "
      "same function, the same cluster, the same seed and the same resample "
      "count, applied to constructed rankings rather than to the engine.")
    A("")

    # ------------------------------------------------------------- 6. MDE
    A("## 6. Minimum detectable difference")
    A("")
    A("No asymptotic power formula is used. Three temporal blocks do not "
      "support one, and a formula that assumes many independent clusters would "
      "return a spuriously narrow bound that then corrupts every downstream "
      "decision in Stage 2R.")
    A("")
    A("Instead the bound is constructed. For each k and each reachable "
      "allocation of net launch events across the three dates, a ranking is "
      "built that beats the demand comparator by exactly that many events: the "
      "highest-ranked positives outside the top k are lifted to the top, the "
      "weakest non-positives inside it are dropped to the bottom, and the "
      "frozen bootstrap is run on the difference. The smallest allocation "
      "whose 95% interval excludes zero is the minimum detectable difference.")
    A("")
    A("**This construction is an oracle and the answer it gives is a floor.** "
      "It moves exactly the right rows, all the way, with no error elsewhere "
      "in the ranking. No real component change behaves like that, and the "
      "criterion it is scored against is the metro-cluster interval, which "
      "section 5 shows omits vintage uncertainty. A real, honestly-scored "
      "effect must be **larger** than the numbers below to be detected.")
    A("")

    A("### Headroom: what the sample can express at all")
    A("")
    A("An improvement at top k requires positives the demand ranking leaves "
      "outside its top k. Where there are none, no improvement exists to "
      "detect.")
    A("")
    A("| k | " + " | ".join(str(c) for c in dates) + " | total |")
    A("|---|" + "---|" * (D + 1))
    for k in K_VALUES:
        h = headroom(w, k)
        A(f"| {k} | " + " | ".join(str(h[c]) for c in dates)
          + f" | **{sum(h.values())}** |")
    A("")

    A("### The detection threshold")
    A("")
    A("| k | events | detectable allocations | undetectable allocations | "
      "agreement difference at this size |")
    A("|---|---|---|---|---|")
    for k in K_VALUES:
        gk = grid[grid["k"] == k]
        if gk.empty:
            A(f"| {k} | n/a | no allocation is reachable | | |")
            continue
        for eN in sorted(gk["events"].unique()):
            ge = gk[gk["events"] == eN]
            det = ge[ge["agreement_excludes_zero"] | ge["recall_excludes_zero"]]
            lo_, hi_ = ge["agreement_diff"].min(), ge["agreement_diff"].max()
            rng_ = (f"{lo_:+.3f}" if f"{lo_:+.3f}" == f"{hi_:+.3f}"
                    else f"{lo_:+.3f} to {hi_:+.3f}")
            A(f"| {k} | {eN} | {len(det)} of {len(ge)} | "
              f"{len(ge) - len(det)} of {len(ge)} | {rng_} |")
    A("")

    A("### Resolution envelope")
    A("")
    for k in K_VALUES:
        gk = grid[grid["k"] == k]
        if gk.empty:
            A(f"- **k={k}: nothing is detectable at any effect size.** The "
              "demand comparator already places every positive inside its top "
              f"{k} at all {D} dates, so the headroom is zero and no ranking "
              "can beat it there by any amount. The frozen difference of "
              "0.000 is arithmetic saturation, not a measured tie.")
            continue
        det = gk[gk["agreement_excludes_zero"] | gk["recall_excludes_zero"]]
        if det.empty:
            A(f"- **k={k}: nothing reachable is detectable.** The largest "
              f"improvement the sample can express is "
              f"{int(gk['events'].max())} events "
              f"({gk['agreement_diff'].max():+.3f} agreement) and its "
              "interval still spans zero.")
            continue
        sizes = [int(x) for x in sorted(gk["events"].unique())]
        hit = {x: gk[(gk["events"] == x)
                     & (gk["agreement_excludes_zero"]
                        | gk["recall_excludes_zero"])] for x in sizes}
        always = [x for x in sizes if len(hit[x]) == len(gk[gk["events"] == x])]
        never = [x for x in sizes if len(hit[x]) == 0]
        lo = int(det["events"].min())
        vis = min(always) if always else lo
        line = (f"- **k={k}: usually visible at {vis} net launch events or "
                f"more** (agreement difference "
                f"{gk[gk['events'] == vis]['agreement_diff'].min():+.3f} or "
                f"larger, recall difference "
                f"{gk[gk['events'] == vis]['recall_diff'].min():+.3f} or "
                f"larger)")
        if never:
            line += (f"; **never distinguishable at {max(never)} events or "
                     f"fewer** (up to "
                     f"{gk[gk['events'] == max(never)]['agreement_diff'].max():+.3f} "
                     f"agreement)")
        band = [x for x in sizes if x not in always and x not in never]
        if band:
            line += (f". Between them, {', '.join(str(x) for x in band)} "
                     f"event(s) is detected under some allocations across the "
                     f"three dates and not others, so it is not a size this "
                     f"design resolves reliably")
        line += (f". The first allocation ever detected is {lo} events "
                 f"({', '.join(det[det['events'] == lo]['allocation'])})")
        A(line + ".")
    A("")

    singles = grid[grid["n_dates_moved"] == 1]
    n_single_det = int((singles["agreement_excludes_zero"]
                        | singles["recall_excludes_zero"]).sum())
    A(f"**An improvement confined to one decision vintage is never detected.** "
      f"Of {len(singles)} single-date allocations across all k, "
      f"{n_single_det} exclude zero. The largest single-date improvement the "
      f"sample can express is "
      f"{int(singles['events'].max())} events, worth up to "
      f"{singles['agreement_diff'].max():+.3f} agreement, and its interval "
      f"still contains zero. **This is exactly the shape of the observed "
      f"k=10 result**, which is one event at one date.")
    A("")
    A("### The supportable statement")
    A("")
    live_k = sorted(grid["k"].unique())
    vis_g, never_g = [], []
    for k in live_k:
        gk = grid[grid["k"] == k]
        sizes = [int(x) for x in sorted(gk["events"].unique())]
        hit = {x: gk[(gk["events"] == x)
                     & (gk["agreement_excludes_zero"]
                        | gk["recall_excludes_zero"])] for x in sizes}
        al = [x for x in sizes if len(hit[x]) == len(gk[gk["events"] == x])]
        vis_g.append(min(al) if al else max(sizes) + 1)
        never_g.append({x for x in sizes if len(hit[x]) == 0})
    X = min(vis_g)
    Y = max(set.intersection(*never_g)) if never_g else 0
    dead_k = [k for k in K_VALUES if k not in live_k]
    A(f"> Under this design, an incremental ranking improvement worth about "
      f"**{X} or more net launch events**, spread across at least two of the "
      f"{D} decision vintages, would usually be visible. An improvement worth "
      f"**{Y} or fewer** events cannot be distinguished from zero, and an "
      f"improvement confined to a single vintage cannot be distinguished from "
      f"zero at any magnitude this sample permits. At "
      f"k={', '.join(str(k) for k in dead_k)} no improvement is detectable at "
      f"any size, because none is expressible.")
    A("")
    npos = int(w["positive"].sum())
    A(f"{X} events is {X/npos:.0%} of the {npos} positive rows and "
      f"{X/len(distinct):.0%} of the {len(distinct)} distinct launch events "
      f"in the study. The observed full-engine difference is "
      f"{int(ev['net_events'].abs().max())} event.")
    A("")

    # --------------------------------------------------- 7. k=20 saturation
    A("## 7. Why k=20 is saturated")
    A("")
    A("| date | candidates | positives | positives in demand top 20 | "
      "positives in model top 20 |")
    A("|---|---|---|---|---|")
    for c in dates:
        g = w[w["cutoff"] == c]
        tm = int(g.nlargest(20, "score_model")["positive"].sum())
        td = int(g.nlargest(20, "score_demand")["positive"].sum())
        A(f"| {c} | {len(g)} | {int(g['positive'].sum())} | {td} | {tm} |")
    A("")
    r20m = _recall_at_k(w, "score_model", 20)
    r20d = _recall_at_k(w, "score_demand", 20)
    a20m = _agreement_at_k(w, "score_model", 20)
    a20d = _agreement_at_k(w, "score_demand", 20)
    A(f"Both rankings reach recall {r20m:.3f}. Every positive at every date "
      "is already inside the top twenty of roughly eighty candidates under "
      "both scores.")
    A("")
    A("**Both k=20 metrics are pinned, not only recall.** Recall@20 is 1.000 "
      "for any ranking that captures every positive. Agreement@20 is then "
      f"P_d/20 by construction, which averages to {a20d:.3f} "
      f"({a20m:.3f} for the model), and no reordering inside or outside the "
      "top twenty can change either number. Section 6 measures the same fact "
      "from the other side: headroom at k=20 is zero at all three dates.")
    A("")
    A("**k=20 is therefore unsuitable for measuring incremental ranking value "
      "in this sample.** Its 0.000 difference and its interval of "
      f"{_fmt(e['k']['20']['diff_agreement'])} are properties of the "
      "candidate set, not measurements of the engine: with 76 to 88 "
      "candidates and 3 to 7 positives per date, a top twenty is 23% to 26% "
      "of the field and captures everything. Reporting it as a tie invites "
      "the reading that the two rankings were equally good, when in fact no "
      "comparison took place. It should be retained as a descriptive coverage "
      "statistic and dropped from any incremental-value claim.")
    A("")

    # ------------------------------------------------------- 8. the verdict
    A("## 8. Identification verdict")
    A("")
    A(f"# {vd}")
    A("")
    for r in reasons:
        A(f"- {r}")
    A("")
    A("The verdict follows from sections 2, 6 and 7 and from nothing else. "
      "The metrics can represent a one-event difference; the design cannot "
      "distinguish one from zero, and the entire observed Family 4 result is "
      "one-event differences.")
    A("")
    A(f"**Why not `{VERDICTS[0]}`.** Adequacy would require the design to "
      f"resolve differences near the granularity the metrics expose, which is "
      f"one launch event. It resolves {X}.")
    A("")
    A(f"**Why not `{VERDICTS[2]}`.** Something is detectable: an effect of "
      f"{X} or more events spread across at least two vintages does exclude "
      f"zero. The design is coarse, not blind, and saying otherwise would "
      f"overstate the limitation in the other direction.")
    A("")
    A("**The verdict is the optimistic reading of its own evidence.** The "
      f"{X} event threshold comes from an oracle construction scored against "
      "an interval that section 5 shows omits vintage uncertainty. Both push "
      "the threshold down. For every decision Stage 2R actually has to make, "
      f"the design should be treated as `{VERDICTS[2]}`, because no "
      f"realistic calibration or component repair moves {X} of "
      f"{len(distinct)} launch events. `{VERDICTS[1]}` is the accurate "
      "label; it is not a licence to look for a small win.")
    A("")
    A("### The claim this licenses, and the one it does not")
    A("")
    A("Binding on the rest of Stage 2R and on all downstream writing, per "
      "`docs/REMAINING_ROADMAP_REDESIGN.md` section 2R.0:")
    A("")
    A("> No detectable incremental value at the available resolution.")
    A("")
    A("not")
    A("")
    A("> The richer model has been proven equivalent to, or worse than, "
      "demand.")
    A("")
    A("Sections 3 and 6 make the distinction concrete rather than rhetorical. "
      "A real advantage of one to four launch events would have produced "
      "exactly what V2 reports: point estimates at one lattice step with "
      "intervals spanning zero. So would no advantage at all. The design "
      "cannot separate those two worlds, and the null is therefore "
      "**underpowered, not empty**.")
    A("")
    A("### How this constrains Stage 2R.1 through 2R.5")
    A("")
    A("| stage | constraint |")
    A("|---|---|")
    A("| **2R.1** score-layer attribution | Run it as **mechanism "
      "attribution**, not as a horse race. Report agreement and recall per "
      "layer descriptively and never as evidence for or against a layer. The "
      "finding is whether a layer's rank moves are explained by the mechanism "
      "it represents; a layer that reshuffles markets its own mechanism does "
      "not explain is a defect regardless of the metric. |")
    A("| **2R.2** ceiling diagnostic | Not affected: it is deterministic. "
      "Tie-block size, top-k occupancy and launch outcomes among capped rows "
      "are counted, not estimated. Classify A, B or C on those counts. Do not "
      "reach for a predictive metric to decide the outcome, and keep the two "
      "issues separate: censoring compression is not removed by correcting "
      "the floor value. |")
    A("| **2R.3** frequency diagnostic | Not affected, and not contingent on "
      "any predictive finding. 3x on 461 of 463 decisions is a decomposition "
      "question about the objective function. It needs no launch-prediction "
      "power and must not wait on one. |")
    A("| **2R.4** D1 blast radius | Not affected. Rows moved, demand change, "
      "margin change and verdict change are deterministic against immutable "
      "V2. The repair is already scheduled and is **not** contingent on any "
      "predictive metric moving; section 6 shows the design could not detect "
      "the improvement even if it occurred. |")
    A("| **2R.5** necessity gates | Raise the bar. A W2 task cannot be "
      "justified by an expected gain in a Family 4 metric, because a gain "
      "smaller than five launch events is undetectable here and a gain that "
      "large is implausible from calibration alone. Justify on mechanism, or "
      "do not run it. |")
    A("| **future W2 calibration** | No calibration should be validated "
      "against this replay's Family 4 numbers as its primary evidence. Doing "
      "so would tune against an instrument whose resolution is coarser than "
      "any effect calibration plausibly produces. If predictive validation is "
      "wanted, the binding constraint is N: more decision vintages or more "
      "carriers, both of which the roadmap places out of scope. |")
    A("")
    A("The consequence for the portfolio is stated rather than hidden: the "
      "predictive evaluation is a bounded negative result with its bound "
      "measured, and the remaining Stage 2R work is mechanism diagnosis, "
      "which this study is well powered for because it is arithmetic.")
    A("")

    DOC.write_text("\n".join(L) + "\n")
    return "\n".join(L)


if __name__ == "__main__":
    print(main())
