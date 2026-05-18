from __future__ import annotations

from collections import Counter
from pathlib import Path

from app.core.archive_reader import ArchiveReader
from app.core.categorizer import Categorizer
from app.core.models import AnalysisResult, AnalysisSummary, LogEvent
from app.core.parser import LogParser
from app.core.product_detector import ProductDetector


class Analyzer:
    def __init__(self, rules_dir: Path | None = None) -> None:
        self.archive_reader = ArchiveReader()
        self.categorizer = Categorizer(rules_dir=rules_dir)
        self.parser = LogParser(self.categorizer)
        self.product_detector = ProductDetector()

    def analyze_paths(self, paths: list[Path]) -> AnalysisResult:
        sources = self.archive_reader.read_paths(paths)
        events: list[LogEvent] = []

        for source in sources:
            events.extend(self.parser.parse_source(source))

        summary = self._build_summary(events, len(sources), self.product_detector.detect(sources))
        return AnalysisResult(summary=summary, events=events, sources=paths)

    def _build_summary(self, events: list[LogEvent], file_count: int, product: str) -> AnalysisSummary:
        errors = [event for event in events if event.level == "ERROR"]
        warnings = [event for event in events if event.level == "WARN"]
        dated_errors = sorted((event for event in errors if event.parsed_time), key=lambda event: event.parsed_time)
        categories = Counter(event.category for event in events)

        return AnalysisSummary(
            product=product,
            file_count=file_count,
            total_errors=len(errors),
            total_warnings=len(warnings),
            first_error_time=dated_errors[0].time if dated_errors else "",
            last_error_time=dated_errors[-1].time if dated_errors else "",
            top_category=categories.most_common(1)[0][0] if categories else "Unknown",
        )
