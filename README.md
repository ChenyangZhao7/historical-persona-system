# Historical Persona System

Historical speculation driven by historical figures' behavioural profiles.

Every figure in the database is encoded as a 10-dimensional behavioural vector
extracted from Wikipedia (and optionally from a source you supply). Those vectors
are then used to match a person against history, to find cross-civilisation
equivalents, and to generate era-grounded "what would they have done" narratives.

---

## The ten dimensions

| # | Dimension | 0.0 | 1.0 |
|---|-----------|-----|-----|
| 1 | reaction_to_oppression | endures silently | actively resists |
| 2 | group_dependency | lone wolf | relies on collective |
| 3 | principle_vs_interest | principle above all | interest above all |
| 4 | interpersonal_trust | highly open | deeply suspicious |
| 5 | change_orientation | preserve status quo | radical change |
| 6 | emotional_stability | calm and controlled | emotional and impulsive |
| 7 | core_motivation | idealism | survival / power |
| 8 | historical_mission | lives in present | mission-driven |
| 9 | response_to_injustice | accepts and adapts | anger and resistance |
| 10 | expression_style | silent and reserved | vocal and assertive |

Each dimension also carries a **confidence** score. Low-confidence dimensions
contribute less to matching, and are imputed from behaviourally similar figures
when a chat persona or a reconstruction needs a complete vector.

## Features

| Page | What it does |
|------|--------------|
| **Match** | Describe yourself → get your 10D profile → find your historical mirrors |
| **Reverse** | Cross-civilisation behavioural equivalents of any figure |
| **Predict** | Similar ancient and modern figures answer your question in the first person |
| **Reconstruct** | Describe an action → find behavioural kin → fabricate a period-appropriate account |
| **Chat** | Converse with a figure in character |
| **Database** | Add any Wikipedia figure, optionally with supplementary source text |
| **Graph** | The behavioural neighbourhood around one figure |
| **Locations** | Key places in a figure's life |
| **Relics** | Match an artefact description to figures by implied behaviour |
| **Map** | Client-side PCA projection of the whole corpus |
| **Benchmark** | Distribution of behavioural patterns across the corpus |

Matching supports 5 presets (Equal, Mission-first, Leadership, Idealist, Emotion)
plus per-dimension sliders, an IndexedDB vector cache, a draggable radar for live
re-matching, and a dark theme.

## Requirements

- Python **3.12** — 3.10–3.12 work; newer interpreters may not have wheels for the pinned numpy/scikit-learn
- Node.js **18+**
- An API key for your chosen LLM provider (below) — it is your key and your billing

### Choosing the LLM provider

The provider layer is a single module (`backend/services/llm.py`). Set
`LLM_PROVIDER` in `.env`:

| `LLM_PROVIDER` | Key | Model variable | Default model |
|---|---|---|---|
| `anthropic` (default) | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` | `claude-sonnet-4-6` |
| `deepseek` | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODEL` | `deepseek-chat` |

DeepSeek is called through its OpenAI-compatible REST endpoint with `requests`,
so switching providers needs no extra dependency. `DEEPSEEK_BASE_URL` defaults
to `https://api.deepseek.com`.

## Quick start

```bash
git clone <your-repo-url> historical-persona-system
cd historical-persona-system

# backend
python -m venv venv
#  macOS/Linux:  source venv/bin/activate
#  Windows:      venv\Scripts\activate
pip install -r backend/requirements.txt

# frontend
npm --prefix frontend install

# key
cp .env.example .env      # then put your key in .env
# or: export ANTHROPIC_API_KEY=sk-ant-...

npm start
```

Then open <http://localhost:5173>.

`npm start` runs the API on `:8000` and the Vite dev server on `:5173`. The dev
server proxies every backend route, so no CORS or base-URL configuration is
needed. `scripts/run-backend.mjs` finds the interpreter inside `venv/` on both
Windows and macOS/Linux.

For a production-style single process instead:

```bash
npm --prefix frontend run build     # emits frontend/dist
uvicorn main:app --app-dir backend --port 8000
```

FastAPI then serves the built frontend from the same origin.

## The dataset

`backend/data/historical.db` ships with **452 figures** and their vectors.

- **50** have a curated `era` and `period` (`ancient` or `modern`). These are the
  pool used by Predict, Reconstruct and the era benchmark.
- **402** were extracted on demand and carry `era = NULL`, `period = "unknown"`.
  They are matched and browseable, but deliberately **excluded** from anything
  that needs a century rather than guessed into one.

To grow the corpus:

```bash
cd backend
python -m uvicorn main:app --port 8000 &   # the importer talks to a running API
python bulk_import.py                      # ~4s per figure, resumable
```

Or use the **Database** page, which accepts extra source text for figures whose
Wikipedia article is thin.

### Cleaning the dataset

`backend/scripts/migrate_dataset.py` removes degenerate profiles (all-zero
vectors, flat vectors, empty confidence), collapses duplicate names and clears
the old `era = 0` placeholder. It is a dry run unless you pass `--apply`, and it
copies the database to `backend/data/backup/` first.

```bash
cd backend
python scripts/migrate_dataset.py           # show what would change
python scripts/migrate_dataset.py --apply   # do it
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze/` | Fetch Wikipedia (+ optional supplement) and extract a profile |
| GET | `/figures/` | List figures with vectors; `?evidence=false` for the slim payload |
| POST | `/figures/` | Create a figure from raw text |
| POST | `/match/` | Match a self-description to figures (accepts 10 weights) |
| GET | `/reverse/{name}` | Cross-civilisation equivalents |
| POST | `/predict/` | Ancient + modern figures answer your question |
| POST | `/reconstruct/` | Fabricated historical accounts for an action |
| POST | `/chat/` | Persona dialogue |
| POST | `/graph/` | Behavioural neighbourhood |
| POST | `/locations/` | Life geography |
| POST | `/relics/match/` | Artefact attribution |

Interactive docs at <http://localhost:8000/docs>.

## Project structure

```
historical-persona-system/
├── backend/
│   ├── main.py                 # FastAPI app, lifespan, static frontend
│   ├── database.py             # schema, indexes, connection helper
│   ├── env.py                  # tiny .env loader (no dependency)
│   ├── imputer.py              # missing-dimension reconstruction
│   ├── routers/                # one module per endpoint group
│   ├── services/               # extractor, matcher, predictor, reconstructor, chat …
│   ├── scripts/                # dataset migration
│   ├── tests/                  # pytest suite
│   └── data/historical.db      # 452 figures with vectors
├── frontend/
│   └── src/
│       ├── pages/              # one component per feature
│       ├── components/         # DraggableRadar, Skeleton
│       └── services/           # IndexedDB vector cache, client-side similarity
├── scripts/run-backend.mjs     # cross-platform dev launcher
└── render.yaml                 # single-service deploy
```

## Tests

```bash
pip install -r backend/requirements-dev.txt   # adds pytest to the venv
npm test                                       # same as: cd backend && python -m pytest tests -v
```

The suite covers the similarity maths, the imputer, LLM-output validation and the
HTTP layer with mocked dependencies. It never calls Anthropic.

## Cost and keys

Every extraction, match, prediction, reconstruction, chat turn and relic lookup
makes one or more Anthropic API calls, billed to whoever owns the key. A
prediction is 4 calls; a reconstruction is 3. There is no authentication on the
API — do not leave a funded key behind a public deployment.

## Deploy

`render.yaml` builds the frontend and runs a single Python service. Point
`DATABASE_PATH` at a mounted disk: on first start the app copies the bundled
database there, then writes to it.

## Licence

MIT — see [LICENSE](LICENSE).
