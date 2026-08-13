"""Seed Ctrl+E for Send selection when keys.json has no entry yet."""
import json
import os
import sys

path = sys.argv[1]
key = "cuda_statghost,send_selection"
entry = {
    "name": "plugin: STATghost: Send selection",
    "s1": ["Ctrl+E"],
}
data = {}
if os.path.isfile(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read().strip()
    if raw:
        data = json.loads(raw)
if key in data:
    print("keys.json: " + key + " already set — left untouched")
else:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data[key] = entry
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print("keys.json: seeded Ctrl+E for Send selection")
