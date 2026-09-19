"""Context engineering package: Write, Select, Compress, Isolate."""

from universal_copilot.context.assembler import ContextAssembler
from universal_copilot.context.compression import ContextCompressor
from universal_copilot.context.pruning import prune_redundant_lines, truncate_to_token_budget
from universal_copilot.context.quarantine import quarantine_content, unquarantine_content

__all__ = [
    "ContextAssembler",
    "ContextCompressor",
    "prune_redundant_lines",
    "truncate_to_token_budget",
    "quarantine_content",
    "unquarantine_content",
]
