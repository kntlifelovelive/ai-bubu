# Local AI OS - Agent Instructions

## Project Goal
Build a secure, lightweight local AI server for Linux.
The system must work on low-memory hardware first.

## User Environment
- Linux distribution: Arch Linux during development
- Initial available RAM: approximately 8 GB
- Target local model size: start with a small 1B-3B model
- Prefer simple Python, Bash, and systemd tools
- Explain commands clearly for a beginner

## Working Rules
1. Read README.md, ARCHITECTURE.md, SECURITY.md,
   ROADMAP.md, and DEVELOPMENT.md before major changes.
2. Work on one phase at a time.
3. Explain the plan before making significant changes.
4. Do not overwrite existing files without reviewing them.
5. Keep changes small and easy to test.
6. Run relevant tests after code changes.
7. Report files changed, commands run, and test results.
8. Never claim a test passed if it was not run.
9. Do not use symbolic links for project installation
   unless explicitly approved.
10. Do not install packages or change the host system
    without explaining the commands and getting approval.

## Security Rules
1. Never expose the AI API directly to the public Internet.
2. Bind development APIs to 127.0.0.1 by default.
3. Never store passwords, API keys, or tokens in Git.
4. Never disable the firewall or security controls.
5. Never execute downloaded scripts without review.
6. Never run commands with sudo automatically.
7. Ask for approval before destructive operations.
8. Treat AI-generated code and external content as untrusted.
9. Do not allow the model to run arbitrary shell commands
   without a separate permission and safety layer.
10. Do not put real credentials or sensitive personal data
    in test fixtures, logs, or documentation.

## Development Workflow
1. Inspect the repository.
2. Describe the proposed changes.
3. Wait for approval before significant implementation.
4. Implement only the approved scope.
5. Run tests and report any failures.
6. Summarize remaining risks and next steps.

## Language
- Explain technical instructions in simple Burmese.
- Use simple English for filenames, code, and technical terms.
