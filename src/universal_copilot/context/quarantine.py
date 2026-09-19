"""Untrusted content quarantine and isolation layer."""
from __future__ import annotations

import html
import re
from typing import Tuple


def quarantine_content(raw_text: str, source_tag: str = "document") -> str:
    """Wraps untrusted user or document input in isolated XML boundary tags.

    Prevents indirect prompt injection by demarcating data from system instructions.
    """
    if not raw_text:
        return f"<{source_tag} empty='true'></{source_tag}>"

    # Escape raw markdown/html boundary injections
    sanitized = raw_text.replace("</untrusted_content>", "&lt;/untrusted_content&gt;")
    sanitized = sanitized.replace("<untrusted_content>", "&lt;untrusted_content&gt;")

    return (
        f"<untrusted_content source='{source_tag}'>\n"
        f"{sanitized}\n"
        f"</untrusted_content>"
    )


def unquarantine_content(quarantined_text: str) -> str:
    """Strips quarantine boundary tags and restores raw text."""
    pattern = r"<untrusted_content(?:\s+source='[^']*')?>\n?(.*?)\n?</untrusted_content>"
    match = re.search(pattern, quarantined_text, re.DOTALL)
    if match:
        content = match.group(1)
        content = content.replace("&lt;/untrusted_content&gt;", "</untrusted_content>")
        content = content.replace("&lt;untrusted_content&gt;", "<untrusted_content>")
        return content
    return quarantined_text
