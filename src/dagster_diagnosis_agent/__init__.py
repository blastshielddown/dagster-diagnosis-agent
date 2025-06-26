"""Compatibility shim – forwards imports to :pymod:`dagster_diagnostic_agent`."""

from importlib import import_module
import sys as _sys

_module = import_module("dagster_diagnostic_agent")

# Re-export everything so ``import dagster_diagnosis_agent as x`` continues to
# work during the transition period.
_sys.modules[__name__] = _module

