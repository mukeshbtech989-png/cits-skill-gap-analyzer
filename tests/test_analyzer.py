"""Unit tests for the analysis engine (run: python -m unittest discover -s tests)."""

from __future__ import annotations

import unittest

from ml.analyzer import (
    SKILL_CATALOG,
    analyze_many,
    analyze_student,
    cohort_summary,
    grade,
    model_metrics,
)


def make_student(**overrides):
    record = {
        "id": 1,
        "roll_no": "CITS26CSA999",
        "name": "Test Student",
        "attendance": 80,
        "theory_marks": 70,
        "practical_marks": 75,
        "test_score": 68,
        "project_score": 72,
        "skills": {skill: 65 for skill in SKILL_CATALOG},
    }
    record.update(overrides)
    return record


class GradeTests(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(grade(92), "Excellent")
        self.assertEqual(grade(85), "Excellent")
        self.assertEqual(grade(84.9), "Good")
        self.assertEqual(grade(70), "Good")
        self.assertEqual(grade(69.9), "Average")
        self.assertEqual(grade(55), "Average")
        self.assertEqual(grade(54.9), "Needs Improvement")
        self.assertEqual(grade(0), "Needs Improvement")


class AnalysisTests(unittest.TestCase):
    def test_score_is_in_range(self):
        result = analyze_student(make_student())
        self.assertGreaterEqual(result["overall_score"], 0)
        self.assertLessEqual(result["overall_score"], 100)
        self.assertIn(result["level"], {"Excellent", "Good", "Average", "Needs Improvement"})

    def test_strong_student_scores_higher(self):
        weak = analyze_student(
            make_student(
                attendance=50,
                theory_marks=40,
                practical_marks=45,
                test_score=35,
                project_score=40,
                skills={skill: 30 for skill in SKILL_CATALOG},
            )
        )
        strong = analyze_student(
            make_student(
                attendance=95,
                theory_marks=90,
                practical_marks=94,
                test_score=88,
                project_score=92,
                skills={skill: 92 for skill in SKILL_CATALOG},
            )
        )
        self.assertGreater(strong["overall_score"], weak["overall_score"])
        self.assertEqual(weak["risk"], "High")
        self.assertNotEqual(strong["risk"], "High")

    def test_gaps_detected_for_low_skills(self):
        skills = {skill: 80 for skill in SKILL_CATALOG}
        skills["Python"] = 40
        skills["JavaScript"] = 55
        result = analyze_student(make_student(skills=skills))

        gap_names = {gap["skill"] for gap in result["gaps"]}
        self.assertIn("Python", gap_names)
        self.assertIn("JavaScript", gap_names)
        self.assertNotIn("Java", gap_names)

        python_gap = next(gap for gap in result["gaps"] if gap["skill"] == "Python")
        self.assertEqual(python_gap["gap"], 20)
        self.assertEqual(python_gap["severity"], "critical")
        self.assertEqual(result["gaps"][0]["skill"], "Python")

    def test_recommendations_follow_gaps(self):
        skills = {skill: 85 for skill in SKILL_CATALOG}
        skills["MySQL"] = 30
        result = analyze_student(make_student(skills=skills))

        self.assertTrue(result["recommendations"])
        self.assertEqual(result["recommendations"][0]["skill"], "MySQL")
        self.assertIn("SQL", result["recommendations"][0]["action"])

    def test_recommendation_when_no_gaps(self):
        result = analyze_student(
            make_student(skills={skill: 90 for skill in SKILL_CATALOG})
        )
        self.assertEqual(result["gaps"], [])
        self.assertEqual(result["recommendations"][0]["skill"], "Overall")

    def test_missing_skills_do_not_crash(self):
        result = analyze_student(make_student(skills={}))
        self.assertEqual(len(result["skills"]), len(SKILL_CATALOG))
        self.assertTrue(result["gaps"])

    def test_batch_matches_single(self):
        records = [make_student(roll_no=f"CITS{i}") for i in range(3)]
        batch = analyze_many(records)
        single = analyze_student(records[1])
        self.assertEqual(len(batch), 3)
        self.assertEqual(batch[1]["overall_score"], single["overall_score"])


class CohortTests(unittest.TestCase):
    def test_summary(self):
        analyses = analyze_many(
            [
                make_student(roll_no="A", skills={skill: 90 for skill in SKILL_CATALOG}),
                make_student(
                    roll_no="B",
                    attendance=55,
                    theory_marks=40,
                    practical_marks=45,
                    test_score=35,
                    project_score=40,
                    skills={skill: 35 for skill in SKILL_CATALOG},
                ),
            ]
        )
        summary = cohort_summary(analyses)

        self.assertEqual(summary["total"], 2)
        self.assertGreater(summary["average_score"], 0)
        self.assertGreaterEqual(summary["at_risk"], 1)
        self.assertTrue(summary["skills"])
        self.assertLessEqual(
            summary["weakest"][0]["average"], summary["strongest"][0]["average"]
        )

    def test_empty_summary(self):
        summary = cohort_summary([])
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["average_score"], 0)


class ModelTests(unittest.TestCase):
    def test_model_quality(self):
        metrics = model_metrics()
        self.assertGreaterEqual(metrics["r2"], 0.9)
        self.assertLess(metrics["mae"], 5)
        self.assertGreater(metrics["samples"], 1000)


if __name__ == "__main__":
    unittest.main()
