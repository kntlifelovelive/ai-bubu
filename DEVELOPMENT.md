# Development - ai-bubu

This file explains how to build, test, and run the project.

## Prerequisites

- Arch Linux (or any modern Linux)
- Python 3.10 or newer
- Basic tools: `git`, `curl`

## Environment Setup

```bash
# Create a virtual environment (keeps your system clean)
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov mypy flake8
```

## Run the Server

```bash
# Make sure config exists
cp config/config.example.yaml config/config.yaml

# Start the development server
python -m src.server

# Check it is running
curl http://127.0.0.1:5001/health
```

The server binds to `127.0.0.1:5001` by default.
Do not change `host` to `0.0.0.0` unless you understand
the security consequences.

## Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=html

# Type check
mypy src/

# Lint
flake8 src/ tests/
```

Tests run in the virtual environment and do not touch
the host system.

## Adding a New Test

1. Write the test in `tests/`.
2. Run it with `pytest tests/test_xxx.py -v`.
3. Do not claim it passed until you see the green result.
4. Commit the test with the feature test.

## Config Files

- `config/config.example.yaml` - safe template (commit this)
- `config/config.yaml` - your local settings (NOT committed)

Edit `config/config.yaml` only. Never add real API keys or
passwords to tracked files.

## Git Workflow

1. Work on the feature branch (`git checkout -b feature-name`).
2. Commit often with clear messages.
3. Push before finishing (`git push -u origin <branch>`).
4. Report the files changed and test results.

## Reporting a Change

After each change, say:
- Files changed
- Commands run
- Test results

Do not hide failures.
