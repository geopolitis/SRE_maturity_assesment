import json, os
from .constants import DATA_FILE

def load_responses() -> dict:
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f: json.dump({}, f)
        return {}
    try:
        with open(DATA_FILE) as f: return json.load(f)
    except json.JSONDecodeError:
        with open(DATA_FILE,"w") as f: json.dump({}, f)
        return {}

def save_responses(data: dict):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)
