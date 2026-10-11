# ai-bubu

**ai-bubu** is a secure, lightweight local AI server for Linux.
It runs a small language model (1B-3B parameters) on your own computer.
No data leaves your machine. No internet access needed.

The system is built to work on low-memory hardware first
(about 8 GB RAM).

## What It Does

- Exposes a simple chat API on `127.0.0.1` (localhost only; binding to
  any other host fails at startup)
- Manages model memory so it does not overload the computer
- Phase 2: loads a small CPU model (1B-3B) and runs inference
- Phase 2: auto-unloads the model when idle

The model loader and inference engine are skeletons in Phase 1; they
are stubs that validate input but do not read or execute any model.


## Quick Start

```bash
# 1. Set up a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the config file (add your model path here)
cp config/config.example.yaml config/config.yaml

# 4. Start the server (development mode)
python -m src.server

# 5. Test the health check
curl http://127.0.0.1:5001/health
```

## Directory Layout

```
.
├── src/            # Python source code
│   ├── server.py   # HTTP server
│   ├── model.py    # Model loading and memory manager
│   ├── config.py   # Configuration loader
│   ├── security.py # Input validation and permissions
│   └── memory.py   # Memory usage monitoring
├── config/         # Configuration files
├── scripts/        # Helper scripts
├── tests/          # Automated tests
├── systemd/        # Systemd unit file
└── AGENTS.md       # Agent workflow rules
```

## Security

- The API binds to `127.0.0.1` by default (not reachable from outside)
- No passwords or API keys are stored in Git
- Firewall stays enabled
- User input is validated before any processing

## Development Workflow

See `DEVELOPMENT.md` for build, test, and run instructions.
See `ROADMAP.md` for the planned phases.
