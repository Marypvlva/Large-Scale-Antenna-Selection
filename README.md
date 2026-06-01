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

## Final Benchmark

Benchmark setup:

- `N = 1000`
- `L = 2`
- seeds `10` and `42`
- 25 random matrices per seed
- switch-off ratios `0.25` and `0.5`
- 100 total tests

The seed is fixed once per seed with `np.random.seed(seed)`, then each generator
call draws a new random matrix from that fixed reproducible sequence.

Summary in dB:

| Method | Mean dB | Median dB | Min dB | Max dB |
|---|---:|---:|---:|---:|
| H1 | 77.493 | 77.593 | 70.757 | 83.444 |
| H2 | 76.670 | 76.706 | 69.687 | 82.542 |
| Ours | 80.241 | 80.575 | 75.506 | 84.319 |

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

## Reproduce Benchmark

The final `L=2` task slice can be reproduced with:

```bash
.venv/bin/python benchmark_l2_seed10_42.py
```

This script sets `np.random.seed(seed)` once per seed and then generates a
sequence of new random matrices, so the 100 benchmark rows are reproducible but
not repeated copies.
