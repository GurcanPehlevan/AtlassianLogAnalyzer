from __future__ import annotations

from pathlib import Path


def infer_log_type(display_path: str) -> str:
    value = display_path.lower()
    name = Path(display_path.split("!/", 1)[-1]).name.lower()

    if any(token in value for token in ("mail", "smtp", "outgoing_mail", "outgoing-mail", "outgoingmail")):
        return "Mail"
    if any(token in name for token in ("access", "request")):
        return "Access"
    if "audit" in value:
        return "Audit"
    if any(token in name for token in ("gc", "garbage")):
        return "GC"
    if any(token in value for token in ("thread", "threaddump", "thread-dump")):
        return "Thread Dump"
    if any(
        token in value
        for token in ("application", "atlassian-jira", "jira", "atlassian-confluence", "confluence", "bitbucket")
    ):
        return "Application"
    if any(token in name for token in ("catalina", "localhost")):
        return "Application"
    return "Other"
