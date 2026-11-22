"""AI-Based Student Performance & Skill Gap Analyzer.

CITS · Computer Software Application (CSA) · NSTI Kanpur · Session 2026-27
Author: Mukesh Kumar

Run locally::

    python app.py

The app exposes an HTML dashboard plus a small JSON API (see README.md).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from ml import analyzer
from models import DEFAULT_BATCH, DEFAULT_TRADE, Student, db
from seed import seed_if_empty

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"

SKILL_KEYS: list[str] = list(analyzer.SKILL_CATALOG.keys())


def skill_field(skill: str) -> str:
    """Stable HTML form field name for a skill (handles '/', '+' and spaces)."""
    return "skill_" + "".join(ch if ch.isalnum() else "_" for ch in skill)


def _clamp(raw: Any, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(100.0, value))


def _student_payload(source: Mapping[str, Any]) -> dict[str, Any]:
    """Normalise a form dict or JSON body into validated student fields."""

    def first(*names: str, default: Any = None) -> Any:
        for name in names:
            if name in source and source.get(name) not in (None, ""):
                return source.get(name)
        return default

    skills: dict[str, float] = {}
    raw_skills = source.get("skills")
    if isinstance(raw_skills, dict):
        for key, value in raw_skills.items():
            if key in analyzer.SKILL_CATALOG:
                skills[key] = _clamp(value)
    else:
        for key in SKILL_KEYS:
            value = source.get(skill_field(key))
            if value not in (None, ""):
                skills[key] = _clamp(value)

    return {
        "roll_no": str(first("roll_no", "roll", default="")).strip(),
        "name": str(first("name", default="")).strip(),
        "trade": str(first("trade", default=DEFAULT_TRADE)).strip() or DEFAULT_TRADE,
        "batch": str(first("batch", default=DEFAULT_BATCH)).strip() or DEFAULT_BATCH,
        "email": (str(first("email", default="")).strip() or None),
        "attendance": _clamp(first("attendance", default=0)),
        "theory_marks": _clamp(first("theory_marks", default=0)),
        "practical_marks": _clamp(first("practical_marks", default=0)),
        "test_score": _clamp(first("test_score", default=0)),
        "project_score": _clamp(first("project_score", default=0)),
        "skills": skills,
    }


def _database_url() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        return "sqlite:///" + (DATA_DIR / "cits.db").as_posix()
    if url.startswith("mysql://"):
        url = "mysql+pymysql://" + url[len("mysql://") :]
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def register_routes(app: Flask) -> None:
    # ------------------------------------------------------------- pages
    @app.get("/")
    def dashboard():
        students = Student.query.order_by(Student.name.asc()).all()
        analyses = analyzer.analyze_many([student.to_record() for student in students])
        rows = [
            {"student": student, "analysis": analysis}
            for student, analysis in zip(students, analyses)
        ]
        rows.sort(key=lambda row: row["analysis"]["overall_score"], reverse=True)
        return render_template(
            "index.html",
            rows=rows,
            summary=analyzer.cohort_summary(analyses),
            importance=analyzer.feature_importance(),
            metrics=analyzer.model_metrics(),
        )

    @app.get("/students/new")
    def add_student():
        return render_template(
            "new_student.html",
            skill_keys=SKILL_KEYS,
            catalog=analyzer.SKILL_CATALOG,
            form={},
        )

    @app.post("/students")
    def create_student():
        payload = _student_payload(request.form)
        if not payload["name"] or not payload["roll_no"]:
            flash("Roll number and student name are required.", "error")
            return (
                render_template(
                    "new_student.html",
                    skill_keys=SKILL_KEYS,
                    catalog=analyzer.SKILL_CATALOG,
                    form=request.form,
                ),
                400,
            )
        if Student.query.filter_by(roll_no=payload["roll_no"]).first():
            flash(f"Roll number {payload['roll_no']} already exists.", "error")
            return (
                render_template(
                    "new_student.html",
                    skill_keys=SKILL_KEYS,
                    catalog=analyzer.SKILL_CATALOG,
                    form=request.form,
                ),
                409,
            )

        student = Student(**{key: value for key, value in payload.items() if key != "skills"})
        student.skills = payload["skills"]
        db.session.add(student)
        db.session.commit()
        flash(f"{student.name} added successfully.", "success")
        return redirect(url_for("student_detail", student_id=student.id))

    @app.get("/students/<int:student_id>")
    def student_detail(student_id: int):
        student = db.session.get(Student, student_id)
        if student is None:
            abort(404)
        analysis = analyzer.analyze_student(student.to_record())
        return render_template(
            "student_detail.html",
            student=student,
            analysis=analysis,
            catalog=analyzer.SKILL_CATALOG,
            catalog_expected=60,
        )

    @app.post("/students/<int:student_id>/delete")
    def delete_student(student_id: int):
        student = db.session.get(Student, student_id)
        if student is None:
            abort(404)
        name = student.name
        db.session.delete(student)
        db.session.commit()
        flash(f"{name} removed from the records.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/demo")
    def demo():
        """Serve the dependency-free static demo (also published on GitHub Pages)."""
        return send_from_directory(DOCS_DIR, "index.html")

    # --------------------------------------------------------------- API
    @app.get("/api/health")
    @app.get("/healthz")
    def api_health():
        return jsonify({"status": "ok", "model": analyzer.model_metrics()})

    @app.get("/api/students")
    def api_students():
        students = Student.query.order_by(Student.name.asc()).all()
        analyses = analyzer.analyze_many([student.to_record() for student in students])
        return jsonify(
            {
                "count": len(students),
                "students": [
                    student.to_dict(analysis)
                    for student, analysis in zip(students, analyses)
                ],
            }
        )

    @app.post("/api/students")
    def api_create_student():
        payload = _student_payload(request.get_json(silent=True) or {})
        if not payload["name"] or not payload["roll_no"]:
            return jsonify({"error": "roll_no and name are required"}), 400
        if Student.query.filter_by(roll_no=payload["roll_no"]).first():
            return jsonify({"error": f"roll_no {payload['roll_no']} already exists"}), 409

        student = Student(**{key: value for key, value in payload.items() if key != "skills"})
        student.skills = payload["skills"]
        db.session.add(student)
        db.session.commit()
        analysis = analyzer.analyze_student(student.to_record())
        return jsonify(student.to_dict(analysis)), 201

    @app.get("/api/students/<int:student_id>")
    def api_student(student_id: int):
        student = db.session.get(Student, student_id)
        if student is None:
            return jsonify({"error": "student not found"}), 404
        return jsonify(student.to_dict(analyzer.analyze_student(student.to_record())))

    @app.delete("/api/students/<int:student_id>")
    def api_delete_student(student_id: int):
        student = db.session.get(Student, student_id)
        if student is None:
            return jsonify({"error": "student not found"}), 404
        db.session.delete(student)
        db.session.commit()
        return jsonify({"deleted": student_id})

    @app.post("/api/analyze")
    def api_analyze():
        payload = _student_payload(request.get_json(silent=True) or {})
        return jsonify(analyzer.analyze_student(payload))

    @app.get("/api/cohort")
    def api_cohort():
        students = Student.query.order_by(Student.name.asc()).all()
        analyses = analyzer.analyze_many([student.to_record() for student in students])
        return jsonify(
            {
                "summary": analyzer.cohort_summary(analyses),
                "feature_importance": analyzer.feature_importance(),
                "model": analyzer.model_metrics(),
            }
        )

    # ------------------------------------------------------------ errors
    @app.errorhandler(404)
    def not_found(error):  # noqa: ARG001
        if request.path.startswith("/api/"):
            return jsonify({"error": "not found"}), 404
        return render_template("404.html"), 404


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "cits-skill-gap-dev-secret"),
        SQLALCHEMY_DATABASE_URI=_database_url(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
    )

    DATA_DIR.mkdir(exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_if_empty()
        # Warm the model so the first dashboard request does not pay the
        # training cost.
        analyzer.get_model()

    app.jinja_env.globals.update(grade=analyzer.grade, skill_field=skill_field)
    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
    )
