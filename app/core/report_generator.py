from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict

from jinja2 import Template

from app.core.models import AnalysisResult, LogEvent


HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Atlassian Log Analyzer Report</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #172b4d; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border-bottom: 1px solid #dfe1e6; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #f4f5f7; }
    .summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 24px; }
    .metric { border: 1px solid #dfe1e6; border-radius: 6px; padding: 12px; }
    .label { color: #5e6c84; font-size: 12px; }
    .value { font-size: 20px; font-weight: 600; }
  </style>
</head>
<body>
  <h1>Atlassian Log Analyzer Report</h1>
  <section class="summary">
    {% for label, value in summary_items %}
    <div class="metric"><div class="label">{{ label }}</div><div class="value">{{ value }}</div></div>
    {% endfor %}
  </section>
  <table>
    <thead><tr><th>Time</th><th>Level</th><th>Category</th><th>File</th><th>Message</th></tr></thead>
    <tbody>
    {% for event in events %}
      <tr><td>{{ event.time }}</td><td>{{ event.level }}</td><td>{{ event.category }}</td><td>{{ event.file }}</td><td>{{ event.message }}</td></tr>
    {% endfor %}
    </tbody>
  </table>
</body>
</html>"""
)


class ReportGenerator:
    def render(self, result: AnalysisResult, report_format: str) -> str:
        if report_format == "json":
            return self.to_json(result)
        if report_format == "csv":
            return self.to_csv(result.events)
        if report_format == "markdown":
            return self.to_markdown(result)
        if report_format == "html":
            return self.to_html(result)
        raise ValueError(f"Unsupported report format: {report_format}")

    def to_json(self, result: AnalysisResult) -> str:
        payload = {
            "summary": asdict(result.summary),
            "events": [asdict_without_parsed_time(event) for event in result.events],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def to_csv(self, events: list[LogEvent]) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["time", "level", "category", "file", "message"])
        writer.writeheader()
        for event in events:
            writer.writerow(
                {
                    "time": event.time,
                    "level": event.level,
                    "category": event.category,
                    "file": event.file,
                    "message": event.message,
                }
            )
        return buffer.getvalue()

    def to_markdown(self, result: AnalysisResult) -> str:
        summary = result.summary
        lines = [
            "# Atlassian Log Analyzer Report",
            "",
            f"- Product: {summary.product}",
            f"- Files analyzed: {summary.file_count}",
            f"- Total ERROR: {summary.total_errors}",
            f"- Total WARN: {summary.total_warnings}",
            f"- First error time: {summary.first_error_time or 'N/A'}",
            f"- Last error time: {summary.last_error_time or 'N/A'}",
            f"- Top category: {summary.top_category}",
            "",
            "| Time | Level | Category | File | Message |",
            "| --- | --- | --- | --- | --- |",
        ]
        for event in result.events:
            lines.append(
                f"| {escape_md(event.time)} | {escape_md(event.level)} | {escape_md(event.category)} | "
                f"{escape_md(event.file)} | {escape_md(event.message)} |"
            )
        return "\n".join(lines)

    def to_html(self, result: AnalysisResult) -> str:
        summary = result.summary
        summary_items = [
            ("Product", summary.product),
            ("Files analyzed", summary.file_count),
            ("Total ERROR", summary.total_errors),
            ("Total WARN", summary.total_warnings),
            ("First error time", summary.first_error_time or "N/A"),
            ("Last error time", summary.last_error_time or "N/A"),
            ("Top category", summary.top_category),
        ]
        return HTML_TEMPLATE.render(summary_items=summary_items, events=result.events)


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def asdict_without_parsed_time(event: LogEvent) -> dict[str, str]:
    return {
        "time": event.time,
        "level": event.level,
        "category": event.category,
        "file": event.file,
        "message": event.message,
        "raw": event.raw,
    }
