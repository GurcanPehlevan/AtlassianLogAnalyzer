from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class LogSource:
    name: str
    display_path: str
    content: str


@dataclass(slots=True)
class LogEvent:
    time: str
    parsed_time: datetime | None
    level: str
    category: str
    log_type: str
    file: str
    message: str
    raw: str


@dataclass(slots=True)
class AnalysisSummary:
    product: str = "Unknown"
    file_count: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    first_error_time: str = ""
    last_error_time: str = ""
    top_category: str = "Unknown"


@dataclass(slots=True)
class AnalysisResult:
    summary: AnalysisSummary
    events: list[LogEvent] = field(default_factory=list)
    sources: list[Path] = field(default_factory=list)
