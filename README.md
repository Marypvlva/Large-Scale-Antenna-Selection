# Large-Scale Antenna Subset Selection

This repository contains a single-file Python implementation of a hybrid optimization algorithm for the MOTOR 2026 Industrial Challenge: Antenna Selection.

The task is to select an active subset of antennas from a complex-valued matrix under per-antenna power constraints. For a mask \(x\), the implementation rescales the selected rows by
\[
z = \frac{1}{\sqrt{\max_{n:x_n=1}\sum_l |v_{nl}|^2}}
\]
for \(P=1\), forms \(V_{\mathrm{eff}} = V^*W\), and focuses on the general determinant-based objective:

\[
U_G(x)=\det(V_{\mathrm{eff}}(x)V_{\mathrm{eff}}(x)^*+\sigma I)
\]

with \(\sigma = 1\).

## Method

The solver combines:

- weakest-antenna deletion baseline (H1),
- interference-based deletion baseline (H2),
- rank-one greedy deletion,
- vectorized one-swap local search,
- smart candidate selection using power, gradient proxy, and spectral alignment,
- forced local-optimum escape with one-swap repolishing,
- spectral balancing rescue,
- simulated annealing rescue,
- randomized perturbation refinement.

The method is designed for large antenna arrays with \(N \geq 1000\) and stream numbers \(L=2,\dots,10\).

The solver supports two modes:

- `fast`: stages H1/H2 local search first and runs the expensive greedy start only when the staged gain is below `CONDITIONAL_GREEDY_GAIN`;
- `quality`: always runs the greedy start and the full configured rescue stack.

## Results

The algorithm was tested on generated complex-valued matrices using the data generation procedure from the challenge statement. Timing is hardware- and NumPy-build-dependent.

| Setting | Mean Gain | Min Gain | Mean Time | Failures below 5% |
|---|---:|---:|---:|---:|
| N=1000 | 322.6% | 6.46% | 27.64s | 0 |
| N=2000 | 311.9% | 7.12% | 38.19s | 0 |

Across 108 tested cases in quality-style validation, the mean gain was 317.2%, the minimum gain was 6.46%, and no case fell below the 5% improvement target. The mean runtime was 32.91 seconds and the median runtime was 24.30 seconds in the latest local validation.

A representative 42-case fast-mode validation had no failures below 5%, minimum gain 6.46%, mean gain 336.8%, and mean runtime 16.35 seconds. Fast mode skipped the greedy start in 34 of 42 cases.

## Run

```bash
python antenna_v1.py
```

For a local environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python antenna_v1.py
```
