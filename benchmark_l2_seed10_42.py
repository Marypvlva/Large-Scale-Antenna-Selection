import csv
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import antenna_v1 as antenna


N = 1000
L = 2
SEEDS = (10, 42)
OFF_RATIOS = (0.25, 0.5)
MATRICES_PER_SEED = 25
OUT_DIR = Path("ours_vs_hidden_L2_100_seed10_42_results")

METHOD_STYLES = {
    "h1_db": (":", "H1"),
    "h2_db": ("-.", "H2"),
    "hidden_db": ("--", "Hidden"),
    "ours_db": ("-", "Ours"),
}


def capacity_db(raw_score):
    return 10.0 * np.log10(max(raw_score, np.finfo(float).tiny))


def score(V, active):
    raw = antenna.raw_det_score(V, active, antenna.SIGMA)
    return raw, capacity_db(raw)


def empirical_curve(values):
    values = np.sort(np.asarray(values, dtype=float))
    cdf = np.arange(1, len(values) + 1, dtype=float) / len(values)
    return cdf, values


def run_case(V, off, seed, sample_id):
    n_active = int(round(N * (1.0 - off)))

    h1 = antenna.h1_weakest_deletion(V, n_active)
    h2 = antenna.h2_interference_deletion(V, n_active)
    hidden = antenna.h3_weakest_strongest_deletion(V, n_active)

    h1_raw, h1_db = score(V, h1)
    h2_raw, h2_db = score(V, h2)
    hidden_raw, hidden_db = score(V, hidden)

    result = antenna.solve_general(
        V,
        n_active,
        seed=seed,
        sigma=antenna.SIGMA,
        max_passes=antenna.MAX_PASSES,
        target_gain=antenna.TARGET_GAIN,
        early_stop_on_target=antenna.EARLY_STOP_ON_TARGET,
        solver_mode=antenna.SOLVER_MODE,
        conditional_greedy_gain=antenna.CONDITIONAL_GREEDY_GAIN,
        verbose=False,
    )
    ours_raw = result["ours_score"]
    ours_db = capacity_db(ours_raw)

    return {
        "N": N,
        "L": L,
        "off": off,
        "K_active": n_active,
        "seed": seed,
        "sample_id": sample_id,
        "h1_raw": h1_raw,
        "h2_raw": h2_raw,
        "hidden_raw": hidden_raw,
        "ours_raw": ours_raw,
        "h1_db": h1_db,
        "h2_db": h2_db,
        "hidden_db": hidden_db,
        "ours_db": ours_db,
        "ours_method": result["method"],
        "used_greedy": result["used_greedy"],
        "used_rescue": result["used_rescue"],
        "delta_db_ours_minus_hidden": ours_db - hidden_db,
    }


def generate_rows():
    rows = []
    case_id = 1
    for seed in SEEDS:
        np.random.seed(seed)
        for sample_id in range(1, MATRICES_PER_SEED + 1):
            V = antenna.generate_V(N, L)
            for off in OFF_RATIOS:
                row = {"case_id": case_id}
                row.update(run_case(V, off, seed, sample_id))
                rows.append(row)
                case_id += 1
    return rows


def write_csv(rows, path):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_ours_vs_hidden_for_slice(rows, seed, off, path):
    subset = [r for r in rows if r["seed"] == seed and r["off"] == off]
    n_active = int(round(N * (1.0 - off)))

    plt.figure(figsize=(8, 6))
    for label, key, style in [
        ("Hidden", "hidden_db", "--"),
        ("Ours", "ours_db", "-"),
    ]:
        x, y = empirical_curve([r[key] for r in subset])
        plt.plot(x, y, style, linewidth=2.5, label=label)

    plt.title(f"L=2, seed={seed}, off={off:.2f}, K={n_active}: Ours vs Hidden")
    plt.xlabel("Empirical CDF")
    plt.ylabel("Capacity objective, 10 log10(det) [dB]")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_all_methods_for_slice(rows, seed, off, path):
    subset = [r for r in rows if r["seed"] == seed and r["off"] == off]
    n_active = int(round(N * (1.0 - off)))

    plt.figure(figsize=(8, 6))
    for key, (style, label) in METHOD_STYLES.items():
        x, y = empirical_curve([r[key] for r in subset])
        plt.plot(x, y, style, linewidth=2.5, label=label)

    plt.title(f"L=2, seed={seed}, off={off:.2f}, K={n_active}: Ours vs Hidden, H1, H2")
    plt.xlabel("Empirical CDF")
    plt.ylabel("Capacity objective, 10 log10(det) [dB]")
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def method_summary(rows, key):
    values = np.array([r[key] for r in rows], dtype=float)
    return values.mean(), np.median(values), values.min(), values.max()


def write_report(rows, path, elapsed):
    delta = np.array([r["delta_db_ours_minus_hidden"] for r in rows], dtype=float)

    lines = [
        "# Ours vs Hidden, L=2, 100 Tests Using Seeds 10 and 42",
        "",
        "## Setup",
        "",
        f"- N: {N}",
        f"- L: {L}",
        f"- Tests: {len(rows)}",
        f"- Seeds: {list(SEEDS)}",
        f"- Switch-off ratios: {list(OFF_RATIOS)}",
        f"- Random matrices per seed: {MATRICES_PER_SEED}",
        "- Active K values: off=0.25 -> K=3N/4=750, off=0.5 -> K=N/2=500",
        "- Generator: exactly the appendix style. For each seed, `np.random.seed(seed)` is set once, then each call to `generate_V` draws a new random matrix from the fixed reproducible sequence.",
        "- Objective in dB: `10 log10(det(V_eff V_eff* + sigma I))`, `sigma=1`",
        "- Final proposed method: `solve_general` (`Ours`)",
        "- Comparator: hidden weak+strong heuristic",
        "",
        "The fixed seed makes the sequence reproducible, but the generated matrices are still random draws; the CSV contains no repeated benchmark rows.",
        "",
        "## Summary",
        "",
        "| Method | Mean dB | Median dB | Min dB | Max dB |",
        "|---|---:|---:|---:|---:|",
    ]

    for label, key in [
        ("H1", "h1_db"),
        ("H2", "h2_db"),
        ("Hidden weak+strong", "hidden_db"),
        ("Ours", "ours_db"),
    ]:
        mean, median, min_value, max_value = method_summary(rows, key)
        lines.append(f"| {label} | {mean:.3f} | {median:.3f} | {min_value:.3f} | {max_value:.3f} |")

    lines += [
        "",
        "## Ours minus Hidden",
        "",
        f"- Mean delta: {delta.mean():.3f} dB",
        f"- Median delta: {np.median(delta):.3f} dB",
        f"- Min delta: {delta.min():.6f} dB",
        f"- Max delta: {delta.max():.3f} dB",
        f"- Ours better than hidden: {int(np.sum(delta > 0.0))} / {len(rows)} tests",
        f"- Ours worse than hidden: {int(np.sum(delta < 0.0))} / {len(rows)} tests",
        "",
        "## Mean by Seed and Switch-off Ratio",
        "",
        "| seed | off | cases | Hidden mean dB | Ours mean dB | Mean delta dB |",
        "|---:|---:|---:|---:|---:|---:|",
    ]

    for seed in SEEDS:
        for off in OFF_RATIOS:
            subset = [r for r in rows if r["seed"] == seed and r["off"] == off]
            hidden = np.array([r["hidden_db"] for r in subset], dtype=float)
            ours = np.array([r["ours_db"] for r in subset], dtype=float)
            subset_delta = ours - hidden
            lines.append(
                f"| {seed} | {off:.2f} | {len(subset)} | "
                f"{hidden.mean():.3f} | {ours.mean():.3f} | {subset_delta.mean():.3f} |"
            )

    lines += [
        "",
        "## Best and Worst Individual Deltas",
        "",
        "| case | seed | sample | off | Hidden dB | Ours dB | Delta dB | Ours method |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    ranked = sorted(rows, key=lambda r: r["delta_db_ours_minus_hidden"])
    for row in ranked[:3] + ranked[-3:]:
        delta_text = (
            f"{row['delta_db_ours_minus_hidden']:.6f}"
            if abs(row["delta_db_ours_minus_hidden"]) < 0.001
            else f"{row['delta_db_ours_minus_hidden']:.3f}"
        )
        lines.append(
            f"| {row['case_id']} | {row['seed']} | {row['sample_id']} | {row['off']:.2f} | "
            f"{row['hidden_db']:.3f} | {row['ours_db']:.3f} | "
            f"{delta_text} | {row['ours_method']} |"
        )

    lines += [
        "",
        "## CDF",
        "",
        "### Ours vs Hidden",
        "",
        "![seed=10, off=0.25](ours_vs_hidden_L2_100_seed10_off025_cdf.png)",
        "",
        "![seed=10, off=0.50](ours_vs_hidden_L2_100_seed10_off050_cdf.png)",
        "",
        "![seed=42, off=0.25](ours_vs_hidden_L2_100_seed42_off025_cdf.png)",
        "",
        "![seed=42, off=0.50](ours_vs_hidden_L2_100_seed42_off050_cdf.png)",
        "",
        "### H1, H2, Hidden, Ours",
        "",
        "![seed=10, off=0.25](ours_hidden_h1_h2_L2_100_seed10_off025_cdf.png)",
        "",
        "![seed=10, off=0.50](ours_hidden_h1_h2_L2_100_seed10_off050_cdf.png)",
        "",
        "![seed=42, off=0.25](ours_hidden_h1_h2_L2_100_seed42_off025_cdf.png)",
        "",
        "![seed=42, off=0.50](ours_hidden_h1_h2_L2_100_seed42_off050_cdf.png)",
        "",
        "## Runtime",
        "",
        f"- Total script time: {elapsed:.2f} seconds",
    ]

    path.write_text("\n".join(lines) + "\n")


def main():
    t0 = time.time()
    OUT_DIR.mkdir(exist_ok=True)

    rows = generate_rows()

    main_csv = OUT_DIR / "ours_vs_hidden_L2_100_seed10_42.csv"
    write_csv(rows, main_csv)

    for seed in SEEDS:
        for off, off_tag in [(0.25, "off025"), (0.5, "off050")]:
            plot_ours_vs_hidden_for_slice(
                rows,
                seed,
                off,
                OUT_DIR / f"ours_vs_hidden_L2_100_seed{seed}_{off_tag}_cdf.png",
            )
            plot_all_methods_for_slice(
                rows,
                seed,
                off,
                OUT_DIR / f"ours_hidden_h1_h2_L2_100_seed{seed}_{off_tag}_cdf.png",
            )

    elapsed = time.time() - t0
    write_report(
        rows,
        OUT_DIR / "ours_vs_hidden_L2_100_seed10_42_report.md",
        elapsed,
    )

    print(f"saved results to {OUT_DIR}")
    print(f"elapsed {elapsed:.2f}s")


if __name__ == "__main__":
    main()
