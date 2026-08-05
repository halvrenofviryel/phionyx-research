# Shadow stub: mypy resolves numpy HERE (via mypy_path) and never parses the
# real numpy stubs. Reason (2026-08-05): numpy >= 2.5 ships PEP 695 `type`
# statements in its .pyi; with our python_version=3.10 contract, mypy fails at
# PARSE time inside numpy's own files on the 3.12/3.13 CI runners — and
# follow_imports="skip" does not prevent parsing, so it could not cure this
# (measured: CI run on 528b09f). numpy is intentionally untyped (Any) for this
# codebase; retargeting per-interpreter is a recorded future decision.
from typing import Any

def __getattr__(name: str) -> Any: ...
