# Security

Treat input files as untrusted and keep the documented size limits. This offline parser is not a security boundary; use an isolated low-privilege environment for hostile data. No network, registry publishing or external command execution is performed by the CLI. Do not post secrets or exploit payloads publicly; use GitHub private vulnerability reporting if enabled, otherwise privately contact the owner through a published channel without exposing sensitive data. Dependency checks and CI cover only their recorded scope, not absence of all vulnerabilities.
