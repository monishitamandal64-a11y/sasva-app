# SASVA · SchemeSetu

**AI driven scheme matching for marginalised entrepreneurs**

Team NEXUS · Smart India Hackathon 2026 · Problem ID **SIH26092** · Theme Smart Automation · Team ID **IIC_TMSL_P9_S10**

A woman running a pickle unit in a village is eligible for four central schemes and hears about none of them. SASVA takes a five field profile, scores every scheme in the catalogue on four auditable weights, and hands back a ranked shortlist with the documents, the steps and the portal link. Each card leaves the app as a real PDF, a WhatsApp message or spoken audio, so a CSC operator can serve someone who does not read English.

---

## 1. Architecture

```
┌────────────────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│  CLIENT  ·  Streamlit      │  ───────────────────►   │  SERVER  ·  FastAPI      │
│  client/app.py             │  ◄───────────────────   │  server/main.py          │
│  11 features, mobile ready │      /match /schemes    │  REST + OpenAPI docs     │
└────────────────────────────┘      /feedback /sync    └────────────┬─────────────┘
              │                                                     │
              │  falls back to the local engine if the API is down  │
              └──────────────────────► server/engine.py ◄───────────┘
                                       scoring · LiteVectorIndex
                                                │
                                       data/schemes.json  (14 live, 312 in pipeline)
```

The client never hard fails. If the server is unreachable it imports the same
engine in process, so a demo on a hotel wifi still works.

## 2. Feature map

| # | Feature | Where |
|---|---|---|
| I | Header card: emblem, SASVA mark, Home / About Us | `client/app.py` → `.sasva-header` |
| II | Floating welcome card, gradient `#667eea → #764ba2`, `floatUpDown 3.5s`, 3 language buttons | `.welcome-card` |
| III | Auto feed strip with last sync and next sync, Admin only force re-sync | `fetch_sync()`, `POST /resync` |
| IV | Login, roles User / CSC Operator / Admin, profile in `session_state`, Admin dataframe | sidebar + dashboard block |
| V | Search box with `⏎ ENTER` button and five quick chips | `search_in`, `enter_btn` |
| VI | Gradient scheme card, eligibility and ministry badges, AI match breakdown bars | `.scheme-card`, `.bd-row` |
| VII | Five actions per card: Save, real PDF, WhatsApp, Voice, Track Success | `build_pdf`, `build_voice`, `whatsapp_link` |
| VIII | Expander with numbered application steps and the document list | `st.expander` per card |
| IX | Success tracking with a progress bar per tracked application | `session_state.tracking` |
| X | Feedback text area feeding the self learning loop | `POST /feedback` |
| XI | Notification preference: None / WhatsApp / SMS / Email | `notify_pick` |

## 3. Scoring, and why it is defensible

Fixed weights, printed on every card, summing to 100:

| Component | Weight | What earns full marks |
|---|---|---|
| Category | 40 | The scheme is reserved for your category, or reserved for women and you are a woman. Merely being open to everyone scores 0.72 of the weight. |
| Funding | 30 | Your requirement sits inside the band, and the band is tight. A 1 lakh to 5 crore band that happens to contain your number is capped at 0.55. |
| Sector | 15 | The scheme is specialised in your sector. Generalist schemes score 0.70. |
| Region | 15 | The scheme is exclusive to your area type. Schemes covering both score 0.80. |

Hard blockers (women only, category restricted, age, wrong area type) cap the
score at 45 and print the reason on the card instead of hiding the scheme.

Sample output, SC woman, rural food unit, needs Rs 3 lakh:

```
89%  DAY-NRLM      Strong match      cat 40.0  fund 23.2  sector 10.5  region 15.0
82%  SC-ST Hub     Strong match      cat 40.0  fund 19.7  sector 10.5  region 12.0
78%  PMFME         Worth applying    cat 28.8  fund 24.9  sector 12.8  region 12.0
74%  PMEGP         Worth applying    cat 28.8  fund 23.2  sector 10.5  region 12.0
```

General male, urban trader, needs Rs 40 thousand, gets PM SVANidhi at 87% and
DAY-NRLM at 45% with the reason "reserved for women applicants". PwD male
manufacturer needing Rs 25 lakh gets NHFDC Swavalamban at 84%.

## 4. Data

`data/schemes.json` carries 14 central schemes: PMEGP, PM MUDRA, Stand-Up
India, PMFME, DAY-NULM SEP, PM SVANidhi, PM Vishwakarma, DAY-NRLM, NHFDC
Swavalamban, CGTMSE, Startup India Seed Fund, Mahila Coir Yojana, National
SC-ST Hub, ASPIRE.

Every amount was copied from the public scheme page at collection time. The
`meta.accuracy_note` field says so, and the footer and every generated PDF
repeat it. **Verify on the ministry portal before any beneficiary facing use.**

Scaling past 300 schemes: `server/engine.py` holds `LiteVectorIndex`, a pure
Python TF-IDF cosine index with a vector database shaped interface. Keep the
`add()` and `search()` signatures and swap the internals for Chroma, FAISS or
pgvector. Nothing upstream changes.

## 5. Run locally

```bash
git clone <your-repo> sasva && cd sasva
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Two terminals:

```bash
# terminal 1 - server
uvicorn server.main:app --reload --port 8000     # docs at http://localhost:8000/docs

# terminal 2 - client
streamlit run client/app.py                      # app at http://localhost:8501
```

One terminal:

```bash
chmod +x start.sh && ./start.sh                  # runs both, client on 8501
```

Client only, no server:

```bash
streamlit run client/app.py    # sidebar shows "offline, using local engine"
```

Docker:

```bash
docker build -t sasva .
docker run -p 8501:8501 -p 8000:8000 sasva
```

## 6. Deploy

### Render, one Docker service (recommended, client + server together)

1. Push this repo to GitHub.
2. Render dashboard → **New** → **Web Service** → connect the repo.
3. Runtime **Docker**, plan Free, region Singapore.
4. Health check path `/_stcore/health`.
5. Environment variable `API_PORT = 8000`. Do not set `PORT`, Render injects it and `start.sh` binds Streamlit to it.
6. Create Web Service. First build takes about 4 minutes.

Or commit `render.yaml` and use **New → Blueprint**, which reads the same settings.

### Render, two services (cleaner scaling)

| Service | Type | Start command | Env |
|---|---|---|---|
| `sasva-api` | Web (Python) | `uvicorn server.main:app --host 0.0.0.0 --port $PORT` | — |
| `sasva-client` | Web (Python) | `streamlit run client/app.py --server.port $PORT --server.address 0.0.0.0` | `SASVA_API_URL = https://sasva-api.onrender.com` |

Build command for both: `pip install -r requirements.txt`.

### Streamlit Community Cloud (client only, zero config)

1. Push to GitHub, go to share.streamlit.io → **New app**.
2. Main file path `client/app.py`, Python 3.11.
3. Deploy. With no `SASVA_API_URL` secret the client uses the bundled engine and every feature still works.
4. To point it at a hosted API, add to **Secrets**, then read it as an env var:
   `SASVA_API_URL = "https://sasva-api.onrender.com"`

### Vercel (server only)

Streamlit needs a long lived process, so Vercel hosts the API and Streamlit
Cloud or Render hosts the client. `api/index.py` and `vercel.json` are included.
Vercel installs the root `requirements.txt`; for a lean function keep only
`fastapi` and `uvicorn` in it on that branch, since the server needs nothing else.

```bash
npm i -g vercel && vercel --prod
```

Then set `SASVA_API_URL` on the client to the Vercel URL.

## 7. API

Interactive docs at `/docs`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/schemes?q=women&limit=10` | Keyword and semantic search |
| GET | `/schemes/{id}` | One scheme, 404 if unknown |
| POST | `/match` | Profile in, scored and ranked schemes out |
| POST | `/feedback` | Store feedback, returns the learning signal |
| GET | `/feedback` | Session feedback log |
| GET | `/sync` | Last and next feed timestamps |
| POST | `/resync?role=Admin` | Force re-sync, 403 for any other role |
| GET | `/stats` | Catalogue counts by ministry, sector, category |
| GET | `/languages` | The 22 language roadmap |

```bash
curl -X POST localhost:8000/match -H 'Content-Type: application/json' -d '{
  "profile": {"category":"SC","gender":"Female","age":32,
              "sector":"Food Processing","funding_need":300000,"region":"Rural"},
  "query": "food", "limit": 3}'
```

## 8. What was tested

Verified in a clean Python 3.12 environment with the pinned requirements:

- All ten endpoints, including the 403 on `/resync?role=User` and the 404 on an unknown scheme id.
- The Streamlit app driven headlessly through `streamlit.testing.v1.AppTest`: language switch, search, quick chips, save, track, feedback submit, notification change, Admin login, force re-sync, About page. Zero exceptions.
- PDF generation for all twelve rendered cards. Output is a valid `%PDF-1.3` file with a proper trailer, and non latin-1 characters such as the rupee sign are transliterated so `fpdf2` never crashes.
- Offline mode with the server stopped: 12 cards, working search and working feedback.
- `start.sh` booting both processes, server healthy on 8000 and client returning HTTP 200 on 8501.

Not tested here: the Docker image build, because no Docker daemon was available in the build sandbox, and the gTTS voice call, which needs outbound internet at runtime and degrades to a warning message when blocked.

## 9. Layout

```
sasva/
├── client/app.py           Streamlit client, all 11 features
├── server/
│   ├── main.py             FastAPI app and schemas
│   ├── engine.py           scoring, search, LiteVectorIndex, feedback
│   └── __init__.py
├── data/schemes.json       14 schemes with provenance note
├── api/index.py            Vercel entry point for the server
├── .streamlit/config.toml  theme and headless server config
├── requirements.txt        streamlit, pandas, gTTS, fpdf2, fastapi, uvicorn
├── Dockerfile              single image, both processes
├── start.sh                launches server then client
├── render.yaml             Render blueprint
└── README.md
```

## 10. Roadmap

1. Real crawler for myscheme.gov.in and the state portals, replacing the simulated nightly sync.
2. Swap `LiteVectorIndex` for pgvector and take the catalogue past 300 schemes with state level filtering.
3. Aadhaar based DigiLocker document pull, so the document checklist becomes a document upload.
4. WhatsApp Business API for the notification channel instead of a share link.
5. Feedback weights actually retrained nightly, with a human review queue for scheme data corrections.
