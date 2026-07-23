# Development Guide

This guide explains how to set up, test, and extend the WC26 Transfer Intelligence Python core.

## Requirements

- Python 3.12 or newer
- Git
- Local processed datasets for real-data integration tests

## Local Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/MelihSiskular/world-cup-2026.git
cd world-cup-2026
```

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Upgrade pip and install the project with development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Confirm that the package and console command are available:

```bash
python -c "import wc26; print(wc26.__version__)"
wc26-transfer --help
```

## Running Transfer Intelligence

The recommended command is:

```bash
wc26-transfer \
  --player "Michael Olise" \
  --top-n 5
```

The legacy module command remains available for backward compatibility:

```bash
python -m src.transfer_intelligence.find_replacements \
  --player "Michael Olise" \
  --top-n 5
```

Both commands execute the same application entrypoint and analysis service.

## Python Core Architecture

The main application flow is:

```text
Command-line interface
        ↓
entrypoint.py
        ↓
TransferAnalysisRequest
        ↓
run_transfer_analysis()
        ↓
TransferAnalysisResult
        ├── console reporting adapter
        └── CSV exporting adapter
```
The analysis service is intentionally side-effect free. It does not print to
the terminal, create directories, or write CSV files.

`run_transfer_analysis()` accepts analytical inputs and returns a structured,
JSON-compatible `TransferAnalysisResult`.

Presentation and output concerns are handled by separate adapters:

- `print_transfer_report()` renders the console report.
- `export_transfer_csv()` writes recommendation files.
- `TransferAnalysisResult.to_dict()` produces a JSON-compatible response.

This separation allows the same application service to be reused by the CLI,
a FastAPI backend, scheduled pipelines, web clients, and mobile applications.
### Module Responsibilities

| Module | Responsibility |
|---|---|
| `config.py` | Paths, thresholds, mode configuration, and scoring weights |
| `utils.py` | Shared formatting, normalization, and conversion utilities |
| `datasets.py` | Loading and validating analytical datasets |
| `matching.py` | Resolving players and attaching similarity data |
| `candidates.py` | Preparing the transfer candidate population |
| `scoring.py` | Transfer scoring rules and suitability calculations |
| `recommendations.py` | Mode filtering, ranking, and result generation |
| `explanations.py` | Recommendation labels and data-driven explanations |
| `reporting.py` | Rendering structured analysis results as console reports || `cli.py` | Command-line argument definitions |
| `entrypoint.py` | Mapping CLI input to the application request |
| `service.py` | Running the analysis workflow and returning a structured result || `models.py` | Backend-ready request, result, mode, and recommendation contracts |
| `exporting.py` | CSV output generation from structured analysis results |

The package-level public API is intentionally small:

```python
from wc26.analytics.transfer_intelligence import (
    TransferAnalysisRequest,
    run_transfer_analysis,
)
```

Internal modules may change as the project evolves. Code outside the package should prefer the public API.

## Quality Checks

Run Ruff linting:

```bash
python -m ruff check \
  src/transfer_intelligence/find_replacements.py \
  src/wc26 \
  tests
```

Check formatting:

```bash
python -m ruff format --check \
  src/transfer_intelligence/find_replacements.py \
  src/wc26 \
  tests
```

Run strict type checking:

```bash
python -m mypy src/wc26
```

Run portable tests:

```bash
python -m pytest -m "not integration"
```

Run tests with branch coverage:

```bash
python -m pytest \
  -m "not integration" \
  --cov=wc26 \
  --cov-branch \
  --cov-report=term-missing
```

The current minimum coverage baseline is 65%.

The baseline is intended to prevent untested code from gradually reducing the quality of the Python core. It may be increased as backend-ready contracts and additional service tests are introduced.

## Integration Tests

Real-data integration tests require the processed World Cup datasets to exist locally.

Run them explicitly with:

```bash
WC26_RUN_INTEGRATION=1 \
python -m pytest -m integration -v
```

These tests are excluded from GitHub Actions because the required processed datasets are not guaranteed to exist on the GitHub runner.

## Test Organization

```text
tests/
├── unit/
│   ├── test_package.py
│   ├── test_paths.py
│   └── transfer_intelligence/
│       ├── test_candidates.py
│       ├── test_cli.py
│       ├── test_datasets.py
│       ├── test_entrypoint.py
│       ├── test_legacy_behavior.py
│       ├── test_matching.py
│       ├── test_module_boundaries.py
│       ├── test_public_api.py
│       ├── test_recommendations.py
│       ├── test_reporting.py
│       ├── test_scoring.py
│       └── test_service.py
└── integration/
    └── transfer_intelligence/
        └── test_cli_smoke.py
```

### Unit Tests

Unit tests verify individual modules and business rules using small, deterministic inputs.

### Characterization Tests

Characterization tests preserve important behavior inherited from the original transfer intelligence script.

They allow internal refactoring without unintentionally changing existing recommendation behavior.

### Integration Tests

Integration tests exercise the complete workflow using real processed datasets and verify that the CLI produces valid recommendation outputs.

## Adding a New Feature

When adding or changing transfer intelligence behavior:

1. Create a focused branch from the latest `main`.
2. Add or update tests before changing critical scoring behavior.
3. Keep business rules out of CLI and reporting modules.
4. Keep pandas objects inside the analytics layer.
5. Prefer the package public API over legacy imports.
6. Run all local quality checks.
7. Review the coverage result.
8. Open a Pull Request and wait for the Python Quality workflow.

Example branch:

```bash
git switch main
git pull origin main
git switch -c feat/example-feature
```

## Legacy Compatibility

The file:

```text
src/transfer_intelligence/find_replacements.py
```

is a compatibility wrapper for existing commands, imports, and tests.

Do not remove its explicit re-exports as part of an unrelated refactor. Removing them should be treated as an intentional breaking change.

New application behavior should be implemented under:

```text
src/wc26/analytics/transfer_intelligence/
```

## Commit Style

Prefer focused commits with imperative messages:

```text
feat: add transfer intelligence console command
fix: handle missing heatmap profile
refactor: separate recommendation exporters
test: cover value recommendation filtering
docs: document Python core development workflow
ci: add Python quality workflow
```

Avoid combining unrelated refactoring, feature, and documentation changes in one commit.

## Pull Request Checklist

Before opening a Pull Request:

```bash
python -m ruff check \
  src/transfer_intelligence/find_replacements.py \
  src/wc26 \
  tests

python -m ruff format --check \
  src/transfer_intelligence/find_replacements.py \
  src/wc26 \
  tests

python -m mypy src/wc26

python -m pytest \
  -m "not integration" \
  --cov=wc26 \
  --cov-branch \
  --cov-report=term-missing

git diff --check
```

Also verify:

- New behavior has tests.
- Existing behavior remains compatible unless a breaking change is intended.
- Public API changes are documented.
- Generated datasets and local output files are not committed accidentally.
- The GitHub Actions Python Quality workflow passes.
