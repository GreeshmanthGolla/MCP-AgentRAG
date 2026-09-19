"""Dynamic FastMCP tool implementations for Universal Copilot."""
from __future__ import annotations

import csv
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from universal_copilot.config import settings
from universal_copilot.memory.store import MemoryStore


def tool_query_entity(entity_id: str) -> Dict[str, Any]:
    """Fetch structured attributes and historical cases for a given entity ID."""
    entities_path = settings().data_dir / "synthetic" / "entities.json"
    if entities_path.exists():
        try:
            data = json.loads(entities_path.read_text(encoding="utf-8"))
            if entity_id in data:
                return {"status": "success", "entity": data[entity_id]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "not_found", "message": f"Entity '{entity_id}' not found in registry."}


def tool_list_documents() -> List[Dict[str, Any]]:
    """Return catalog of all available and ingested documents."""
    docs_dir = settings().data_dir / "sample_docs"
    catalog = []
    if docs_dir.exists():
        for f in sorted(docs_dir.iterdir()):
            if f.is_file():
                catalog.append({
                    "filename": f.name,
                    "extension": f.suffix.lower(),
                    "size_bytes": f.stat().st_size,
                    "last_modified": f.stat().st_mtime,
                })
    return catalog


def tool_execute_query(query_str: str) -> Dict[str, Any]:
    """Query structured tabular and catalog data (CSV, JSON)."""
    results: List[Dict[str, Any]] = []
    docs_dir = settings().data_dir / "sample_docs"
    q_lower = query_str.lower()

    # Search product catalog JSON
    catalog_path = docs_dir / "product_catalog.json"
    if catalog_path.exists():
        try:
            cat_data = json.loads(catalog_path.read_text(encoding="utf-8"))
            for prod in cat_data.get("products", []):
                prod_str = json.dumps(prod).lower()
                if any(w in prod_str for w in q_lower.split()):
                    results.append({"type": "product", "data": prod})
        except Exception:
            pass

    # Search roster CSV
    roster_path = docs_dir / "employee_roster.csv"
    if roster_path.exists():
        try:
            with open(roster_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_str = " ".join(row.values()).lower()
                    if any(w in row_str for w in q_lower.split()):
                        results.append({"type": "employee_record", "data": row})
        except Exception:
            pass

    return {
        "status": "success",
        "query": query_str,
        "match_count": len(results),
        "results": results[:10],
    }


def tool_log_audit_event(
    event_type: str,
    user_or_entity: str,
    details: Dict[str, Any],
    store: Optional[MemoryStore] = None,
) -> Dict[str, Any]:
    """Write an immutable compliance audit event to persistent storage."""
    ms = store or MemoryStore()
    event_id = f"evt_{uuid.uuid4().hex[:8]}"
    now = time.time()
    details_json = json.dumps(details)

    with ms.get_connection() as conn:
        conn.execute(
            """INSERT INTO audit_logs (event_id, event_type, user_or_entity, details_json, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (event_id, event_type, user_or_entity, details_json, now),
        )
        conn.commit()

    return {
        "status": "recorded",
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": now,
    }
