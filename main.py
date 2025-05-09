from fastapi import FastAPI, Request
import subprocess
import tempfile
import json
import os

app = FastAPI()

@app.post("/solve")
async def solve(request: Request):
    payload = await request.json()

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp_input:
        json.dump(payload, tmp_input)
        tmp_input.flush()

        result = subprocess.run(
            ["python3", "main.py", tmp_input.name],
            cwd="./packingsolver",  # ← das Tool muss da liegen
            capture_output=True,
            text=True
        )

    if result.returncode != 0:
        return {"error": result.stderr}

    return {"output": result.stdout}
