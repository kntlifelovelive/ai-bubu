# Roadmap - ai-bubu

## Phase 1 (this phase) - Project foundation

Goal: repository layout, documentation, and safe defaults.
No model backend yet.

- [x] Directory structure created
- [x] README.md with quick start
- [x] ARCHITECTURE.md (layered design)
- [x] SECURITY.md (rules and threat model)
- [x] ROADMAP.md (this file)
- [x] DEVELOPMENT.md (build, test, run)
- [x] `.gitignore` (no secrets, no models, no caches)
- [x] Python skeleton: config, memory, security, server
- [x] Config template: `config/config.example.yaml`
- [x] Systemd service file (reference only)
- [x] Basic tests pass

## Phase 2 - Working inference engine

Goal: the server can actually run a small model.

- [ ] Choose backend (llama.cpp via Python binding, or
      a minimal GGUF interpreter)
- [ ] Load a 1B-3B GGUF model on CPU
- [ ] Streaming chat completions API
- [ ] Model cache and memory limits working
- [ ] Tests for model load/unload

Target hardware: 8 GB RAM, no GPU required.

## Phase 3 - System integration

Goal: run as a proper background service.

- [ ] Working systemd unit file
- [ ] Auto-restart on crash
- [ ] Log rotation
- [ ] Start/stop helper scripts
- [ ] Smoke tests via `curl`

## Phase 4 - Usability

Goal: easy for beginners to get running.

- [ ] One-command install script
- [ ] Docker image (optional)
- [ ] Example client scripts
- [ ] FAQ documentation

## Phase 5 - Performance and size

Goal: smaller memory and faster inference.

- [ ] Quantized model support (Q4_K_M, etc.)
- [ ] Better context window tuning
- [ ] Benchmarks on 4 GB / 8 GB machines
