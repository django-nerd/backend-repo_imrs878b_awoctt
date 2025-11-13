import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import TrashHotspot

app = FastAPI(title="Ocean Trash Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Ocean Trash Management Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# -----------------------------
# Trash Hotspot API
# -----------------------------

class HotspotCreate(TrashHotspot):
    pass

@app.get("/api/hotspots", response_model=List[TrashHotspot])
def list_hotspots(limit: Optional[int] = None):
    try:
        docs = get_documents("trashhotspot", {}, limit)
        # Normalize MongoDB documents to Pydantic model-compatible dicts
        result = []
        for d in docs:
            d.pop("_id", None)
            result.append(TrashHotspot(**d))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hotspots")
def create_hotspot(payload: HotspotCreate):
    try:
        data = payload.model_dump()
        inserted_id = create_document("trashhotspot", data)
        return {"id": inserted_id, "ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seed-hotspots")
def seed_hotspots():
    """Seed the database with a few known ocean garbage patch hotspots"""
    try:
        seeds = [
            {
                "name": "Great Pacific Garbage Patch",
                "latitude": 31.0,
                "longitude": -140.0,
                "density": 600.0,
                "area_km2": 1600000,
                "description": "Largest accumulation of ocean plastic in the North Pacific Gyre",
                "collected_kg": 0,
                "severity": "critical",
                "tags": ["pacific", "gyre", "macroplastics"]
            },
            {
                "name": "North Atlantic Subtropical Gyre",
                "latitude": 31.0,
                "longitude": -60.0,
                "density": 300.0,
                "area_km2": 1000000,
                "description": "High-density accumulation zone in the Atlantic",
                "collected_kg": 0,
                "severity": "high",
                "tags": ["atlantic", "gyre"]
            },
            {
                "name": "Indian Ocean Gyre",
                "latitude": -25.0,
                "longitude": 80.0,
                "density": 280.0,
                "area_km2": 1200000,
                "description": "Persistent plastic accumulation region",
                "collected_kg": 0,
                "severity": "high",
                "tags": ["indian", "gyre"]
            },
            {
                "name": "South Pacific Gyre",
                "latitude": -30.0,
                "longitude": -120.0,
                "density": 200.0,
                "area_km2": 800000,
                "description": "Southern hemisphere accumulation zone",
                "collected_kg": 0,
                "severity": "medium",
                "tags": ["pacific", "south"]
            }
        ]
        created = []
        for s in seeds:
            created.append(create_document("trashhotspot", s))
        return {"inserted": created, "count": len(created)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
