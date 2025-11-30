from __future__ import annotations
from pathlib import Path
import json, time

# Directory for session files
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _session_file(session_id: str) -> Path:
    return DATA_DIR / f"session_{session_id}.jsonl"

def append_turn(session_id: str, role: str, content: str, meta: dict | None = None) -> None:
    if not session_id:
        return
    rec = {
        "t": time.time(),
        "role": role,
        "content": content,
        "meta": meta or {}
    }
    path = _session_file(session_id)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(existing + json.dumps(rec, ensure_ascii=True) + "\n", encoding="utf-8")

def load_history(session_id: str, limit: int = 24) -> list[dict]:
    path = _session_file(session_id)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    out = []
    for ln in lines:
        try:
            rec = json.loads(ln)
            out.append({"role": rec.get("role", "user"), "content": rec.get("content", "")})
        except json.JSONDecodeError:
            pass
    return out

def first_user_question(session_id: str) -> str | None:
    path = _session_file(session_id)
    if not path.exists():
        return None
    for ln in path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(ln)
            if rec.get("role") == "user":
                return rec.get("content")
        except json.JSONDecodeError:
            continue
    return None
