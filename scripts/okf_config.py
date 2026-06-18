# scripts/okf_config.py
"""Read/write the optional okf.json bundle config. An absent or malformed file
falls back to defaults. Only the three known keys are persisted."""
import json
from pathlib import Path

KEYS = ("name", "stale_days", "link_style")

def default_config(root):
    return {"name": Path(root).name, "stale_days": 180, "link_style": "absolute"}

def _valid(key, value):
    """Reject wrong-typed values from a hand-edited okf.json so a typo like
    stale_days: "soon" can't crash a downstream consumer; it falls back to the
    default instead. (bool is excluded from int — JSON true/false isn't a count.)"""
    if key == "stale_days":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, str)   # name, link_style

def load_config(root):
    cfg = default_config(root)
    f = Path(root) / "okf.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):   # invalid JSON or unreadable/bad encoding
            data = None
        if isinstance(data, dict):
            cfg.update({k: v for k, v in data.items() if k in KEYS and _valid(k, v)})
    return cfg

def save_config(root, config):
    merged = default_config(root)
    merged.update({k: v for k, v in config.items() if k in KEYS})
    (Path(root) / "okf.json").write_text(json.dumps(merged, indent=2) + "\n",
                                         encoding="utf-8")
    return merged
