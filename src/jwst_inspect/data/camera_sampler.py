from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraSample:
    frame_index: int
    seed: int
    split: str
    renderer_mode: str
    sampler_mode: str
    target_region: str
    lighting_condition: str
    material_variant: str
    anomaly_type: str
    anomaly_prim: str | None
    position_m: tuple[float, float, float]
    look_at_m: tuple[float, float, float]
    inspector_position_m: tuple[float, float, float]


def _round_vector(values: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(round(value, 4) for value in values)


def _position_on_shell(radius_m: float, azimuth_rad: float, elevation_rad: float) -> tuple[float, float, float]:
    horizontal = radius_m * math.cos(elevation_rad)
    return _round_vector(
        (
            horizontal * math.cos(azimuth_rad),
            horizontal * math.sin(azimuth_rad),
            radius_m * math.sin(elevation_rad),
        )
    )


def sample_week1_cameras(frame_count: int = 10, base_seed: int = 120200) -> list[CameraSample]:
    """Return deterministic metadata-only camera samples for the Week 1 gate.

    These poses are intentionally simple and are not Isaac Sim camera commands.
    They give Team 2 stable metadata, split, renderer, and target-region records
    before Replicator is available.
    """

    if frame_count < 1:
        raise ValueError("frame_count must be positive")

    split_plan = (
        ["train"] * 6
        + ["validation"] * 2
        + ["dev_test"] * max(0, frame_count - 8)
    )[:frame_count]
    sampler_modes = ("uniform_standoff", "task_focused", "failure_focused")
    task_regions = ("approach_hold_standoff", "mirror_inspection", "sunshield_survey")
    lighting_conditions = ("nominal_sun_key", "high_glare_edge", "low_light_cold_side")
    material_variants = ("nominal", "high_glare", "degraded", "anomaly_test")
    anomaly_plan: tuple[tuple[str, str | None], ...] = (
        ("none", None),
        ("none", None),
        ("glare_induced_false_anomaly_condition", "/World/JWST/Optics/PrimaryMirror"),
        ("none", None),
        ("sunshield_discoloration", "/World/JWST/Sunshield"),
        ("none", None),
        ("mirror_region_obstruction", "/World/JWST/Optics/PrimaryMirror"),
        ("none", None),
        ("none", None),
        ("truss_occlusion_proxy", "/World/JWST/Truss"),
    )

    samples: list[CameraSample] = []
    for frame_index in range(frame_count):
        sampler_mode = sampler_modes[frame_index % len(sampler_modes)]
        target_region = task_regions[frame_index % len(task_regions)]
        split = split_plan[frame_index]
        renderer_mode = "path_traced" if split == "dev_test" and frame_index % 2 else "rasterized"

        if sampler_mode == "uniform_standoff":
            radius_m = 40.0
            elevation_rad = math.radians(-10 + frame_index * 4)
        elif sampler_mode == "task_focused":
            radius_m = 32.0 if target_region == "mirror_inspection" else 45.0
            elevation_rad = math.radians(8)
        else:
            radius_m = 28.0
            elevation_rad = math.radians(-18)

        azimuth_rad = math.radians((frame_index * 37) % 360)
        position_m = _position_on_shell(radius_m, azimuth_rad, elevation_rad)
        anomaly_type, anomaly_prim = anomaly_plan[frame_index % len(anomaly_plan)]

        samples.append(
            CameraSample(
                frame_index=frame_index,
                seed=base_seed + frame_index,
                split=split,
                renderer_mode=renderer_mode,
                sampler_mode=sampler_mode,
                target_region=target_region,
                lighting_condition=lighting_conditions[frame_index % len(lighting_conditions)],
                material_variant=material_variants[frame_index % len(material_variants)],
                anomaly_type=anomaly_type,
                anomaly_prim=anomaly_prim,
                position_m=position_m,
                look_at_m=(0.0, 0.0, 0.0),
                inspector_position_m=position_m,
            )
        )

    return samples
