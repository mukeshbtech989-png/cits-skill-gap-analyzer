"""SQLAlchemy models for the CITS Skill Gap Analyzer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

DEFAULT_TRADE = "Computer Software Application (CSA)"
DEFAULT_BATCH = "2026-27"


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    trade = db.Column(db.String(80), nullable=False, default=DEFAULT_TRADE)
    batch = db.Column(db.String(40), nullable=False, default=DEFAULT_BATCH)
    email = db.Column(db.String(160))

    attendance = db.Column(db.Float, nullable=False, default=0.0)
    theory_marks = db.Column(db.Float, nullable=False, default=0.0)
    practical_marks = db.Column(db.Float, nullable=False, default=0.0)
    test_score = db.Column(db.Float, nullable=False, default=0.0)
    project_score = db.Column(db.Float, nullable=False, default=0.0)

    # Skill name -> score (0-100) stored as JSON text so the schema stays
    # flexible while remaining portable between SQLite and MySQL.
    skills_json = db.Column(db.Text, nullable=False, default="{}")

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # -- skills helpers -----------------------------------------------------
    @property
    def skills(self) -> dict[str, float]:
        try:
            raw = json.loads(self.skills_json or "{}")
        except (TypeError, ValueError):
            return {}
        return {
            str(key): float(value)
            for key, value in raw.items()
            if isinstance(value, (int, float))
        }

    @skills.setter
    def skills(self, value: dict[str, Any] | None) -> None:
        cleaned = {}
        if not isinstance(value, dict):
            self.skills_json = "{}"
            return
        for key, score in value.items():
            try:
                cleaned[str(key)] = max(0.0, min(100.0, float(score)))
            except (TypeError, ValueError):
                continue
        self.skills_json = json.dumps(cleaned, sort_keys=True)

    # -- serialisation ------------------------------------------------------
    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "roll_no": self.roll_no,
            "name": self.name,
            "trade": self.trade,
            "batch": self.batch,
            "email": self.email,
            "attendance": self.attendance,
            "theory_marks": self.theory_marks,
            "practical_marks": self.practical_marks,
            "test_score": self.test_score,
            "project_score": self.project_score,
            "skills": self.skills,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_dict(self, analysis: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = self.to_record()
        if analysis is not None:
            payload["analysis"] = analysis
        return payload

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Student {self.roll_no} {self.name!r}>"
