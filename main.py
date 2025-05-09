from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
import csv
import os
import subprocess
import json
import tempfile

app = FastAPI()

# Vordefinierte Ladehilfsmittel (Paletten)
PREDEFINED_BINS = [
    {
        "id": "euro",
        "width": 120,
        "length": 80,
        "height": 130,
        "max_weight": 1000
    },
    {
        "id": "chep",
        "width": 100,
        "length": 120,
        "height": 130,
        "max_weight": 1000
    },
    {
        "id": "industrie",
        "width": 120,
        "length": 100,
        "height": 130,
        "max_weight": 1450
    }
]

# Eingabe-Schema für Items
class Item(BaseModel):
    id: Optional[str] = None
    width: float
    length: float
    height: float
    quantity: int = 1
    weight: Optional[float] = 0.0

class Parameters(BaseModel):
    bin_infinite_copies: bool = True
    objective: str = "bin-packing"
    time_limit: int = 10

class SolveRequest(BaseModel):
    items: List[Item]
    parameters: Optional[Parameters] = Parameters()

@app.post("/solve-boxstacks")
async def solve_boxstacks(data: SolveRequest):
    temp_dir = tempfile.mkdtemp()
    items_file = os.path.join(temp_dir, "items.csv")
    bins_file = os.path.join(temp_dir, "bins.csv")
    params_file = os.path.join(temp_dir, "parameters.csv")
    output_file = os.path.join(temp_dir, "output.json")

    # Schreibe items.csv
    with open(items_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "width", "length", "height", "quantity", "weight",
            "max_stack_above_weight", "max_items_in_stack", "nesting_height",
            "X", "Y", "Z"
        ])
        for idx, item in enumerate(data.items):
            writer.writerow([
                item.id or f"item_{idx}",
                float(item.width),
                float(item.length),
                float(item.height),
                int(item.quantity),
                float(item.weight or 0),
                99999,  # max_stack_above_weight
                0,      # max_items_in_stack
                0,      # nesting_height
                0, 0, 0  # X, Y, Z
            ])

    # Schreibe bins.csv aus PREDEFINED_BINS
    with open(bins_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "width", "length", "height", "max_weight", "X", "Y", "Z"])
        for bin in PREDEFINED_BINS:
            writer.writerow([
                bin["id"],
                bin["width"],
                bin["length"],
                bin["height"],
                bin["max_weight"],
                1, 1, 1
            ])

    # Schreibe parameters.csv mit optimalen Defaults
    with open(params_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        writer.writerow(["objective", data.parameters.objective])
        writer.writerow(["bin_infinite_copies", str(data.parameters.bin_infinite_copies).lower()])
        writer.writerow(["time_limit", data.parameters.time_limit])
        writer.writerow(["unloading_constraint", "IncreasingX"])
        writer.writerow(["verbosity_level", 0])

    # Führe den Solver aus
    try:
        result = subprocess.run([
            "./install/bin/packingsolver_boxstacks",
            "--verbosity-level", "0",
            "--items", items_file,
            "--bins", bins_file,
            "--parameters", params_file,
            "--output", output_file,
            "--certificate", os.path.join(temp_dir, "solution.csv")
        ], capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            return {"error": result.stderr}

        with open(output_file, "r") as f:
            solution = json.load(f)

        return {"output": solution}

    except Exception as e:
        return {"error": str(e)}
