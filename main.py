import os
from datetime import datetime, time, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal

from database import create_document
from schemas import ProductionEntry, PackingEntry, DowntimeEntry

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Production Daily Count Backend"}

# Shift determination
class ShiftInfo(BaseModel):
    shift: Literal["First", "Second", "Off"]
    sheet_name: str


def determine_shift(now: datetime) -> ShiftInfo:
    # Define shift times in local time (assume server local time)
    first_start = time(7, 0)
    first_end = time(15, 25)
    second_start = time(15, 30)
    second_end = time(23, 59, 59)

    current_time = now.time()

    if first_start <= current_time <= first_end:
        return ShiftInfo(shift="First", sheet_name=f"{now.strftime('%Y-%m-%d')}_First")
    elif second_start <= current_time <= second_end:
        return ShiftInfo(shift="Second", sheet_name=f"{now.strftime('%Y-%m-%d')}_Second")
    else:
        # After midnight until before 7:00 treated as off for safety
        # If needed, associate 00:00-00:05 with previous Second shift, but keeping simple
        return ShiftInfo(shift="Off", sheet_name=f"{now.strftime('%Y-%m-%d')}_Off")


# Google Sheets placeholder replaced with MongoDB persistence and CSV export per sheet_name
import csv
from pathlib import Path

DATA_DIR = Path("logs/exports")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def export_to_csv(sheet_name: str, headers: List[str], row: List):
    file_path = DATA_DIR / f"{sheet_name}.csv"
    file_exists = file_path.exists()
    with file_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(row)


@app.post("/api/production")
def submit_production(entry: ProductionEntry):
    now = entry.timestamp
    info = determine_shift(now)
    if info.shift == "Off":
        # We still accept but mark as Off shift
        pass

    # Persist to MongoDB
    doc_id = create_document("productionentry", entry)

    # Export to CSV sheet per shift
    headers = [
        "operator_name",
        "operator_id",
        "operator_type",
        "test_type",
        "test_station",
        "device_type",
        "production_count",
        "timestamp",
        "shift",
        "mongo_id",
    ]
    row = [
        entry.operator_name,
        entry.operator_id,
        entry.operator_type,
        entry.test_type,
        entry.test_station,
        entry.device_type,
        entry.production_count,
        entry.timestamp.isoformat(),
        info.shift,
        doc_id,
    ]
    export_to_csv(info.sheet_name + "_production", headers, row)

    return {"status": "ok", "id": doc_id, "shift": info.shift}


@app.post("/api/packing")
def submit_packing(entry: PackingEntry):
    now = entry.timestamp
    info = determine_shift(now)
    doc_id = create_document("packingentry", entry)

    headers = [
        "operator_name",
        "device_type",
        "operator_type",
        "job_type",
        "packing_count",
        "timestamp",
        "shift",
        "mongo_id",
    ]
    row = [
        entry.operator_name,
        entry.device_type,
        entry.operator_type,
        entry.job_type,
        entry.packing_count,
        entry.timestamp.isoformat(),
        info.shift,
        doc_id,
    ]
    export_to_csv(info.sheet_name + "_packing", headers, row)

    return {"status": "ok", "id": doc_id, "shift": info.shift}


@app.post("/api/downtime")
def submit_downtime(entry: DowntimeEntry):
    now = entry.timestamp
    info = determine_shift(now)
    doc_id = create_document("downtimeentry", entry)

    headers = [
        "operator_name",
        "description",
        "timestamp",
        "shift",
        "mongo_id",
    ]
    row = [
        entry.operator_name,
        entry.description,
        entry.timestamp.isoformat(),
        info.shift,
        doc_id,
    ]
    export_to_csv(info.sheet_name + "_downtime", headers, row)

    return {"status": "ok", "id": doc_id, "shift": info.shift}


@app.get("/test")
def test_database():
    from database import db
    status = {
        "backend": "Running",
        "database": "Connected" if db is not None else "Not Available",
    }
    return status


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
