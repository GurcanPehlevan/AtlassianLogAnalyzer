from __future__ import annotations

from collections import Counter

from app.core.models import LogSource


PRODUCT_PATTERNS = {
    "Bitbucket": ("bitbucket", "stash", "com.atlassian.bitbucket"),
    "Jira": ("jira", "atlassian-jira", "com.atlassian.jira"),
    "Confluence": ("confluence", "com.atlassian.confluence"),
    "Bamboo": ("bamboo", "com.atlassian.bamboo"),
    "Crowd": ("crowd", "com.atlassian.crowd"),
}


class ProductDetector:
    def detect(self, sources: list[LogSource]) -> str:
        scores: Counter[str] = Counter()
        for source in sources:
            haystack = f"{source.display_path}\n{source.content[:20000]}".lower()
            for product, patterns in PRODUCT_PATTERNS.items():
                for pattern in patterns:
                    scores[product] += haystack.count(pattern)

        if not scores:
            return "Unknown"

        product, score = scores.most_common(1)[0]
        return product if score > 0 else "Unknown"
