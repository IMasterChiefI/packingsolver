from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import csv
import os
import subprocess
import json
import tempfile

app = FastAPI()

# Vordefinierte Ladehilfsmittel mit realistischen Abmessungen, Gewicht und Koordinaten
PREDEFINED_BINS = [
    {
        "id": "euro",
        "max_weight": 1000,
        "X": 120.0,  # Länge in cm
        "Y": 80.0,   # Breite in cm
        "Z": 130.0,  # Maximale Höhe mit Beladung
        "cost": 10.0
    },
    {
        "id": "chep",
        "max_weight": 1000,
        "X": 100.0,
        "Y": 120.0,
        "Z": 130.0,
        "cost": 12.0
    },
    {
        "id": "industrie",
        "max_weight": 1450,
        "X": 120.0,
        "Y": 100.0,
        "Z": 130.0,
        "cost": 13.5
    }
]

class Item(BaseModel):
    id: Optional[str] = None
    x: float  # Länge
    y: float  # Breite
    z: float  # Höhe
    quantity: int = 1
    weight: Optional[float] = 0.0

class Parameters(BaseModel):
    objective: str = "bin-packing"
    bin_infinite_copies: bool = True
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
            "id", "x", "y", "z", "quantity", "weight",
            "max_stack_above_weight", "max_items_in_stack", "nesting_height",
            "X", "Y", "Z"
        ])
        for idx, item in enumerate(data.items):
            writer.writerow([
                item.id or f"item_{idx}",
                float(item.x), float(item.y), float(item.z),
                int(item.quantity), float(item.weight or 0),
                99999, 0, 0, "", "", ""
            ])

    # Schreibe bins.csv
    with open(bins_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "max_weight", "X", "Y", "Z", "cost"])
        for b in PREDEFINED_BINS:
            writer.writerow([b["id"], b["max_weight"], b["X"], b["Y"], b["Z"], b["cost"]])

    # Schreibe parameters.csv mit vollständigen Defaults
    with open(params_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        writer.writerows([
            ["objective", data.parameters.objective],
            ["bin_infinite_copies", str(data.parameters.bin_infinite_copies).lower()],
            ["unloading_constraint", "IncreasingX"],
            ["group_bin_number", -1],
            ["group_stack_number", -1],
            ["group_stack_orientation", 0],
            ["group_stack_height", -1],
            ["group_stack_area", -1],
            ["group_stack_weight", -1],
            ["group_stack_density", -1],
            ["group_stack_cost", -1],
            ["group_item_number", -1],
            ["group_item_orientation", 0],
            ["group_item_height", -1],
            ["group_item_area", -1],
            ["group_item_weight", -1],
            ["group_item_density", -1],
            ["group_item_cost", -1],
            ["verbosity_level", 1],
            ["time_limit", data.parameters.time_limit]
        ])

    try:
        result = subprocess.run([
            "./install/bin/packingsolver_boxstacks",
            "--verbosity-level", "1",
            "--items", items_file,
            "--bins", bins_file,
            "--parameters", params_file,
            "--output", output_file
        ], capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            return {"error": result.stderr}

        with open(output_file, "r") as f:
            return {"output": json.load(f)}

    except Exception as e:
        return {"error": str(e)}
