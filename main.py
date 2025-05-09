from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
import csv
import uuid
import os
import subprocess
import json
import tempfile

app = FastAPI()


class Item(BaseModel):
    id: Optional[str] = None
    width: float
    length: float
    height: float
    quantity: int = 1
    weight: Optional[float] = 0.0


class Bin(BaseModel):
    id: Optional[str] = None
    width: float
    length: float
    height: float
    max_weight: Optional[float] = 1000.0


class Parameters(BaseModel):
    bin_infinite_copies: bool = True
    objective: str = "bin-packing"
    time_limit: int = 10


class SolveRequest(BaseModel):
    items: List[Item]
    bins: List[Bin]
    parameters: Optional[Parameters] = Parameters()


@app.post("/solve-boxstacks")
async def solve_boxstacks(data: SolveRequest):
    temp_dir = tempfile.mkdtemp()
    items_file = os.path.join(temp_dir, "items.csv")
    bins_file = os.path.join(temp_dir, "bins.csv")
    params_file = os.path.join(temp_dir, "parameters.csv")
    output_file = os.path.join(temp_dir, "output.json")

    # Write items.csv
    with open(items_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "width", "length", "height", "quantity", "weight"])
        for idx, item in enumerate(data.items):
            writer.writerow([
                item.id or f"item_{idx}",
                item.width,
                item.length,
                item.height,
                item.quantity,
                item.weight or 0
            ])

    # Write bins.csv
    with open(bins_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "width", "length", "height", "max_weight"])
        for idx, bin in enumerate(data.bins):
            writer.writerow([
                bin.id or f"bin_{idx}",
                bin.width,
                bin.length,
                bin.height,
                bin.max_weight or 1000.0
            ])

    # Write parameters.csv
    with open(params_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        writer.writerow(["objective", data.parameters.objective])
        writer.writerow(["time_limit", data.parameters.time_limit])
        if data.parameters.bin_infinite_copies:
            writer.writerow(["bin_infinite_copies", "true"])

    # Call the binary
    try:
        result = subprocess.run([
            "./install/bin/packingsolver_boxstacks",
            "--verbosity-level", "0",
            "--items", items_file,
            "--bins", bins_file,
            "--parameters", params_file,
            "--output", output_file,
            "--certificate", os.path.join(temp_dir, "solution.csv"),
        ], capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            return {"error": result.stderr}

        with open(output_file, "r") as f:
            solution = json.load(f)

        return {"output": solution}

    except Exception as e:
        return {"error": str(e)}
