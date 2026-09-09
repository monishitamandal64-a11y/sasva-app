"""Vercel serverless entry point for the SASVA API.

Vercel maps every request to this file (see vercel.json) and serves the ASGI
app it exposes. The Streamlit client cannot run on Vercel, it needs a long
lived process, so deploy the client on Streamlit Cloud or Render and point
SASVA_API_URL at this deployment.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.main import app  # noqa: E402

# Vercel's Python runtime looks for a module level ASGI callable named `app`.
__all__ = ["app"]
