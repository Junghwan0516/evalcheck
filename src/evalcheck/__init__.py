"""Local, reproducible text split audits. No network calls."""
from .core import AuditConfig, audit, propose_split
from .io import load_records
from .report import write_report

from ._version import VERSION as __version__
__all__ = ["AuditConfig", "audit", "propose_split", "load_records", "write_report"]
