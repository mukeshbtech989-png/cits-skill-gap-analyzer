"""Machine-learning package for the CITS Skill Gap Analyzer."""

from .analyzer import (  # noqa: F401
    SKILL_CATALOG,
    analyze_many,
    analyze_student,
    cohort_summary,
    feature_importance,
    get_model,
    grade,
    model_metrics,
    retrain,
)
