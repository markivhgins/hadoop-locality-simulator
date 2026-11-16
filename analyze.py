#!/usr/bin/env python3
"""Paired statistics, tables and figures from results/all_runs.csv.
usage: python3 scripts/analyze.py [results_dir]
All numbers in the paper come from the files this script writes (summary.csv, tables.md, figures/)."""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

R = sys.argv[1] if len(sys.argv) > 1 else "results"
FIG = f"{R}/figures"; os.makedirs(FIG, exist_ok=True)
df = pd.read_csv(f"{R}/all_runs.csv")
man = pd.read_csv(f"{R}/manifest.csv")

METRICS = ["makespan_s", "mean_turnaround_s", "mean_wait_s", "mean_remote_read_s", "remote_mib", "cross_rack_mib"]
POL = ["blind", "aware", "delay"]
COL = {"blind": "#8c8c8c", "aware": "#1f77b4", "delay": "#d95f02"}
LBL = {"blind": "Locality-blind", "aware": "Greedy locality-aware", "delay": "Delay (D=2 s)"}
COMPS = [("blind", "aware"), ("blind", "delay"), ("aware", "delay")]
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .3, "figure.dpi": 130})

def tci(x):
    x = np.asarray(x, float); n = len(x)
    return x.mean(), (stats.t.ppf(.975, n - 1) * x.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0)

# ---------- paired summary: base - alt, positive = alt is better (all metrics lower-is-better)
rows = []
for (exp, sid, param, value), g in df.groupby(["experiment", "setting_id", "param", "value"], sort=False):
    for m in METRICS:
        w = g.pivot(index="seed", columns="policy", values=m)
        for b, a in COMPS:
            d = (w[b] - w[a]).to_numpy(); mean, ci = tci(d)
            mb, ma = w[b].mean(), w[a].mean()
            rows.append(dict(experiment=exp, setting_id=sid, param=param, value=str(value),
                             comparison=f"{a}_vs_{b}", metric=m, mean_base=mb, mean_alt=ma,
                             mean_diff=mean, sd_diff=d.std(ddof=1), ci95=ci,
                             improvement_pct=100 * mean / mb if mb > 0 else np.nan,
                             ci95_pct=100 * ci / mb if mb > 0 else np.nan,
                             frac_seeds_better=float((d > 1e-9).mean()), n=len(d)))
S = pd.DataFrame(rows); S.to_csv(f"{R}/summary.csv", index=False)

def get(exp, comp, metric):
    t = S[(S.experiment == exp) & (S.comparison == comp) & (S.metric == metric)].copy()
    t["x"] = pd.to_numeric(t["value"], errors="coerce")
    return t.sort_values("x") if t["x"].notna().all() else t

def per_policy(exp, metric):
    d = df[df.experiment == exp].copy(); d["x"] = pd.to_numeric(d["value"], errors="coerce")
    out = {}
    for p in POL:
        g = d[d.policy == p].groupby("x")[metric].apply(lambda v: tci(v)).dropna()
        out[p] = (np.array(g.index), np.array([a for a, _ in g]), np.array([b for _, b in g]))
    return out

def save(name): plt.tight_layout(); plt.savefig(f"{FIG}/{name}.png", dpi=170); plt.close()

def bars(ax, setting, metric, scale=1.0):
    g = df[df.setting_id == setting]; xs = np.arange(len(POL))
    ms = [tci(g[g.policy == p][metric] * scale) for p in POL]
    ax.bar(xs, [m for m, _ in ms], yerr=[c for _, c in ms], color=[COL[p] for p in POL], capsize=4)
    ax.set_xticks(xs); ax.set_xticklabels(["blind", "aware", "delay"])

# Fig 1: completion time
fig, ax = plt.subplots(1, 3, figsize=(9, 3))
for a, (m, t) in zip(ax, [("makespan_s", "Makespan (s)"), ("mean_turnaround_s", "Mean job turnaround (s)"), ("mean_wait_s", "Mean task queueing wait (s)")]):
    bars(a, "E1_main", m); a.set_title(t)
save("fig1_completion_time")
# Fig 2: traffic
fig, ax = plt.subplots(1, 2, figsize=(6.5, 3))
for a, (m, t) in zip(ax, [("remote_mib", "Remote input traffic (MiB)"), ("cross_rack_mib", "Cross-rack traffic (MiB)")]):
    bars(a, "E1_main", m); a.set_title(t)
save("fig2_network_traffic")
# Fig 3: bandwidth sensitivity
pp_mk, pp_rm = per_policy("E2_bw", "makespan_s"), per_policy("E2_bw", "remote_mib")
fig, ax = plt.subplots(1, 3, figsize=(10, 3))
for p in POL:
    x, m, c = pp_mk[p]; ax[0].errorbar(x, m, c, color=COL[p], marker="o", ms=3, capsize=2, label=LBL[p])
    x, m, c = pp_rm[p]; ax[1].errorbar(x, m, c, color=COL[p], marker="o", ms=3, capsize=2, label=LBL[p])
for comp, p in [("aware_vs_blind", "aware"), ("delay_vs_blind", "delay")]:
    t = get("E2_bw", comp, "makespan_s"); ax[2].errorbar(t.x, t.improvement_pct, t.ci95_pct, color=COL[p], marker="o", ms=3, capsize=2, label=LBL[p] + " vs blind")
for a in ax: a.set_xscale("log"); a.set_xlabel("Per-flow cross-rack bandwidth (MiB/s)")
ax[0].set_ylabel("Makespan (s)"); ax[0].legend(fontsize=7)
ax[1].set_ylabel("Remote input (MiB)"); ax[2].set_ylabel("Makespan improvement (%)"); ax[2].legend(fontsize=7)
ax[0].set_title("Makespan"); ax[1].set_title("Remote traffic (bandwidth-independent)"); ax[2].set_title("Improvement vs blind")
save("fig3_bandwidth_sensitivity")
# Fig 4: locality distribution (task counts and byte-weighted agree because splits are uniform)
fig, ax = plt.subplots(1, 2, figsize=(8, 3))
for a, sid, title in [(ax[0], "E1_main", "Main cluster (16 workers, 4 racks)"), (ax[1], "E1_small", "Small baseline (8 workers, 2 racks)")]:
    g = df[df.setting_id == sid]; bottom = np.zeros(3)
    for col, lab, cc in [("node_local", "Node-local", "#2ca02c"), ("rack_local", "Rack-local", "#ffbf00"), ("off_rack", "Off-rack", "#d62728")]:
        v = np.array([g[g.policy == p][col].mean() / (g[g.policy == p][["node_local", "rack_local", "off_rack"]].sum(axis=1).mean()) * 100 for p in POL])
        a.bar(POL, v, bottom=bottom, color=cc, label=lab); bottom += v
    a.set_title(title); a.set_ylabel("Tasks (%)")
ax[0].legend(fontsize=7, loc="lower right")
save("fig4_locality_distribution")
# Fig 5: trade-off across every setting (relative to blind)
fig, ax = plt.subplots(figsize=(5, 4))
for comp, p in [("aware_vs_blind", "aware"), ("delay_vs_blind", "delay")]:
    x = S[(S.comparison == comp) & (S.metric == "remote_mib")].set_index("setting_id").improvement_pct
    y = S[(S.comparison == comp) & (S.metric == "makespan_s")].set_index("setting_id").improvement_pct
    j = pd.concat([x, y], axis=1, keys=["x", "y"]).dropna()
    ax.scatter(j.x, j.y, s=14, alpha=.7, color=COL[p], label=LBL[p])
ax.axhline(0, color="k", lw=.6); ax.axvline(0, color="k", lw=.6)
ax.set_xlabel("Remote-traffic reduction vs blind (%)"); ax.set_ylabel("Makespan improvement vs blind (%)"); ax.legend(fontsize=7)
ax.set_title("Traffic vs time trade-off (each point = one setting)")
save("fig5_tradeoff")
# Fig 6: load
fig, ax = plt.subplots(1, 3, figsize=(10, 3))
pp = per_policy("E3_load", "makespan_s")
for p in POL: x, m, c = pp[p]; ax[0].errorbar(x, m, c, color=COL[p], marker="o", ms=3, capsize=2, label=LBL[p])
ax[0].set_ylabel("Makespan (s)"); ax[0].legend(fontsize=7)
for comp, p in [("aware_vs_blind", "aware"), ("delay_vs_blind", "delay")]:
    for a, m, yl in [(ax[1], "makespan_s", "Makespan improvement (%)"), (ax[2], "remote_mib", "Remote-traffic reduction (%)")]:
        t = get("E3_load", comp, m); a.errorbar(t.x, t.improvement_pct, t.ci95_pct, color=COL[p], marker="o", ms=3, capsize=2, label=LBL[p]); a.set_ylabel(yl)
for a in ax: a.set_xlabel("Load (map tasks / map slots)"); a.set_xscale("log", base=2); a.set_xticks([1, 2, 4, 8]); a.set_xticklabels(["1", "2", "4", "8"])
save("fig6_load")
# Fig 7: replication x racks heatmaps (aware vs blind)
fig, ax = plt.subplots(1, 3, figsize=(10, 3))
for a, m, t, comp in [(ax[0], "remote_mib", "Remote-traffic reduction (%), aware", "aware_vs_blind"),
                      (ax[1], "makespan_s", "Makespan improvement (%), aware", "aware_vs_blind"),
                      (ax[2], "makespan_s", "Makespan improvement (%), delay", "delay_vs_blind")]:
    g = S[(S.experiment == "E4_grid") & (S.comparison == comp) & (S.metric == m)].copy()
    g["racks"] = g.value.str.split("x").str[0].astype(int); g["rep"] = g.value.str.split("x").str[1].astype(int)
    M = g.pivot(index="rep", columns="racks", values="improvement_pct")
    im = a.imshow(M.values, cmap="viridis", aspect="auto", origin="lower")
    a.set_xticks(range(len(M.columns))); a.set_xticklabels(M.columns); a.set_yticks(range(len(M.index))); a.set_yticklabels(M.index)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.values[i, j]; a.text(j, i, "n/a" if np.isnan(v) else f"{v:.1f}", ha="center", va="center", color="w", fontsize=8)
    a.set_xlabel("Racks"); a.set_ylabel("Replicas"); a.set_title(t, fontsize=8); a.grid(False); plt.colorbar(im, ax=a)
save("fig7_replication_racks")
# Fig 8: delay threshold
E5 = [("E5_main", "cross 25 MiB/s, 4x load"), ("E5_lowbw", "cross 10 MiB/s, 4x load"),
      ("E5_load1", "cross 25 MiB/s, 1x load"), ("E5_highbw", "cross 200 MiB/s, 4x load")]
fig, ax = plt.subplots(4, 3, figsize=(10, 10))
for r, (exp, lab) in enumerate(E5):
    d = df[df.experiment == exp].copy(); d["x"] = d.value.astype(float)
    for a, m, yl in [(ax[r, 0], "makespan_s", "Makespan (s)"), (ax[r, 1], "remote_mib", "Remote input (MiB)"), (ax[r, 2], "mean_wait_s", "Mean task wait (s)")]:
        g = d[d.policy == "delay"].groupby("x")[m].apply(tci)
        a.errorbar(g.index, [v[0] for v in g], [v[1] for v in g], color=COL["delay"], marker="o", ms=3, capsize=2, label="Delay(D)")
        for p in ["blind", "aware"]: a.axhline(d[d.policy == p][m].mean(), color=COL[p], ls="--", label=LBL[p])
        a.set_ylabel(yl); a.set_xlabel("Delay threshold D (s)"); a.set_title(f"{yl.split(' (')[0]} - {lab}", fontsize=8)
ax[0, 0].legend(fontsize=7)
save("fig8_delay_threshold")
# Fig 9: contention
fig, ax = plt.subplots(1, 3, figsize=(10, 3))
for a, exp, t in [(ax[0], "E6_shared", "Shared core link, per-flow cap 25"), (ax[1], "E6_shared_fast", "Shared core link, per-flow cap 100")]:
    pp = per_policy(exp, "makespan_s")
    for p in POL: x, m, c = pp[p]; a.errorbar(x, m, c, color=COL[p], marker="o", ms=3, capsize=2, label=LBL[p])
    a.set_xscale("log"); a.set_xlabel("Core-link capacity (MiB/s)"); a.set_ylabel("Makespan (s)"); a.set_title(t, fontsize=8)
ax[0].legend(fontsize=7)
for exp, ls in [("E6_shared", "-"), ("E6_shared_fast", ":")]:
    for comp, p in [("aware_vs_blind", "aware"), ("delay_vs_blind", "delay")]:
        t = get(exp, comp, "makespan_s"); ax[2].errorbar(t.x, t.improvement_pct, t.ci95_pct, color=COL[p], ls=ls, marker="o", ms=3, capsize=2, label=f"{p} ({'cap 25' if exp == 'E6_shared' else 'cap 100'})")
ax[2].set_xscale("log"); ax[2].set_xlabel("Core-link capacity (MiB/s)"); ax[2].set_ylabel("Makespan improvement vs blind (%)"); ax[2].legend(fontsize=7)
save("fig9_contention")
# Fig 10: block size, cluster size, arrival gap
fig, ax = plt.subplots(1, 3, figsize=(10, 3))
for a, exp, xl in [(ax[0], "E2_block", "Split size (MiB)"), (ax[1], "E4_workers", "Workers"), (ax[2], "E3_gap", "Job arrival gap (s)")]:
    for comp, p in [("aware_vs_blind", "aware"), ("delay_vs_blind", "delay")]:
        t = get(exp, comp, "makespan_s"); a.errorbar(t.x, t.improvement_pct, t.ci95_pct, color=COL[p], marker="o", ms=3, capsize=2, label=LBL[p])
    a.set_xlabel(xl); a.set_ylabel("Makespan improvement vs blind (%)")
ax[0].legend(fontsize=7)
save("fig10_block_workers_gap")

# ---------- markdown tables
def fmt(m, c, d=1): return f"{m:.{d}f} ± {c:.{d}f}"
def pct(r): return "n/a" if np.isnan(r.improvement_pct) else f"{r.improvement_pct:.1f}% ± {r.ci95_pct:.1f}"
def md(header, body):
    return "| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n" + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in body) + "\n"

out = []
for sid, title in [("E1_main", "Table 1. Baseline, main cluster (mean ± 95% CI over 50 seeds)"), ("E1_small", "Table 1b. Baseline, small cluster")]:
    g = df[df.setting_id == sid]; body = []
    for lab, m, d in [("Makespan (s)", "makespan_s", 1), ("Mean turnaround (s)", "mean_turnaround_s", 1), ("Mean task wait (s)", "mean_wait_s", 2),
                      ("Mean remote read (s)", "mean_remote_read_s", 2), ("Remote input (MiB)", "remote_mib", 0), ("Cross-rack (MiB)", "cross_rack_mib", 0),
                      ("Node-local tasks", "node_local", 1), ("Rack-local tasks", "rack_local", 1), ("Off-rack tasks", "off_rack", 1), ("Slot utilization", "utilization", 3)]:
        body.append([lab] + [fmt(*tci(g[g.policy == p][m].fillna(0)), d) for p in POL])
    out.append(f"**{title}**\n\n" + md(["Metric", "Blind", "Aware", "Delay (D=2)"], body))
for sid, title in [("E1_main", "Table 2. Paired differences, main cluster"), ("E1_small", "Table 2b. Paired differences, small cluster")]:
    body = []
    for comp in ["aware_vs_blind", "delay_vs_blind", "delay_vs_aware"]:
        for m in METRICS:
            r = S[(S.setting_id == sid) & (S.comparison == comp) & (S.metric == m)].iloc[0]
            body.append([comp.replace("_vs_", " vs "), m, f"{r.mean_base:.2f}", f"{r.mean_alt:.2f}", fmt(r.mean_diff, r.ci95, 2), pct(r), f"{100*r.frac_seeds_better:.0f}%"])
    out.append(f"**{title}** (diff = base − alt; positive favours the second policy)\n\n" + md(["Comparison", "Metric", "Base", "Alt", "Mean diff ± CI", "Improvement %", "Seeds better"], body))
def sweep(exp, name, label):
    vals = list(pd.unique(S[S.experiment == exp].value)); body = []
    for v in vals:
        g = df[(df.experiment == exp) & (df.value.astype(str) == v)]
        row = [v] + [f"{g[g.policy == p].makespan_s.mean():.1f}" for p in POL]
        for comp, m in [("aware_vs_blind", "makespan_s"), ("delay_vs_blind", "makespan_s"), ("aware_vs_blind", "remote_mib"), ("delay_vs_blind", "remote_mib")]:
            r = S[(S.experiment == exp) & (S.value == v) & (S.comparison == comp) & (S.metric == m)].iloc[0]; row.append(pct(r))
        body.append(row)
    return f"**{name}**\n\n" + md([label, "Makespan blind", "aware", "delay", "Aware: time impr.", "Delay: time impr.", "Aware: remote red.", "Delay: remote red."], body)
for exp, name, label in [("E2_bw", "Table 3. Cross-rack bandwidth sweep (MiB/s per flow)", "Cross BW"), ("E2_block", "Table 4. Split size", "MiB"),
                         ("E3_load", "Table 5. Load (tasks / slots)", "Load"), ("E3_gap", "Table 6. Job arrival gap", "Gap (s)"),
                         ("E4_replicas", "Table 7. Replica count", "Replicas"), ("E4_grid", "Table 8. Racks x replicas", "Racks x repl."),
                         ("E4_workers", "Table 9. Cluster size", "Workers"), ("E5_main", "Table 10. Delay threshold, cross 25 MiB/s", "D (s)"),
                         ("E5_lowbw", "Table 11. Delay threshold, cross 10 MiB/s", "D (s)"),
                         ("E5_load1", "Table 11b. Delay threshold, light load (1x slots)", "D (s)"),
                         ("E5_highbw", "Table 11c. Delay threshold, fast network (cross 200, rack 400 MiB/s)", "D (s)"), ("E6_shared", "Table 12. Shared core link, per-flow 25", "Core cap"),
                         ("E6_shared_fast", "Table 13. Shared core link, per-flow 100", "Core cap")]:
    out.append(sweep(exp, name, label))
# contention diagnostics
body = []
for exp in ["E6_shared", "E6_shared_fast"]:
    for v in pd.unique(S[S.experiment == exp].value):
        g = df[(df.experiment == exp) & (df.value.astype(str) == v)]
        body.append([exp, v] + [f"{g[g.policy == p].mean_remote_read_s.mean():.1f}" for p in POL] + [f"{g[g.policy == p].core_load.mean():.2f}" for p in POL])
out.append("**Table 14. Contention diagnostics: mean remote read time (s) and offered core load**\n\n" +
           md(["Exp", "Core cap", "read blind", "read aware", "read delay", "load blind", "load aware", "load delay"], body))
open(f"{R}/tables.md", "w").write("\n\n".join(out))
print("wrote summary.csv, tables.md, figures/ ->", R)
