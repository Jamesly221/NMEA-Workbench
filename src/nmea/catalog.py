"""Load and validate user-editable JSON reference entries."""
import json
import re
from pathlib import Path


def load_catalog(directory: Path):
    entries, errors = {}, []
    for path in sorted(directory.glob("*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(entry, dict):
                raise ValueError("entry must be an object")
            code = entry.get("type", "")
            if not isinstance(code, str) or not re.fullmatch(r"[A-Z0-9]{3}", code):
                raise ValueError("type must be three uppercase letters/digits")
            for key in ("title", "description", "example", "notes", "source"):
                if not isinstance(entry.get(key), str):
                    raise ValueError(f"{key} must be text")
            fields = entry.get("fields")
            if not isinstance(fields, list) or not fields:
                raise ValueError("fields must be a nonempty list")
            for field in fields:
                if not isinstance(field, dict) or not all(isinstance(field.get(k), str) for k in ("name", "description")):
                    raise ValueError("each field needs a name and description")
            if code in entries:
                raise ValueError(f"duplicate type {code}")
            entries[code] = entry
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"{path.name}: {exc}")
    if not entries and not errors:
        errors.append(f"No reference entries found in {directory}")
    return entries, errors
