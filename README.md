# AI-Based Student Performance & Skill Gap Analyzer

A trainer-facing web application that combines academic and practical data into a single
AI performance score, then highlights each student's skill gaps and builds a personalised
learning plan.

Built for the **CITS – Computer Software Application (CSA)** project at
**NSTI Kanpur**, session **2026-27**.

- **Live app (Flask + ML):** deploy to Render — see [Deployment](#deployment)
- **Static demo (GitHub Pages):** `docs/` — works with zero backend
- **Stack:** Python · Flask · SQLAlchemy (SQLite/MySQL) · pandas · scikit-learn · HTML/CSS/JS

---

## Why this project

Training institutes usually review student performance across separate registers —
attendance, theory marks, practical marks, test scores, project work and technical
skills. Combining that by hand is slow, and trainers struggle to spot individual
weaknesses early.

This project automates the whole loop:

1. **Collect** academic, attendance, practical, test, project and skill data.
2. **Analyse** it with a trained RandomForest model plus a transparent rule score.
3. **Detect** skill gaps against expected levels.
4. **Recommend** the highest-priority skills to improve, with practice guidance.
5. **Present** everything in a dashboard trainers can scan in seconds.

## Features

| Feature | Description |
| --- | --- |
| AI performance score | RandomForest prediction blended with an explainable weighted score |
| Skill-gap detection | Every skill compared with its expected level; severity ranked |
| Personalised plan | Top three gaps mapped to concrete actions and resources |
| Cohort dashboard | Class average, at-risk count, weakest/strongest skills, top performers |
| Model transparency | Feature importance chart + MAE/R² shown in the UI |
| Student records | Add, view and delete students from the web UI or JSON API |
| Dual frontend | Server-rendered Flask dashboard **and** a dependency-free static demo |
| Portable database | SQLite out of the box, MySQL/Postgres via `DATABASE_URL` |
| Demo data | Eight realistic CSA students seeded on first run |

## Tech stack

| Layer | Tools |
| --- | --- |
| Backend | Python 3.10+, Flask, Flask-SQLAlchemy |
| Database | SQLite (default), MySQL 8 / MariaDB, PostgreSQL |
| ML / analytics | scikit-learn (RandomForestRegressor), pandas, NumPy, joblib |
| Frontend | Jinja2 templates, HTML5, modern CSS, vanilla JavaScript |
| Hosting | Render (Flask app) + GitHub Pages (`docs/` static demo) |
| Tooling | unittest, GitHub Actions, MIT license |

## Project structure

```
cits-skill-gap-analyzer/
├── app.py                  # Flask app factory, routes and JSON API
├── models.py               # SQLAlchemy Student model
├── seed.py                 # Demo students (seeded when the table is empty)
├── requirements.txt
├── Procfile / render.yaml  # Render deployment
├── ml/
│   ├── analyzer.py         # Feature engineering, model training, gap logic
│   └── train_model.py      # `python -m ml.train_model`
├── templates/              # Dashboard, student report, add form, 404
├── static/css/style.css
├── docs/                   # Static demo published on GitHub Pages
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── PROJECT_REPORT.md   # Full project report for submission
│   └── schema.sql          # MySQL schema
├── tests/test_analyzer.py
└── .github/workflows/      # Pages deploy + tests
```

## Quick start

```powershell
# 1. Clone and enter the project
git clone https://github.com/mukeshbtech989-png/cits-skill-gap-analyzer.git
cd cits-skill-gap-analyzer

# 2. Create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. (optional) train the model explicitly
python -m ml.train_model

# 5. run the app
python app.py
```

Open <http://127.0.0.1:5000>. Eight demo students are inserted automatically the first
time the app starts. The database lives at `data/cits.db` (git-ignored).

Other useful URLs:

- `http://127.0.0.1:5000/demo` — the static demo served by Flask
- `http://127.0.0.1:5000/api/students` — JSON API
- `http://127.0.0.1:5000/healthz` — health check

### Using MySQL instead of SQLite

```sql
CREATE DATABASE cits_skill_gap CHARACTER SET utf8mb4;
```

```powershell
$env:DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/cits_skill_gap"
python app.py
```

The schema is created automatically on first start. `docs/schema.sql` contains the
equivalent DDL if you prefer to create the table manually.

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | dev value | Flask session/flash signing |
| `DATABASE_URL` | `sqlite:///data/cits.db` | Any SQLAlchemy URL (MySQL/Postgres supported) |
| `FLASK_DEBUG` | `1` | Set to `0` in production |
| `PORT` | `5000` | Local server port |

## How the analysis works

**Inputs:** attendance, theory marks, practical marks, test score, project score and a
score for each tracked skill (Python, Java, MySQL, HTML/CSS, JavaScript, C/C++, MS Office,
Soft Skills).

**1. Rule score** — a weighted average (attendance 10%, theory 20%, practical 25%,
tests 20%, project 15%, average skill 10%). This keeps the result explainable.

**2. ML score** — a `RandomForestRegressor` trained on 1,500 deterministic synthetic
records (seeded, so results are reproducible). Features: the five academic metrics plus
average and minimum skill level. The model typically reaches **R² ≈ 0.96–0.98** and
**MAE ≈ 2 marks** on held-out data.

**3. Headline score** — `0.7 × ML score + 0.3 × rule score`, then mapped to a level:

| Score | Level |
| --- | --- |
| ≥ 85 | Excellent |
| 70–84.9 | Good |
| 55–69.9 | Average |
| < 55 | Needs Improvement |

**4. Gaps** — each skill below its expected level (60 by default) becomes a gap with
severity `critical` (≥ 20 points), `moderate` (10–19.9) or `minor` (< 10).

**5. Recommendations** — the three largest gaps map to concrete practice actions.

**6. Risk** — High when the score is below 55 or attendance is below 60%; Medium below
70 or attendance below 75%.

## JSON API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/students` | All students with their analysis |
| POST | `/api/students` | Create a student from JSON |
| GET | `/api/students/<id>` | One student + analysis |
| DELETE | `/api/students/<id>` | Delete a student |
| POST | `/api/analyze` | Analyse a payload without saving it |
| GET | `/api/cohort` | Cohort summary, feature importance, model metrics |
| GET | `/healthz` | Health check |

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Student",
    "attendance": 82,
    "theory_marks": 70,
    "practical_marks": 75,
    "test_score": 68,
    "project_score": 72,
    "skills": {"Python": 55, "Java": 74, "MySQL": 66, "HTML/CSS": 70,
               "JavaScript": 48, "C/C++": 58, "MS Office": 80, "Soft Skills": 72}
  }'
```

## Tests

```powershell
python -m unittest discover -s tests -v
```

The suite checks grade bands, score ranges, gap detection, recommendation coverage,
cohort aggregation and model quality.

## Deployment

### 1. Push to GitHub

```powershell
git init
git add .
git commit -m "Initial commit: CITS skill gap analyzer"
git branch -M main
git remote add origin https://github.com/mukeshbtech989-png/cits-skill-gap-analyzer.git
git push -u origin main
```

### 2. Static demo on GitHub Pages (free, no server)

1. Repository **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. The workflow in `.github/workflows/pages.yml` publishes `docs/` automatically
   on every push that touches `docs/`.

The demo URL is `https://mukeshbtech989-png.github.io/cits-skill-gap-analyzer/`
(`REPO_URL` in `docs/app.js` is already set to the repository).

> GitHub Pages only serves static files. That is why the interactive demo is written in
> vanilla JavaScript — the Flask API and ML model need a real Python host.

### 3. Full Flask app on Render (free tier)

**Option A — Blueprint:** Render Dashboard → **New → Blueprint** → select the repo.
`render.yaml` configures everything (build, start command, health check).

**Option B — Manual:** New → Web Service → connect the repo →

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| Health check path | `/healthz` |

Render's free web services use an ephemeral disk, so the SQLite database is recreated
and re-seeded on each deploy. For persistent records, attach a managed MySQL/Postgres
database and set `DATABASE_URL` (see `render.yaml` for the commented block).

### 4. Screenshots for your report

Run the app locally, then capture the dashboard, a student report and the static demo.
Place them in `docs/screenshots/` and reference them from the report.

## Roadmap

- [ ] CSV/Excel import for bulk student data
- [ ] Trainer login with per-batch views
- [ ] PDF report export per student
- [ ] Retraining from real (anonymised) institute data
- [ ] Email/WhatsApp alerts for high-risk students

## Project details

| Field | Value |
| --- | --- |
| Project title | AI-Based Student Performance & Skill Gap Analyzer |
| Student | Mukesh Kumar |
| Trade | Computer Software Application (CSA) |
| Course | CITS |
| Institute | NSTI Kanpur |
| Session | 2026-27 |

## License

Released under the [MIT License](LICENSE).

## Acknowledgements

- NSTI Kanpur faculty and CITS CSA trainers
- scikit-learn, Flask and pandas documentation
- Open-source community for the tooling that made this project possible
