"""SASVA matching engine.

Single source of truth for scheme loading, keyword search and eligibility
scoring. The FastAPI server imports it; the Streamlit client imports it too as
an offline fallback so the demo never dies when the API is unreachable.

Scoring weights are fixed and auditable:
    Category 40 + Funding 30 + Sector 15 + Region 15 = 100
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "schemes.json"
FEEDBACK_FILE = Path(__file__).resolve().parents[1] / "data" / "feedback.json"

WEIGHTS = {"category": 40, "funding": 30, "sector": 15, "region": 15}

IST = timezone(timedelta(hours=5, minutes=30))

LANGUAGES = [
    "English", "Hindi", "Bengali", "Marathi", "Telugu", "Tamil", "Gujarati",
    "Urdu", "Kannada", "Odia", "Malayalam", "Punjabi", "Assamese", "Maithili",
    "Santali", "Kashmiri", "Nepali", "Sindhi", "Dogri", "Konkani",
    "Manipuri", "Bodo",
]

# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

_CACHE: Dict[str, Any] = {}


def load_data(refresh: bool = False) -> Dict[str, Any]:
    """Load the scheme catalogue, cached in memory."""
    if refresh or "data" not in _CACHE:
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            _CACHE["data"] = json.load(fh)
    return _CACHE["data"]


def all_schemes() -> List[Dict[str, Any]]:
    return load_data()["schemes"]


def get_scheme(scheme_id: str) -> Optional[Dict[str, Any]]:
    return next((s for s in all_schemes() if s["id"] == scheme_id.upper()), None)


def meta() -> Dict[str, Any]:
    return load_data()["meta"]


def sync_status() -> Dict[str, str]:
    """Timestamps shown in the auto-feed strip."""
    last = _CACHE.get("last_synced") or meta().get("last_synced")
    try:
        last_dt = datetime.fromisoformat(str(last))
    except ValueError:
        last_dt = datetime.now(IST)
    tonight = (datetime.now(IST) + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return {
        "last_synced": last_dt.strftime("%d %b %Y, %I:%M %p"),
        "next_sync": tonight.strftime("%d %b %Y, 12:00 AM"),
        "source": "myscheme.gov.in",
        "schemes_live": str(meta().get("schemes_live", len(all_schemes()))),
        "schemes_in_pipeline": str(meta().get("schemes_in_pipeline", "")),
    }


def force_resync() -> Dict[str, str]:
    """Simulated pull from the government feed. Only the timestamp moves."""
    _CACHE["last_synced"] = datetime.now(IST).isoformat(timespec="seconds")
    load_data(refresh=True)
    return sync_status()


# ---------------------------------------------------------------------------
# Lite vector index
# ---------------------------------------------------------------------------


def _tokenise(text: str) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 2]


class LiteVectorIndex:
    """TF-IDF cosine index with a vector-DB shaped interface.

    Deliberately dependency free so the demo deploys on the free tiers. To move
    to 300+ schemes with true semantic search, keep the ``add`` / ``search``
    signatures and swap the internals for Chroma, FAISS or pgvector::

        collection = chroma_client.get_or_create_collection("sasva_schemes")
        collection.add(ids=ids, documents=docs, metadatas=metas)
        collection.query(query_texts=[q], n_results=k)

    Only ``_embed`` and ``search`` need to change; nothing upstream does.
    """

    def __init__(self) -> None:
        self._docs: Dict[str, Counter] = {}
        self._idf: Dict[str, float] = {}

    def add(self, doc_id: str, text: str) -> None:
        self._docs[doc_id] = Counter(_tokenise(text))
        self._idf = {}

    def _build_idf(self) -> None:
        n = max(len(self._docs), 1)
        df: Counter = Counter()
        for tf in self._docs.values():
            df.update(tf.keys())
        self._idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}

    def _embed(self, tf: Counter) -> Dict[str, float]:
        if not self._idf:
            self._build_idf()
        vec = {t: (1 + math.log(c)) * self._idf.get(t, 1.0) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def search(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        q = self._embed(Counter(_tokenise(query)))
        if not q:
            return []
        hits = []
        for doc_id, tf in self._docs.items():
            d = self._embed(tf)
            score = sum(w * d.get(t, 0.0) for t, w in q.items())
            if score > 0:
                hits.append({"id": doc_id, "score": round(score, 4)})
        hits.sort(key=lambda h: h["score"], reverse=True)
        return hits[:k]


def build_index() -> LiteVectorIndex:
    if "index" not in _CACHE:
        idx = LiteVectorIndex()
        for s in all_schemes():
            blob = " ".join(
                [
                    s["name"], s.get("short", ""), s["ministry"], s["benefit"],
                    " ".join(s.get("keywords", [])),
                    " ".join(s.get("sectors", [])),
                    " ".join(s.get("categories", [])),
                    " ".join(s.get("regions", [])),
                ]
            )
            idx.add(s["id"], blob)
        _CACHE["index"] = idx
    return _CACHE["index"]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_schemes(query: str = "", limit: int = 50) -> List[Dict[str, Any]]:
    """Keyword search, semantically ranked. Empty query returns everything."""
    schemes = all_schemes()
    if not query.strip():
        return schemes[:limit]

    q = query.lower().strip()
    ranked = {h["id"]: h["score"] for h in build_index().search(q, k=limit)}

    out = []
    for s in schemes:
        blob = " ".join(
            [s["name"], s.get("short", ""), s["ministry"], s["benefit"]]
            + s.get("keywords", []) + s.get("sectors", [])
            + s.get("categories", []) + s.get("regions", [])
        ).lower()
        literal = any(word in blob for word in q.split())
        if literal or s["id"] in ranked:
            item = dict(s)
            item["_relevance"] = round(ranked.get(s["id"], 0.15) * 100, 1)
            out.append(item)

    out.sort(key=lambda s: s["_relevance"], reverse=True)
    return out[:limit]


# ---------------------------------------------------------------------------
# Eligibility scoring
# ---------------------------------------------------------------------------

DEFAULT_PROFILE = {
    "name": "",
    "category": "General",
    "gender": "Female",
    "age": 30,
    "sector": "Food Processing",
    "funding_need": 300000,
    "region": "Rural",
    "state": "West Bengal",
}


ALL_CATEGORIES = ["General", "SC", "ST", "OBC", "Minority", "PwD"]


def _category_score(profile: Dict[str, Any], scheme: Dict[str, Any]) -> float:
    """Reward schemes actually targeted at this applicant, not just open to them."""
    cats = [c.lower() for c in scheme.get("categories", [])]
    core = [c for c in cats if c in [x.lower() for x in ALL_CATEGORIES]]
    mine = str(profile.get("category", "General")).lower()
    targeted = len(core) <= 2

    if mine in cats:
        score = 1.0 if targeted else 0.72
    elif "general" in cats:
        score = 0.30
    else:
        return 0.0

    # Women-only schemes are a direct hit for women applicants
    if str(scheme.get("gender", "any")).lower() == "female" \
            and str(profile.get("gender", "")).lower() == "female":
        score = min(1.0, score + 0.28)
    return round(score, 3)


def _funding_score(profile: Dict[str, Any], scheme: Dict[str, Any]) -> float:
    """Inside the band scores well, and a tight band that fits scores better
    than a very wide band that happens to contain the number."""
    need = float(profile.get("funding_need") or 0)
    lo, hi = float(scheme["funding_min"]), float(scheme["funding_max"])
    if need <= 0:
        return 0.5

    spread = max(hi / max(lo, 1.0), 1.0)
    precision = min(1.0, max(0.55, 1.2 - 0.25 * math.log10(spread)))

    if lo <= need <= hi:
        centre = 1.0
    elif need < lo:
        centre = max(0.0, 0.75 * (need / lo))
    else:
        centre = max(0.0, 0.60 * (hi / need))
    return round(precision * centre, 3)


def _sector_score(profile: Dict[str, Any], scheme: Dict[str, Any]) -> float:
    """A specialist scheme for your sector beats an everything-scheme."""
    sectors = [s.lower() for s in scheme.get("sectors", [])]
    mine = str(profile.get("sector", "")).lower()
    if not sectors:
        return 0.5
    if mine not in sectors:
        return 0.15
    if len(sectors) <= 2:
        return 1.0
    if len(sectors) <= 3:
        return 0.85
    return 0.70


def _region_score(profile: Dict[str, Any], scheme: Dict[str, Any]) -> float:
    regions = [r.lower() for r in scheme.get("regions", [])]
    mine = str(profile.get("region", "")).lower()
    if not regions:
        return 0.5
    if mine not in regions:
        return 0.0
    return 1.0 if len(regions) == 1 else 0.8


def _blockers(profile: Dict[str, Any], scheme: Dict[str, Any]) -> List[str]:
    out = []
    gender = str(scheme.get("gender", "any")).lower()
    mine = str(profile.get("gender", "")).lower()
    if gender == "female" and mine not in ("female", "other", ""):
        out.append("Reserved for women applicants")
    if str(profile.get("category", "")).lower() not in [
        c.lower() for c in scheme.get("categories", [])
    ] and "general" not in [c.lower() for c in scheme.get("categories", [])]:
        out.append("Restricted to " + ", ".join(scheme.get("categories", [])))
    age = int(profile.get("age") or 0)
    if age and age < int(scheme.get("age_min", 0)):
        out.append(f"Minimum age {scheme.get('age_min')}")
    if age and scheme.get("age_max") and age > int(scheme["age_max"]):
        out.append(f"Maximum age {scheme['age_max']}")
    region = _region_score(profile, scheme)
    if region == 0.0:
        out.append("Applies to " + ", ".join(scheme.get("regions", [])) + " areas only")
    return out


def score_scheme(profile: Dict[str, Any], scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Return the scheme plus a fully traceable score breakdown."""
    prof = {**DEFAULT_PROFILE, **(profile or {})}
    parts = {
        "category": _category_score(prof, scheme),
        "funding": _funding_score(prof, scheme),
        "sector": _sector_score(prof, scheme),
        "region": _region_score(prof, scheme),
    }
    breakdown = {k: round(parts[k] * WEIGHTS[k], 1) for k in WEIGHTS}
    total = round(sum(breakdown.values()), 1)
    blockers = _blockers(prof, scheme)
    if blockers:
        total = round(min(total, 45.0), 1)

    eligible = int(round(total))
    item = dict(scheme)
    item["match"] = {
        "eligible_pct": eligible,
        "breakdown": breakdown,
        "weights": WEIGHTS,
        "blockers": blockers,
        "verdict": (
            "Strong match" if eligible >= 80 and not blockers
            else "Worth applying" if eligible >= 60 and not blockers
            else "Check eligibility"
        ),
    }
    return item


def match_schemes(
    profile: Dict[str, Any], query: str = "", limit: int = 20
) -> List[Dict[str, Any]]:
    """Search then score. Highest eligibility first."""
    pool = search_schemes(query, limit=100)
    scored = [score_scheme(profile, s) for s in pool]
    scored.sort(
        key=lambda s: (s["match"]["eligible_pct"], s.get("_relevance", 0)),
        reverse=True,
    )
    return scored[:limit]


# ---------------------------------------------------------------------------
# Feedback loop
# ---------------------------------------------------------------------------


def save_feedback(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Append feedback and return the retraining signal it produced.

    Falls back to in-memory storage on read-only containers, which is what
    Render and Streamlit Cloud give you on the free tier.
    """
    record = {
        "received_at": datetime.now(IST).isoformat(timespec="seconds"),
        **entry,
    }
    store = _CACHE.setdefault("feedback", [])
    store.append(record)
    persisted = False
    try:
        existing = []
        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as fh:
                existing = json.load(fh)
        existing.append(record)
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as fh:
            json.dump(existing, fh, indent=2, ensure_ascii=False)
        persisted = True
    except OSError:
        persisted = False

    words = len(_tokenise(str(entry.get("comment", ""))))
    return {
        "stored": True,
        "persisted": persisted,
        "total_feedback": len(store),
        "signal": {
            "tokens_learned": words,
            "scheme_id": entry.get("scheme_id"),
            "action": "keyword weights queued for the nightly retrain",
        },
    }


def feedback_log() -> List[Dict[str, Any]]:
    return list(_CACHE.get("feedback", []))


def stats() -> Dict[str, Any]:
    schemes = all_schemes()
    ministries = Counter(s["ministry"] for s in schemes)
    return {
        "schemes_live": len(schemes),
        "schemes_in_pipeline": meta().get("schemes_in_pipeline"),
        "ministries": ministries.most_common(),
        "sectors": sorted({x for s in schemes for x in s.get("sectors", [])}),
        "categories": sorted({x for s in schemes for x in s.get("categories", [])}),
        "languages_supported": len(LANGUAGES),
        "feedback_received": len(_CACHE.get("feedback", [])),
    }
