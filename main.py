"""SASVA REST API.

Run locally:
    uvicorn server.main:app --reload --port 8000
Docs:
    http://localhost:8000/docs
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from server import engine

app = FastAPI(
    title="SASVA API",
    description=(
        "AI driven scheme matching for marginalised entrepreneurs. "
        "Team NEXUS, SIH 2026, Problem ID SIH26092."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------


class Profile(BaseModel):
    name: str = ""
    category: str = Field("General", description="General, SC, ST, OBC, Minority, PwD")
    gender: str = "Female"
    age: int = 30
    sector: str = "Food Processing"
    funding_need: int = 300000
    region: str = "Rural"
    state: str = ""


class MatchRequest(BaseModel):
    profile: Profile = Profile()
    query: str = ""
    limit: int = 20


class FeedbackRequest(BaseModel):
    name: str = ""
    role: str = "User"
    scheme_id: Optional[str] = None
    helpful: Optional[bool] = None
    comment: str = ""


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.get("/", tags=["meta"])
def root() -> Dict[str, Any]:
    return {
        "service": "SASVA API",
        "status": "ok",
        "endpoints": ["/schemes", "/schemes/{id}", "/match", "/feedback", "/sync", "/resync", "/stats"],
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/schemes", tags=["schemes"])
def list_schemes(
    q: str = Query("", description="Free text, e.g. women rural food"),
    limit: int = Query(50, ge=1, le=300),
) -> Dict[str, Any]:
    results = engine.search_schemes(q, limit=limit)
    return {"count": len(results), "query": q, "schemes": results}


@app.get("/schemes/{scheme_id}", tags=["schemes"])
def scheme_detail(scheme_id: str) -> Dict[str, Any]:
    scheme = engine.get_scheme(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"No scheme with id {scheme_id}")
    return scheme


@app.post("/match", tags=["matching"])
def match(req: MatchRequest) -> Dict[str, Any]:
    results = engine.match_schemes(
        req.profile.model_dump(), query=req.query, limit=req.limit
    )
    return {
        "count": len(results),
        "weights": engine.WEIGHTS,
        "profile": req.profile.model_dump(),
        "schemes": results,
    }


@app.post("/feedback", tags=["learning"])
def feedback(req: FeedbackRequest) -> Dict[str, Any]:
    return engine.save_feedback(req.model_dump())


@app.get("/feedback", tags=["learning"])
def feedback_list() -> Dict[str, Any]:
    log = engine.feedback_log()
    return {"count": len(log), "feedback": log}


@app.get("/sync", tags=["auto-feed"])
def sync() -> Dict[str, str]:
    return engine.sync_status()


@app.post("/resync", tags=["auto-feed"])
def resync(role: str = Query("Admin", description="Only Admin may force a re-sync")) -> Dict[str, Any]:
    if role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Force re-sync is restricted to Admin")
    status = engine.force_resync()
    return {"resynced": True, **status}


@app.get("/stats", tags=["meta"])
def stats() -> Dict[str, Any]:
    return engine.stats()


@app.get("/languages", tags=["meta"])
def languages() -> Dict[str, List[str]]:
    return {"count": len(engine.LANGUAGES), "languages": engine.LANGUAGES}
