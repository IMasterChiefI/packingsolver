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
        "ID": "euro",
        "X": 1200, "Y": 800, "Z": 1300,
        "COST": 10.0, "COPIES": 1, "COPIES_MIN": 0,
        "MAXIMUM_WEIGHT": 1000, "MAXIMUM_STACK_DENSITY": 0.0017,
        "IS_SEMI_TRAILER_TRUCK": 0, "TRACTOR_WEIGHT": 0,
        "FRONT_AXLE_MIDDLE_AXLE_DISTANCE": 0,
        "FRONT_AXLE_TRACTOR_GRAVITY_CENTER_DISTANCE": 0,
        "FRONT_AXLE_HARNESS_DISTANCE": 0,
        "EMPTY_TRAILER_WEIGHT": 0,
        "HARNESS_REAR_AXLE_DISTANCE": 0,
        "TRAILER_GRAVITY_CENTER_REAR_AXLE_DISTANCE": 0,
        "TRAILER_START_HARNESS_DISTANCE": 0,
        "REAR_AXLE_MAXIMUM_WEIGHT": 99999,
        "MIDDLE_AXLE_MAXIMUM_WEIGHT": 99999
    },
    {
        "ID": "chep",
        "X": 1000, "Y": 1200, "Z": 1300,
        "COST": 12.0, "COPIES": 1, "COPIES_MIN": 0,
        "MAXIMUM_WEIGHT": 1000, "MAXIMUM_STACK_DENSITY": 0.0017,
        "IS_SEMI_TRAILER_TRUCK": 0, "TRACTOR_WEIGHT": 0,
        "FRONT_AXLE_MIDDLE_AXLE_DISTANCE": 0,
        "FRONT_AXLE_TRACTOR_GRAVITY_CENTER_DISTANCE": 0,
        "FRONT_AXLE_HARNESS_DISTANCE": 0,
        "EMPTY_TRAILER_WEIGHT": 0,
        "HARNESS_REAR_AXLE_DISTANCE": 0,
        "TRAILER_GRAVITY_CENTER_REAR_AXLE_DISTANCE": 0,
        "TRAILER_START_HARNESS_DISTANCE": 0,
        "REAR_AXLE_MAXIMUM_WEIGHT": 99999,
        "MIDDLE_AXLE_MAXIMUM_WEIGHT": 99999
    },
    {
        "ID": "industrie",
        "X": 1200, "Y": 1000, "Z": 1300,
        "COST": 13.5, "COPIES": 1, "COPIES_MIN": 0,
        "MAXIMUM_WEIGHT": 1450, "MAXIMUM_STACK_DENSITY": 0.0017,
        "IS_SEMI_TRAILER_TRUCK": 0, "TRACTOR_WEIGHT": 0,
        "FRONT_AXLE_MIDDLE_AXLE_DISTANCE": 0,
        "FRONT_AXLE_TRACTOR_GRAVITY_CENTER_DISTANCE": 0,
        "FRONT_AXLE_HARNESS_DISTANCE": 0,
        "EMPTY_TRAILER_WEIGHT": 0,
        "HARNESS_REAR_AXLE_DISTANCE": 0,
        "TRAILER_GRAVITY_CENTER_REAR_AXLE_DISTANCE": 0,
        "TRAILER_START_HARNESS_DISTANCE": 0,
        "REAR_AXLE_MAXIMUM_WEIGHT": 99999,
        "MIDDLE_AXLE_MAXIMUM_WEIGHT": 99999
    }
]

class Item(BaseModel):
    id: Optional[str] = None
    x: float
    y: float
    z: float
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
            "ID", "X", "Y", "Z", "COPIES", "PROFIT", "GROUP_ID", "ROTATIONS",
            "WEIGHT", "STACKABILITY_ID", "NESTING_HEIGHT",
            "MAXIMUM_STACKABILITY", "MAXIMUM_WEIGHT_ABOVE"
        ])
        for idx, item in enumerate(data.items):
            writer.writerow([
                item.id or f"item_{idx}",
                float(item.x),         # X
                float(item.y),         # Y
                float(item.z),         # Z
                int(item.quantity),    # COPIES
                0,                     # PROFIT
                0,                     # GROUP_ID
                63,                    # ROTATIONS
                float(item.weight or 0),
                0,                     # STACKABILITY_ID
                0,                     # NESTING_HEIGHT
                0,                     # MAXIMUM_STACKABILITY
                99999                  # MAXIMUM_WEIGHT_ABOVE
            ])

    with open(bins_file, "w", newline="") as f:
        fieldnames = ["ID","X","Y","Z","COST","COPIES","COPIES_MIN","MAXIMUM_WEIGHT","MAXIMUM_STACK_DENSITY","IS_SEMI_TRAILER_TRUCK","TRACTOR_WEIGHT","FRONT_AXLE_MIDDLE_AXLE_DISTANCE","FRONT_AXLE_TRACTOR_GRAVITY_CENTER_DISTANCE","FRONT_AXLE_HARNESS_DISTANCE","EMPTY_TRAILER_WEIGHT","HARNESS_REAR_AXLE_DISTANCE","TRAILER_GRAVITY_CENTER_REAR_AXLE_DISTANCE","TRAILER_START_HARNESS_DISTANCE","REAR_AXLE_MAXIMUM_WEIGHT","MIDDLE_AXLE_MAXIMUM_WEIGHT"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for bin in PREDEFINED_BINS:
            writer.writerow(bin)


    with open(params_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        writer.writerows([
            ["objective", data.parameters.objective],
            ["bin_infinite_copies", str(data.parameters.bin_infinite_copies).lower()],
            ["time_limit", data.parameters.time_limit],
            ["verbosity_level", 1],
            ["unloading_constraint", "IncreasingX"]
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
