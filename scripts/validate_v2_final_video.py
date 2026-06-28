from __future__ import annotations

import json
from pathlib import Path

import cv2


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "v2_showcase" / "final_video"


def main() -> int:
    video_path = OUT / "jwst_inspect_v2_research_showcase.mp4"
    manifest_path = OUT / "jwst_inspect_v2_research_showcase_manifest.json"
    errors: list[str] = []
    if not video_path.exists() or video_path.stat().st_size < 5_000_000:
        errors.append(f"missing or tiny research video: {video_path}")
    if not manifest_path.exists():
        errors.append(f"missing research video manifest: {manifest_path}")
        manifest = {}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if video_path.exists():
        cap = cv2.VideoCapture(str(video_path))
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()
        if frames < 1400 or fps < 23.5 or width != 1280 or height != 720:
            errors.append(f"unexpected video geometry: frames={frames} fps={fps} size={width}x{height}")

    segments = manifest.get("segments", [])
    if len(segments) != 6:
        errors.append("research video manifest must contain six traceability segments")
    for segment in segments:
        artifacts = segment.get("artifacts", [])
        if not artifacts:
            errors.append(f"{segment.get('topic')}: no traced artifacts")
        for artifact in artifacts:
            path = Path(artifact)
            if not path.exists() or path.stat().st_size == 0:
                errors.append(f"{segment.get('topic')}: missing traced artifact {path}")
    guardrails = manifest.get("guardrails", {})
    if guardrails.get("postprocessed_only_success_claim") is not False:
        errors.append("final video must not claim success from postprocessed-only artifacts")
    if guardrails.get("video_frames_trace_to_artifacts") is not True:
        errors.append("final video frames must trace to artifacts")
    if errors:
        print("V2 final video validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("V2 final video validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
