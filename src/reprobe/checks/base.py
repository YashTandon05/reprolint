from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Category(str, Enum):
    ENVIRONMENT = "Environment"
    STOCHASTICITY = "Stochasticity"
    DATA_INTEGRITY = "Data Integrity"
    CODE_QUALITY = "Code Quality"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Finding:
    """A single issue (or note) discovered by a check."""
    message: str
    severity: Severity = Severity.MEDIUM
    file: str | None = None
    line: int | None = None
    fix: str | None = None


@dataclass
class CheckResult:
    """The uniform result every check returns."""
    name: str
    category: Category
    passed: bool
    score: float
    max_score: float
    findings: list[Finding] = field(default_factory=list)
    reference: str = ""