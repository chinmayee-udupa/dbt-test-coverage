# 📊 dbt Test Coverage

**A CLI tool to analyze and report test coverage in dbt projects — at column, model, and contract levels.**

---

## 🚀 Features

- Column-level test coverage analysis
- Unit test coverage tracking
- Model contract enforcement verification
- Tag, path, and model-name filtering
- Rich terminal output with `rich` formatting
- Threshold checking with exit codes for CI
- JSON report export for downstream use
- Works on any dbt project with a `manifest.json`

---

## 📦 Installation

```bash
pip install "git+https://github.com/chinmayee-udupa/dbt-test-coverage.git"
```

Or with Poetry:

```bash
poetry add git+https://github.com/chinmayee-udupa/dbt-test-coverage.git
```

---

## 🧰 Usage

```bash
dbt-test-coverage --help
```

### 🔧 CLI Options

| Option                 | Description                                                 |
|------------------------|-------------------------------------------------------------|
| `--manifest-file PATH` | Path to `manifest.json` (default: auto-discovered if run from the dbt project root)          |
| `--package NAME`       | Filter by dbt package name                                  |
| `--unit-test-threshold`| Minimum % unit test coverage (exit code 1 if unmet)         |
| `--column-test-threshold`| Minimum % column test coverage                            |
| `--contract-threshold` | Minimum % model contract coverage                           |
| `--show-column-details`| Display column-level breakdowns per model                   |
| `--json-out PATH`      | Save coverage results to JSON                               |
| `--model-name PATTERN` | Glob pattern for model names (e.g. `'fact_*'`)              |
| `--model-path PATH`    | Filter by model file path                                   |
| `--has-tags TAG`       | Only include models with these tags                         |
| `--any-tag`            | Match models that have *any* of the specified tags          |

---

## 📌 Example Commands

### 1. Enforce Test Thresholds with Coverage Report
```bash
dbt-test-coverage \
  --package jaffle_shop \
  --unit-test-threshold 80 \
  --column-test-threshold 70 \
  --contract-threshold 50 \
  --show-column-details \
  --manifest-file tests/integration/jaffle_shop/target/manifest.json
```
![Demo](assets/example_1.gif)

### 2. Save Output to JSON
```bash
dbt-test-coverage \
  --package my_dbt_project \
  --model-name 'fact_*' \
  --json-out coverage.json
```

### 3. Filter Models by File Path
```bash
dbt-test-coverage \
  --package my_dbt_project \
  --model-path 'models/gold/*'
```

### 4. Filter by Tags
Match Models with a Single Tag:
```bash
dbt-test-coverage \
  --package my_dbt_project \
  --has-tags gold
```

Match Models with All of Multiple Tags (default behavior, uses Logical AND):
```bash
dbt-test-coverage \
  --package my_dbt_project \
  --has-tags "gold,silver"
```

Match any of multiple tags:
```bash
dbt-test-coverage \
  --package my_dbt_project \
  --has-tags "gold,silver" \
  --any-tag
```

---

## 🧪 Development

Clone the repo (with submodules):

```bash
git clone --recurse-submodules https://github.com/chinmayee-udupa/dbt-test-coverage.git
cd dbt-test-coverage
poetry install
```

To generate dbt artifacts:
```
poetry run dbt compile --profiles-dir tests/integration/profiles --project-dir tests/integration/jaffle_shop
```

Run tests:

```bash
poetry run pytest
```

Run CLI locally:

```bash
poetry run dbt-test-coverage --help
```

Build package:

```bash
poetry build
```

---

## 📁 Repo Layout

```
dbt-test-coverage/
├── src/dbt_test_coverage/
├── tests/integration/
├── pyproject.toml
└── README.md
```

---

## 🪪 License

[MIT License](https://opensource.org/licenses/MIT)
