from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class CategoryRule:
    category: str
    patterns: list[re.Pattern[str]]


class Categorizer:
    def __init__(self, rules_dir: Path | None = None) -> None:
        self.rules_dir = rules_dir or Path("rules")
        self.rules = self._load_rules()

    def categorize(self, text: str) -> str:
        for rule in self.rules:
            for pattern in rule.patterns:
                if pattern.search(text):
                    return rule.category
        return "Unknown"

    def _load_rules(self) -> list[CategoryRule]:
        rules: list[CategoryRule] = []
        if not self.rules_dir.exists():
            return rules

        for path in sorted(self.rules_dir.glob("*.yml")) + sorted(self.rules_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for item in data.get("rules", []):
                category = str(item.get("category", "Unknown"))
                raw_patterns = item.get("patterns", [])
                patterns = [re.compile(str(pattern), re.IGNORECASE) for pattern in raw_patterns]
                rules.append(CategoryRule(category=category, patterns=patterns))
        return rules
