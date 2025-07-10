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
| `--manifestfile PATH`      | Path to `manifest.json` (default: auto-discovered)          |
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

## 📌 Examples

```bash
dbt-test-coverage \
  --package my_dbt_project \
  --unit-test-threshold 80 \
  --column-test-threshold 70 \
  --contract-threshold 50 \
  --show-column-details \
  --manifest-file tests/integration/jaffle_shop/target/manifest.json
```

```bash
dbt-test-coverage \
  --package my_dbt_project \
  --model-name 'fact_*' \
  --json-out coverage.json
```

```bash
dbt-test-coverage \
  --package my_dbt_project \
  --model-path 'models/gold/*'
```

```bash
dbt-test-coverage \
  --package my_dbt_project \
  --has-tags gold
```

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
