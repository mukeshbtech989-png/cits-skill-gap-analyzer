"""Retrain the performance model and print its quality metrics.

Usage::

    python -m ml.train_model
"""

from ml.analyzer import feature_importance, model_metrics, retrain


def main() -> None:
    info = retrain()
    metrics = info["metrics"]
    print("Model retrained on", metrics["samples"], "samples")
    print(f"  MAE : {metrics['mae']} marks")
    print(f"  R^2 : {metrics['r2']}")
    print("\nFeature importance:")
    for row in feature_importance():
        print(f"  {row['label']:<22} {row['importance']:>5}%")

    # Sanity check against the live cached model.
    assert model_metrics() == metrics


if __name__ == "__main__":
    main()
