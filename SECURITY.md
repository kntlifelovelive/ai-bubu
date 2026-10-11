# Security - ai-bubu

## Security Rules (always followed)

1. **No public exposure** - the API never listens on the public Internet.
   Default bind address is `127.0.0.1` (localhost only).
2. **No secrets in Git** - passwords, API keys, and tokens are never
   committed. Use `config/.env.example` as a template and add real
   values locally only.
3. **Firewall stays on** - no rule disables `ufw`, `firewalld`, or
   `iptables`.
4. **No automatic sudo** - the server runs as a normal user. The
   systemd service file is provided for reference only.
5. **No untrusted script execution** - downloaded files are never
   run automatically. They are reviewed first.
6. **No arbitrary shell access** - the model cannot run shell commands.
   Phase 1 has no shell execution at all. The security layer
   validates prompts, sizes, paths, and binding hosts; these are
   guards, not proofs of safety, and Phase 2 must enforce them.
7. **No sensitive data in logs** - prompts, keys, and tokens are not
   written to log files.
8. **Fail closed** - if validation fails or memory is low, the request
   is rejected, not executed.

## Default Security Settings

| Setting                | Default value      | Why                              |
|------------------------|--------------------|----------------------------------|
| Bind address           | `127.0.0.1`        | Not reachable from outside       |
| Port                   | `5001`             | Arbitrary private port           |
| Max request size       | 1 MB               | Prevents large-file DoS          |
| Max prompt length      | 4096 tokens        | Keeps memory bounded             |
| Max generation length  | 512 tokens         | Bounded output                   |
| Idle timeout           | 300 s              | Unload model to free RAM         |
| Max RAM usage          | 75% of total       | Leaves room for the OS           |

## Threat Model

| Threat                        | Mitigation                                  |
|-------------------------------|---------------------------------------------|
| Remote code execution         | Phase 1: no shell execution at all; the model
|                               | runs only as a validated stub. Phase 2 must invoke
|                               | the backend via subprocess without shell=True and
|                               | must never interpolate prompts into a command line.
| DoS by large requests         | Size and token limits enforced              |
| Memory exhaustion             | RAM cap + auto-unload of model              |
| Exposing to the internet      | Bound to localhost; user must opt-in         |
| Credential theft from Git     | Secrets excluded by `.gitignore`            |

## Configuration Files

- `config/config.example.yaml` - template with safe defaults
- `config/config.yaml` - your local copy (ignored by Git; add your model
  path here, not secrets)

Add your model path in `config/config.yaml`; do not commit real keys.


## Testing Security

Tests in `tests/` check:
- Invalid prompts are rejected
- Over-size requests return 413
- Non-localhost bind fails in tests
- No shell-like input is ever passed to the model
