from __future__ import annotations

import re
from datetime import datetime

from app.core.categorizer import Categorizer
from app.core.models import LogEvent, LogSource


EVENT_RE = re.compile(
    r"(?P<time>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[,.]\d{3})?|"
    r"\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d{3})?)"
    r".{0,180}?\b(?P<level>ERROR|WARN)\b"
    r"(?P<message>.*)",
    re.IGNORECASE,
)

LOOSE_EVENT_RE = re.compile(r"\b(?P<level>ERROR|WARN)\b(?P<message>.*)", re.IGNORECASE)
STACK_CONTINUATION_RE = re.compile(
    r"^\s*(at\s+[\w.$]+\(.*\)|\.\.\. \d+ more|Caused by:|Suppressed:|"
    r"[\w.$]+(?:Exception|Error):|org\.|com\.|java\.|javax\.|sun\.|net\.|io\.)"
)

TIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S,%f",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d-%b-%Y %H:%M:%S.%f",
    "%d-%b-%Y %H:%M:%S",
)


class LogParser:
    def __init__(self, categorizer: Categorizer) -> None:
        self.categorizer = categorizer

    def parse_source(self, source: LogSource) -> list[LogEvent]:
        events: list[LogEvent] = []
        current: dict[str, object] | None = None

        for line in source.content.splitlines():
            match = EVENT_RE.search(line) or LOOSE_EVENT_RE.search(line)
            if match:
                if current:
                    events.append(self._build_event(current, source))
                current = {
                    "time": match.groupdict().get("time") or "",
                    "level": match.group("level").upper(),
                    "lines": [line],
                    "message": match.group("message").strip() or line.strip(),
                }
                continue

            if current and self._belongs_to_current_event(line):
                current["lines"].append(line)  # type: ignore[index, union-attr]
            elif current:
                events.append(self._build_event(current, source))
                current = None

        if current:
            events.append(self._build_event(current, source))

        return events

    def _belongs_to_current_event(self, line: str) -> bool:
        return bool(STACK_CONTINUATION_RE.search(line)) or line.strip() == ""

    def _build_event(self, data: dict[str, object], source: LogSource) -> LogEvent:
        lines = data["lines"]
        raw = "\n".join(lines) if isinstance(lines, list) else str(lines)
        message = str(data.get("message") or raw).strip()
        category = self.categorizer.categorize(raw)
        time_value = str(data.get("time") or "")
        return LogEvent(
            time=time_value,
            parsed_time=parse_time(time_value),
            level=str(data.get("level") or "").upper(),
            category=category,
            file=source.display_path,
            message=message,
            raw=raw,
        )


def parse_time(value: str) -> datetime | None:
    normalized = value.strip()
    if not normalized:
        return None
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            pass
    return None
