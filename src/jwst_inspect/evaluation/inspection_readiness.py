from __future__ import annotations

from dataclasses import dataclass
from typing import Any


READINESS_VERSION = "inspection_readiness_v0_1"


@dataclass(frozen=True)
class InspectionReadinessBreakdown:
    safe_component_coverage: float
    anomaly_recall: float
    anomaly_localization_quality: float
    standoff_quality: float
    view_diversity: float
    smooth_control: float
    successful_return_or_hold: float
    keepout_penalty: float
    collision_penalty: float
    unsafe_coverage_penalty: float
    false_alarm_penalty: float
    missed_priority_penalty: float

    @property
    def score(self) -> float:
        positive = (
            0.25 * self.safe_component_coverage
            + 0.20 * self.anomaly_recall
            + 0.15 * self.anomaly_localization_quality
            + 0.15 * self.standoff_quality
            + 0.10 * self.view_diversity
            + 0.10 * self.smooth_control
            + 0.05 * self.successful_return_or_hold
        )
        penalties = (
            self.keepout_penalty
            + self.collision_penalty
            + self.unsafe_coverage_penalty
            + self.false_alarm_penalty
            + self.missed_priority_penalty
        )
        return max(0.0, min(1.0, positive - penalties))

    def as_dict(self) -> dict[str, float | str]:
        return {
            "score_version": READINESS_VERSION,
            "inspection_readiness_score": round(self.score, 6),
            "safe_component_coverage": round(self.safe_component_coverage, 6),
            "anomaly_recall": round(self.anomaly_recall, 6),
            "anomaly_localization_quality": round(self.anomaly_localization_quality, 6),
            "standoff_quality": round(self.standoff_quality, 6),
            "view_diversity": round(self.view_diversity, 6),
            "smooth_control": round(self.smooth_control, 6),
            "successful_return_or_hold": round(self.successful_return_or_hold, 6),
            "keepout_penalty": round(self.keepout_penalty, 6),
            "collision_penalty": round(self.collision_penalty, 6),
            "unsafe_coverage_penalty": round(self.unsafe_coverage_penalty, 6),
            "false_alarm_penalty": round(self.false_alarm_penalty, 6),
            "missed_priority_penalty": round(self.missed_priority_penalty, 6),
        }


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def inspection_readiness_from_metrics(metrics: dict[str, Any]) -> InspectionReadinessBreakdown:
    """Compute the v2 inspection/maintenance readiness score.

    This intentionally extends the existing benchmark metrics instead of replacing
    them. A high score means the inspection craft collected safe, diverse,
    anomaly-relevant evidence while preserving standoff and avoiding keepout
    violations.
    """

    safe_component_coverage = clamp01(metrics.get("safe_component_coverage", metrics.get("surface_coverage", 0.0)))
    anomaly_recall = clamp01(metrics.get("anomaly_recall", 0.0))
    anomaly_localization_quality = clamp01(metrics.get("anomaly_localization_quality", 0.0))
    standoff_error_mean = float(metrics.get("standoff_error_mean", 10.0))
    standoff_quality = clamp01(1.0 - min(standoff_error_mean / 12.0, 1.0))
    view_diversity = clamp01(metrics.get("view_diversity", 0.0))
    control_effort = float(metrics.get("control_effort", 1.0))
    smooth_control = clamp01(1.0 - min(control_effort / 3.0, 1.0))
    successful_return_or_hold = clamp01(metrics.get("successful_return_or_hold", metrics.get("task_success", 0.0)))

    keepout_penalty = 0.18 * clamp01(metrics.get("keepout_violation_rate", 0.0))
    collision_penalty = 0.25 * clamp01(metrics.get("collision_rate", 0.0))
    unsafe_coverage_penalty = 0.10 * clamp01(metrics.get("unsafe_coverage_fraction", 0.0))
    false_alarm_penalty = 0.08 * clamp01(metrics.get("false_alarm_rate", 0.0))
    missed_priority_penalty = 0.15 * clamp01(metrics.get("missed_priority_fraction", 0.0))

    return InspectionReadinessBreakdown(
        safe_component_coverage=safe_component_coverage,
        anomaly_recall=anomaly_recall,
        anomaly_localization_quality=anomaly_localization_quality,
        standoff_quality=standoff_quality,
        view_diversity=view_diversity,
        smooth_control=smooth_control,
        successful_return_or_hold=successful_return_or_hold,
        keepout_penalty=keepout_penalty,
        collision_penalty=collision_penalty,
        unsafe_coverage_penalty=unsafe_coverage_penalty,
        false_alarm_penalty=false_alarm_penalty,
        missed_priority_penalty=missed_priority_penalty,
    )
