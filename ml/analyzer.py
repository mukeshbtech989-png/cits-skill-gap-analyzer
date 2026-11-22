"""AI/ML engine for the CITS Student Performance & Skill Gap Analyzer.

The engine does three things:

1. Predicts an overall performance score from attendance, theory, practical,
   test, project and skill data using a RandomForestRegressor.
2. Detects skill gaps by comparing every skill score against the expected
   level for that skill.
3. Produces personalised, human-readable recommendations.

The model is trained on a deterministic synthetic dataset (seeded, so the
numbers are reproducible) the first time it is needed and cached to
``ml/model.joblib``.  Run ``python -m ml.train_model`` to retrain on demand.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.joblib"
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------

#: Expected minimum level (out of 100) for every tracked skill.
SKILL_CATALOG: dict[str, int] = {
    "Python": 60,
    "Java": 60,
    "MySQL": 60,
    "HTML/CSS": 60,
    "JavaScript": 60,
    "C/C++": 60,
    "MS Office": 60,
    "Soft Skills": 60,
}

#: Feature vector used by the model, in this exact order.
FEATURES: list[str] = [
    "attendance",
    "theory_marks",
    "practical_marks",
    "test_score",
    "project_score",
    "avg_skill",
    "min_skill",
]

#: Weights used for the transparent rule-based score.
WEIGHTS: dict[str, float] = {
    "attendance": 0.10,
    "theory_marks": 0.20,
    "practical_marks": 0.25,
    "test_score": 0.20,
    "project_score": 0.15,
    "avg_skill": 0.10,
}

LEVEL_BANDS: list[tuple[float, str]] = [
    (85.0, "Excellent"),
    (70.0, "Good"),
    (55.0, "Average"),
    (0.0, "Needs Improvement"),
]

RECOMMENDATIONS: dict[str, dict[str, str]] = {
    "Python": {
        "action": "Practice Python fundamentals: loops, functions, OOP, file handling and small console projects.",
        "resource": "Python official tutorial · W3Schools Python · HackerRank Python track",
    },
    "Java": {
        "action": "Revise core Java: classes, inheritance, interfaces, exception handling and collections.",
        "resource": "Java Tutorials (Oracle) · 'Java: The Complete Reference' by Herbert Schildt",
    },
    "MySQL": {
        "action": "Practise SQL queries: SELECT/JOIN, GROUP BY, sub-queries and normalisation exercises.",
        "resource": "MySQL Documentation · SQLBolt · W3Schools SQL",
    },
    "HTML/CSS": {
        "action": "Build two responsive pages using semantic HTML, Flexbox and CSS Grid.",
        "resource": "MDN Web Docs · freeCodeCamp Responsive Web Design",
    },
    "JavaScript": {
        "action": "Practise DOM manipulation, events, arrays/objects and basic fetch-based mini apps.",
        "resource": "MDN JavaScript Guide · JavaScript.info",
    },
    "C/C++": {
        "action": "Strengthen pointers, arrays, structures and function decomposition with daily coding drills.",
        "resource": "GeeksforGeeks C/C++ tutorials · CodeChef practice problems",
    },
    "MS Office": {
        "action": "Complete practical tasks in Word, Excel (formulas, charts) and PowerPoint.",
        "resource": "Microsoft Office training centre · NSTI practical assignments",
    },
    "Soft Skills": {
        "action": "Join group discussions, mock interviews and short technical presentations each week.",
        "resource": "NSTI employability module · Toastmasters style practice sessions",
    },
}

DEFAULT_RECOMMENDATION = {
    "action": "Revise the basics, solve practice questions and take a short self-test every week.",
    "resource": "Ask your trainer for a practice sheet on this topic.",
}

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def grade(score: float) -> str:
    """Map a 0-100 score to a performance band."""
    for cut_off, label in LEVEL_BANDS:
        if score >= cut_off:
            return label
    return "Needs Improvement"


def _clamp(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(100.0, number))


def _clean_skills(raw: dict[str, Any] | None) -> dict[str, float]:
    """Return a skill -> score map (0-100).

    Unknown skills are still tracked, using the default expectation.  Non-dict
    input (for example a list from a malformed API call) is ignored.
    """
    if not isinstance(raw, dict):
        return {}
    cleaned: dict[str, float] = {}
    for skill, score in raw.items():
        name = str(skill).strip()
        if name:
            cleaned[name] = _clamp(score)
    return cleaned


def _feature_row(record: dict[str, Any]) -> tuple[list[float], dict[str, float], float, float]:
    skills = _clean_skills(record.get("skills"))
    if not skills:
        skills = {skill: 0.0 for skill in SKILL_CATALOG}
    metrics = [_clamp(record.get(key)) for key in (
        "attendance",
        "theory_marks",
        "practical_marks",
        "test_score",
        "project_score",
    )]
    avg_skill = float(np.mean(list(skills.values())))
    min_skill = float(np.min(list(skills.values())))
    return [*metrics, avg_skill, min_skill], skills, avg_skill, min_skill


def _rule_score(metrics: list[float], avg_skill: float) -> float:
    attendance, theory, practical, test, project = metrics
    return (
        WEIGHTS["attendance"] * attendance
        + WEIGHTS["theory_marks"] * theory
        + WEIGHTS["practical_marks"] * practical
        + WEIGHTS["test_score"] * test
        + WEIGHTS["project_score"] * project
        + WEIGHTS["avg_skill"] * avg_skill
    )


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def _synthetic_frame(n_samples: int = 1500, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Create a realistic, deterministic training set.

    A latent "ability" factor drives every measured component so the
    correlations look like real institute data, then the target score is
    produced with the documented weighting plus a little noise.
    """
    rng = np.random.default_rng(seed)
    ability = rng.normal(0.0, 1.0, n_samples)

    attendance = np.clip(78 + 10 * ability + rng.normal(0, 7, n_samples), 40, 100)
    theory = np.clip(65 + 14 * ability + rng.normal(0, 9, n_samples), 10, 100)
    practical = np.clip(68 + 15 * ability + rng.normal(0, 9, n_samples), 10, 100)
    test = np.clip(64 + 15 * ability + rng.normal(0, 10, n_samples), 5, 100)
    project = np.clip(70 + 14 * ability + rng.normal(0, 10, n_samples), 5, 100)
    avg_skill = np.clip(62 + 16 * ability + rng.normal(0, 10, n_samples), 5, 100)
    min_skill = np.clip(avg_skill - rng.uniform(2, 18, n_samples), 0, 100)

    overall = np.clip(
        WEIGHTS["attendance"] * attendance
        + WEIGHTS["theory_marks"] * theory
        + WEIGHTS["practical_marks"] * practical
        + WEIGHTS["test_score"] * test
        + WEIGHTS["project_score"] * project
        + WEIGHTS["avg_skill"] * avg_skill
        + rng.normal(0, 2.2, n_samples),
        0,
        100,
    )

    return pd.DataFrame(
        {
            "attendance": attendance,
            "theory_marks": theory,
            "practical_marks": practical,
            "test_score": test,
            "project_score": project,
            "avg_skill": avg_skill,
            "min_skill": min_skill,
            "overall": overall,
        }
    )


def _train() -> dict[str, Any]:
    frame = _synthetic_frame()
    x = frame[FEATURES]
    y = frame["overall"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=RANDOM_STATE
    )

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=9,
        min_samples_leaf=3,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    return {
        "model": model,
        "metrics": {
            "mae": round(float(mean_absolute_error(y_test, predictions)), 3),
            "r2": round(float(r2_score(y_test, predictions)), 4),
            "samples": int(len(frame)),
        },
        "importances": {
            feature: round(float(value), 4)
            for feature, value in zip(FEATURES, model.feature_importances_)
        },
    }


_MODEL: dict[str, Any] | None = None


def get_model() -> dict[str, Any]:
    """Load the cached model or train a fresh one."""
    global _MODEL
    if _MODEL is None:
        if MODEL_PATH.exists():
            try:
                _MODEL = joblib.load(MODEL_PATH)
            except Exception:  # corrupted / incompatible artefact
                _MODEL = None
        if _MODEL is None:
            _MODEL = _train()
            joblib.dump(_MODEL, MODEL_PATH)
    return _MODEL


def retrain() -> dict[str, Any]:
    """Force a retrain and refresh the cached artefact."""
    global _MODEL
    _MODEL = _train()
    joblib.dump(_MODEL, MODEL_PATH)
    return _MODEL


def model_metrics() -> dict[str, Any]:
    return dict(get_model()["metrics"])


def feature_importance() -> list[dict[str, Any]]:
    labels = {
        "attendance": "Attendance",
        "theory_marks": "Theory marks",
        "practical_marks": "Practical marks",
        "test_score": "Test scores",
        "project_score": "Project work",
        "avg_skill": "Average skill level",
        "min_skill": "Weakest skill",
    }
    importances = get_model()["importances"]
    ordered = sorted(importances.items(), key=lambda item: item[1], reverse=True)
    return [
        {
            "feature": key,
            "label": labels.get(key, key),
            "importance": round(value * 100, 1),
        }
        for key, value in ordered
    ]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def _severity(gap: float) -> str:
    if gap >= 20:
        return "critical"
    if gap >= 10:
        return "moderate"
    return "minor"


def analyze_many(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Analyse a batch of student records in one model call."""
    records = list(records)
    if not records:
        return []

    rows: list[list[float]] = []
    meta: list[tuple[dict[str, Any], dict[str, float], float, float, list[float]]] = []
    for record in records:
        features, skills, avg_skill, min_skill = _feature_row(record)
        rows.append(features)
        meta.append((record, skills, avg_skill, min_skill, features[:5]))

    predictions = get_model()["model"].predict(pd.DataFrame(rows, columns=FEATURES))

    results: list[dict[str, Any]] = []
    for (record, skills, avg_skill, min_skill, metrics), predicted in zip(meta, predictions):
        predicted_score = round(float(predicted), 1)
        rule_score = round(_rule_score(metrics, avg_skill), 1)
        # Blend the learned model with the transparent rule score so the
        # headline number stays explainable to trainers.
        overall = round(0.7 * predicted_score + 0.3 * rule_score, 1)

        gaps: list[dict[str, Any]] = []
        strengths: list[dict[str, Any]] = []
        for skill, score in skills.items():
            expected = SKILL_CATALOG.get(skill, 60)
            score = round(float(score), 1)
            if score < expected:
                gaps.append(
                    {
                        "skill": skill,
                        "score": score,
                        "expected": expected,
                        "gap": round(expected - score, 1),
                        "severity": _severity(expected - score),
                    }
                )
            if score >= 75:
                strengths.append({"skill": skill, "score": score})

        gaps.sort(key=lambda item: item["gap"], reverse=True)
        strengths.sort(key=lambda item: item["score"], reverse=True)

        recommendations = []
        for gap in gaps[:3]:
            tip = RECOMMENDATIONS.get(gap["skill"], DEFAULT_RECOMMENDATION)
            recommendations.append(
                {
                    "skill": gap["skill"],
                    "current": gap["score"],
                    "target": gap["expected"],
                    "priority": gap["severity"],
                    "action": tip["action"],
                    "resource": tip["resource"],
                }
            )
        if not recommendations:
            recommendations.append(
                {
                    "skill": "Overall",
                    "current": overall,
                    "target": 85,
                    "priority": "stretch",
                    "action": "All tracked skills are at or above the expected level. "
                    "Move on to advanced topics and real project work.",
                    "resource": "Ask your trainer for an advanced assignment.",
                }
            )

        attendance = metrics[0]
        if overall < 55 or attendance < 60:
            risk = "High"
        elif overall < 70 or attendance < 75:
            risk = "Medium"
        else:
            risk = "Low"

        name = str(record.get("name") or "This student").strip()
        level = grade(overall)
        article = "an" if level[0].lower() in "aeiou" else "a"
        strong_text = ", ".join(item["skill"] for item in strengths[:3]) or "no skill above 75 yet"
        gap_text = ", ".join(item["skill"] for item in gaps[:3]) or "no skill below the expected level"
        summary = (
            f"{name} is performing at {article} {level.lower()} level with an AI score of "
            f"{overall}/100. Strongest areas: {strong_text}. "
            f"Priority improvement areas: {gap_text}."
        )

        results.append(
            {
                "id": record.get("id"),
                "roll_no": record.get("roll_no"),
                "name": record.get("name"),
                "overall_score": overall,
                "predicted_score": predicted_score,
                "rule_score": rule_score,
                "level": level,
                "risk": risk,
                "skills": {skill: round(float(score), 1) for skill, score in skills.items()},
                "skill_avg": round(avg_skill, 1),
                "min_skill": round(min_skill, 1),
                "components": {
                    "attendance": round(metrics[0], 1),
                    "theory_marks": round(metrics[1], 1),
                    "practical_marks": round(metrics[2], 1),
                    "test_score": round(metrics[3], 1),
                    "project_score": round(metrics[4], 1),
                },
                "gaps": gaps,
                "strengths": strengths,
                "recommendations": recommendations,
                "summary": summary,
            }
        )
    return results


def analyze_student(record: dict[str, Any]) -> dict[str, Any]:
    return analyze_many([record])[0]


def cohort_summary(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate class-level insights for the dashboard."""
    if not analyses:
        return {
            "total": 0,
            "average_score": 0.0,
            "at_risk": 0,
            "level_counts": {},
            "skills": [],
            "weakest": [],
            "strongest": [],
            "top_students": [],
        }

    scores = [item["overall_score"] for item in analyses]
    level_counts = Counter(item["level"] for item in analyses)

    skill_totals: dict[str, float] = {}
    skill_below: Counter = Counter()
    for item in analyses:
        for skill, score in item["skills"].items():
            skill_totals[skill] = skill_totals.get(skill, 0.0) + score
            expected = SKILL_CATALOG.get(skill, 60)
            if score < expected:
                skill_below[skill] += 1

    skill_rows = [
        {
            "skill": skill,
            "average": round(total / len(analyses), 1),
            "expected": SKILL_CATALOG.get(skill, 60),
            "below_count": int(skill_below.get(skill, 0)),
            "below_pct": round(100 * skill_below.get(skill, 0) / len(analyses), 1),
        }
        for skill, total in skill_totals.items()
    ]
    by_average = sorted(skill_rows, key=lambda row: row["average"])

    top = sorted(analyses, key=lambda item: item["overall_score"], reverse=True)[:3]

    return {
        "total": len(analyses),
        "average_score": round(sum(scores) / len(scores), 1),
        "at_risk": sum(1 for item in analyses if item["risk"] == "High"),
        "level_counts": dict(level_counts),
        "skills": by_average,
        "weakest": by_average[:3],
        "strongest": list(reversed(by_average[-3:])),
        "top_students": [
            {"name": item["name"], "roll_no": item["roll_no"], "score": item["overall_score"]}
            for item in top
        ],
    }
