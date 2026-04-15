from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnomalyEvaluationReport:
    total_test_samples: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    target_met: bool


def evaluate_anomaly_detection_precision(
    predictions: list[dict[str, str | float]],
    ground_truth: list[dict[str, str | float]],
) -> AnomalyEvaluationReport:
    gt_map = {str(item["event_id"]): item["is_anomaly"] for item in ground_truth}
    pred_map = {str(item["event_id"]): item["is_anomaly"] for item in predictions}

    tp = 0
    fp = 0
    fn = 0

    for event_id, is_anomaly_gt in gt_map.items():
        is_anomaly_pred = pred_map.get(event_id, False)

        if is_anomaly_gt and is_anomaly_pred:
            tp += 1
        elif not is_anomaly_gt and is_anomaly_pred:
            fp += 1
        elif is_anomaly_gt and not is_anomaly_pred:
            fn += 1

    total = len(gt_map)
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return AnomalyEvaluationReport(
        total_test_samples=total,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1_score=round(f1, 4),
        target_met=precision >= 0.92,
    )
