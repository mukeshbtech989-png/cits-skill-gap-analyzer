"""Demo data so the dashboard is useful the moment the app starts."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from models import DEFAULT_BATCH, DEFAULT_TRADE, Student, db

SAMPLE_STUDENTS: list[dict] = [
    {
        "roll_no": "CITS26CSA001",
        "name": "Aarav Sharma",
        "attendance": 92,
        "theory_marks": 78,
        "practical_marks": 85,
        "test_score": 74,
        "project_score": 88,
        "skills": {
            "Python": 72,
            "Java": 84,
            "MySQL": 78,
            "HTML/CSS": 80,
            "JavaScript": 70,
            "C/C++": 65,
            "MS Office": 85,
            "Soft Skills": 80,
        },
    },
    {
        "roll_no": "CITS26CSA002",
        "name": "Priya Verma",
        "attendance": 88,
        "theory_marks": 82,
        "practical_marks": 90,
        "test_score": 86,
        "project_score": 92,
        "skills": {
            "Python": 88,
            "Java": 90,
            "MySQL": 84,
            "HTML/CSS": 86,
            "JavaScript": 80,
            "C/C++": 78,
            "MS Office": 90,
            "Soft Skills": 88,
        },
    },
    {
        "roll_no": "CITS26CSA003",
        "name": "Rohit Kumar",
        "attendance": 64,
        "theory_marks": 52,
        "practical_marks": 58,
        "test_score": 48,
        "project_score": 55,
        "skills": {
            "Python": 42,
            "Java": 55,
            "MySQL": 50,
            "HTML/CSS": 60,
            "JavaScript": 38,
            "C/C++": 45,
            "MS Office": 62,
            "Soft Skills": 58,
        },
    },
    {
        "roll_no": "CITS26CSA004",
        "name": "Sneha Gupta",
        "attendance": 76,
        "theory_marks": 68,
        "practical_marks": 74,
        "test_score": 66,
        "project_score": 72,
        "skills": {
            "Python": 58,
            "Java": 72,
            "MySQL": 68,
            "HTML/CSS": 74,
            "JavaScript": 52,
            "C/C++": 60,
            "MS Office": 78,
            "Soft Skills": 70,
        },
    },
    {
        "roll_no": "CITS26CSA005",
        "name": "Aditya Singh",
        "attendance": 81,
        "theory_marks": 74,
        "practical_marks": 80,
        "test_score": 70,
        "project_score": 76,
        "skills": {
            "Python": 65,
            "Java": 78,
            "MySQL": 72,
            "HTML/CSS": 70,
            "JavaScript": 62,
            "C/C++": 68,
            "MS Office": 80,
            "Soft Skills": 66,
        },
    },
    {
        "roll_no": "CITS26CSA006",
        "name": "Fatima Khan",
        "attendance": 95,
        "theory_marks": 88,
        "practical_marks": 92,
        "test_score": 90,
        "project_score": 94,
        "skills": {
            "Python": 92,
            "Java": 86,
            "MySQL": 88,
            "HTML/CSS": 90,
            "JavaScript": 84,
            "C/C++": 80,
            "MS Office": 92,
            "Soft Skills": 90,
        },
    },
    {
        "roll_no": "CITS26CSA007",
        "name": "Vivek Yadav",
        "attendance": 58,
        "theory_marks": 46,
        "practical_marks": 52,
        "test_score": 42,
        "project_score": 50,
        "skills": {
            "Python": 35,
            "Java": 48,
            "MySQL": 44,
            "HTML/CSS": 55,
            "JavaScript": 32,
            "C/C++": 40,
            "MS Office": 58,
            "Soft Skills": 50,
        },
    },
    {
        "roll_no": "CITS26CSA008",
        "name": "Anjali Mishra",
        "attendance": 84,
        "theory_marks": 76,
        "practical_marks": 82,
        "test_score": 78,
        "project_score": 80,
        "skills": {
            "Python": 70,
            "Java": 74,
            "MySQL": 80,
            "HTML/CSS": 78,
            "JavaScript": 68,
            "C/C++": 62,
            "MS Office": 82,
            "Soft Skills": 76,
        },
    },
]


def seed_if_empty() -> int:
    """Insert demo students when the table is empty. Returns rows added."""
    if Student.query.count():
        return 0

    for row in SAMPLE_STUDENTS:
        student = Student(
            roll_no=row["roll_no"],
            name=row["name"],
            trade=DEFAULT_TRADE,
            batch=DEFAULT_BATCH,
            attendance=row["attendance"],
            theory_marks=row["theory_marks"],
            practical_marks=row["practical_marks"],
            test_score=row["test_score"],
            project_score=row["project_score"],
        )
        student.skills = row["skills"]
        db.session.add(student)

    try:
        db.session.commit()
    except IntegrityError:
        # Two Gunicorn workers can start together; whichever loses the race
        # simply rolls back instead of crashing the app.
        db.session.rollback()
        return 0
    return len(SAMPLE_STUDENTS)
