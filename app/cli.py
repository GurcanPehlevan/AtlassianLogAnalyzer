from __future__ import annotations

import argparse
from pathlib import Path

from app.core.analyzer import Analyzer
from app.core.report_generator import ReportGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Atlassian log files locally.")
    parser.add_argument("paths", nargs="+", help="Files, folders, .gz files, or .zip archives to analyze.")
    parser.add_argument(
        "--rules",
        default="rules",
        help="Rules directory containing YAML files. Defaults to ./rules.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv", "markdown", "html"),
        default="json",
        help="Report format.",
    )
    parser.add_argument("--output", "-o", help="Output report path. Prints to stdout when omitted.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    analyzer = Analyzer(rules_dir=Path(args.rules))
    result = analyzer.analyze_paths([Path(path) for path in args.paths])
    rendered = ReportGenerator().render(result, args.format)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
