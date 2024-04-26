import os
import constants as cst
import json
import utils.api_gate as api_gate
import os

def _highvram_mode() -> bool:
    high_modes = ["--highvram", "--gpu-only"]
    if os.getenv("VRAM_MODE") in high_modes:
        return True
    return False

# Warmup script to run all workflows once in order to cache the models in VRAM
print("Warming up...")
filename = "warmup_highvram" if _highvram_mode() else "warmup"
print(f"Using High VRAM: {_highvram_mode()}")
filepath = f"{cst.WARMUP_WORKFLOWS_DIR}/{filename}.json"
with open(filepath, "r") as file:
    try:
        payload = json.load(file)
        image = api_gate.generate(payload)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filename}: {e}")

print("Warmup Completed")
