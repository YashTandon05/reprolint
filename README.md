# reprolint

[![PyPI version](https://img.shields.io/pypi/v/reprolint)](https://pypi.org/project/reprolint/)
[![Python versions](https://img.shields.io/pypi/pyversions/reprolint)](https://pypi.org/project/reprolint/)
[![License](https://img.shields.io/github/license/YashTandon05/reprolint)](https://github.com/YashTandon05/reprolint/blob/main/LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/YashTandon05/reprolint/ci.yml?label=CI)](https://github.com/YashTandon05/reprolint/actions)

A reproducibility auditor for machine learning repositories. `reprolint` statically analyzes a codebase using AST parsing and literature-backed checks to produce a scored reproducibility report — identifying missing seeds, unpinned dependencies, hardcoded paths, non-deterministic operations, untracked data, and missing environment captures.

Works as a CLI tool on local directories or public GitHub URLs, and integrates with GitHub Actions as a CI reproducibility gate.

## Installation

```bash
pip install reprolint
```

Or with uv:

```bash
uv tool install reprolint
```

## Usage

### Audit a local repository

```bash
reprolint /path/to/your/ml/project
```

### Audit a public GitHub repository

```bash
reprolint https://github.com/user/repo
```

### Use as a CI gate (fail if score is below threshold)

```bash
reprolint . --min-score 60 --fail
```

### Save the report to a file

```bash
reprolint . --output report.txt
```

## Example output

```
reprolint — auditing myproject/

┌──────────────────────────┬───────────────┬────────┬───────┐
│ Check                    │ Category      │ Result │ Score │
├──────────────────────────┼───────────────┼────────┼───────┤
│ Random seeds             │ Stochasticity │ PASS   │ 25/25 │
│ Dependency pinning       │ Environment   │ FAIL   │  7/20 │
│ Hardcoded paths          │ Code Quality  │ PASS   │ 15/15 │
│ Deterministic execution  │ Stochasticity │ FAIL   │  0/15 │
│ Data tracking            │ Data Integrity│ PASS   │ 15/15 │
│ Environment capture      │ Environment   │ FAIL   │  0/10 │
└──────────────────────────┴───────────────┴────────┴───────┘

Category breakdown
  Environment      ███░░░░░░░  7/30   (23%)
  Stochasticity    ████████░░  25/40  (63%)
  Data Integrity   ██████████  15/15  (100%)
  Code Quality     ██████████  15/15  (100%)

Overall score: 52/100
MODERATE — some reproducibility risk

Findings
  [HIGH] 'torch>=2.0' is loose (not exactly pinned).
        fix: Pin to an exact version (e.g. 'pkg==1.2.3') or commit a lock file.
  [HIGH] A deep-learning framework is used but deterministic mode is never enabled.
        fix: Call torch.use_deterministic_algorithms(True).
  [HIGH] No environment capture found.
        fix: Add a Dockerfile or environment.yml.
```

## Checks

Each check is grounded in peer-reviewed literature or established conference reproducibility checklists.

| Check | Category | Max Score | Reference |
|---|---|---|---|
| Random seeds | Stochasticity | 25 | AAAI-25 Reproducibility Checklist |
| Dependency pinning | Environment | 20 | AAAI-25 Checklist; Sculley et al. (2015) |
| Hardcoded paths | Code Quality | 15 | Sculley et al. (2015) |
| Deterministic execution | Stochasticity | 15 | PyTorch reproducibility docs |
| Data tracking | Data Integrity | 15 | Sculley et al. (2015); Raff (2019) |
| Environment capture | Environment | 10 | AAAI-25 Checklist; Raff (2019) |

Scores are aggregated into a weighted total out of 100. Category weights reflect findings from Raff (2019), which showed that not all reproducibility factors are equally predictive.

## GitHub Actions integration

Add this to your repository at `.github/workflows/reprolint.yml` to enforce a reproducibility threshold on every push and pull request:

```yaml
name: Reproducibility Audit

on:
  push:
    branches: ["main", "master"]
  pull_request:
    branches: ["main", "master"]

jobs:
  reprolint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install reprolint
        run: uv tool install reprolint

      - name: Run reproducibility audit
        run: reprolint . --min-score 60 --fail
```

## References

- AAAI-25 Reproducibility Checklist. Association for the Advancement of Artificial Intelligence, 2024. https://aaai.org/conference/aaai/aaai-25/aaai-25-reproducibility-checklist/
- Sculley, D. et al. "Hidden Technical Debt in Machine Learning Systems." NeurIPS 28, 2015.
- Raff, E. "A Step Toward Quantifying Independently Reproducible Machine Learning Research." NeurIPS 32, 2019. arXiv:1909.06674.
- Pineau, J. et al. "Improving Reproducibility in Machine Learning Research." JMLR 22(164), 2021. arXiv:2003.12206.
- PyTorch Reproducibility Documentation. https://pytorch.org/docs/stable/notes/randomness.html
