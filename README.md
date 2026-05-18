# Large-Scale Antenna Subset Selection

This repository contains a single-file Python implementation of a hybrid optimization algorithm for the MOTOR 2026 Industrial Challenge: Antenna Selection.

The task is to select an active subset of antennas from a complex-valued matrix under per-antenna power constraints. The implementation focuses on the general determinant-based objective:

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
- spectral balancing rescue,
- simulated annealing rescue,
- randomized perturbation refinement.

The method is designed for large antenna arrays with \(N \geq 1000\) and stream numbers \(L=2,\dots,10\).

## Results

The algorithm was tested on generated complex-valued matrices using the data generation procedure from the challenge statement.

| Setting | Mean Gain | Min Gain | Mean Time | Failures below 5% |
|---|---:|---:|---:|---:|
| N=1000 | 322.6% | 6.46% | 6.91s | 0 |
| N=2000 | 311.9% | 7.12% | 10.73s | 0 |

Across 108 tested cases, the mean runtime was 8.82 seconds and the median runtime was 7.94 seconds.

## Run

```bash
python antenna_selection.py
