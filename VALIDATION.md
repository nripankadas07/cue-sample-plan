# Validation

Acceptance: Prove exact contiguous frame coverage, explicit INDEX00 gaps and leading findings, stereo byte offsets, source-byte preservation, RIFF validation, and rejection of unrepresentable frame boundaries and unsafe paths.

The behavior suite has 20 test methods, including malformed-input contracts. CI runs unit tests, compilation, wheel build and new-environment installed-command checks on Linux/Python 3.10, 3.12 and 3.14. A configured workflow does not prove success; inspect current Actions results. Preparation receipts are recorded in PREPARATION.json after execution. All possible inputs, production workloads and Windows/macOS are not certified. No performance benchmark was conducted.
