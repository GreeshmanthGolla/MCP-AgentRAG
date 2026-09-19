"""Configuration manager for Universal Document Copilot."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Determine project root (Agentic-RAG directory)
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


class LLMConfig(BaseModel):
    mode: str = Field(default_factory=lambda: os.getenv("LLM_MODE", "offline"))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.6-pro-latest"))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    temperature: float = 0.1
    max_output_tokens: int = 2048
    cost_per_1k_input: float = 0.00125
    cost_per_1k_output: float = 0.00500
    cache_enabled: bool = True
    cache_path: str = "data/storage/llm_cache.sqlite"
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))


class ChunkingConfig(BaseModel):
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 50
    split_by_headings: bool = True
    supported_extensions: List[str] = Field(
        default_factory=lambda: [
            ".pdf", ".docx", ".doc", ".txt", ".md", ".markdown",
            ".csv", ".json", ".jsonl", ".yaml", ".yml", ".html", ".htm"
        ]
    )


class RetrievalConfig(BaseModel):
    top_k: int = 5
    bm25_weight: float = 0.55
    vector_weight: float = 0.45
    rrf_k: int = 60
    relevance_floor: float = 0.25
    enable_reranker: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"


class GuardrailsConfig(BaseModel):
    enable_pii_redaction: bool = True
    enable_injection_defense: bool = True
    mask_char: str = "[REDACTED]"
    quarantine_untrusted: bool = True


class ReflectionConfig(BaseModel):
    max_retries: int = 2
    grounding_threshold: float = 0.70
    hallucination_floor: float = 0.30


class MemoryConfig(BaseModel):
    db_path: str = "data/storage/copilot_memory.sqlite"
    working_memory_max_steps: int = 50
    episodic_lru_size: int = 100
    enable_sqlite_wal: bool = True


class MCPConfig(BaseModel):
    transport: str = Field(default_factory=lambda: os.getenv("MCP_TRANSPORT", "stdio"))
    host: str = Field(default_factory=lambda: os.getenv("MCP_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("MCP_PORT", "8001")))
    allowed_scopes: List[str] = Field(
        default_factory=lambda: ["read:docs", "read:entity", "write:audit", "execute:query"]
    )


class Settings(BaseModel):
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    config_dir: Path = ROOT_DIR / "config"
    llm: LLMConfig = Field(default_factory=LLMConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    reflection: ReflectionConfig = Field(default_factory=ReflectionConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    policies: Dict[str, Any] = Field(default_factory=dict)

    def resolve_path(self, relative_or_absolute: str | Path) -> Path:
        p = Path(relative_or_absolute)
        return p if p.is_absolute() else self.root_dir / p

    @property
    def sqlite_db_path(self) -> Path:
        return self.resolve_path(self.memory.db_path)

    @property
    def llm_cache_path(self) -> Path:
        return self.resolve_path(self.llm.cache_path)


def load_yaml_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    default_cfg_path = ROOT_DIR / "config" / "default_config.yaml"
    policies_path = ROOT_DIR / "config" / "policies.yaml"

    cfg_dict = load_yaml_config(default_cfg_path)
    policies_dict = load_yaml_config(policies_path)

    settings = Settings(
        llm=LLMConfig(**cfg_dict.get("llm", {})),
        chunking=ChunkingConfig(**cfg_dict.get("chunking", {})),
        retrieval=RetrievalConfig(**cfg_dict.get("retrieval", {})),
        guardrails=GuardrailsConfig(**cfg_dict.get("guardrails", {})),
        reflection=ReflectionConfig(**cfg_dict.get("reflection", {})),
        memory=MemoryConfig(**cfg_dict.get("memory", {})),
        mcp=MCPConfig(**cfg_dict.get("mcp", {})),
        policies=policies_dict,
    )
    return settings


settings = get_settings


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
