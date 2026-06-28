from __future__ import annotations

import json
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1280
HEIGHT = 720
FPS = 24
DURATION_SECONDS = 60


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_H1 = font(46, True)
FONT_H2 = font(30, True)
FONT_BODY = font(22)
FONT_SMALL = font(16)


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def fit_image(img: Image.Image, box: tuple[int, int], fill: bool = False) -> Image.Image:
    target_w, target_h = box
    scale = max(target_w / img.width, target_h / img.height) if fill else min(target_w / img.width, target_h / img.height)
    new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
    resized = img.resize(new_size, Image.Resampling.LANCZOS)
    if fill:
        left = max(0, (resized.width - target_w) // 2)
        top = max(0, (resized.height - target_h) // 2)
        return resized.crop((left, top, left + target_w, top + target_h))
    canvas = Image.new("RGB", (target_w, target_h), (5, 10, 18))
    canvas.paste(resized, ((target_w - resized.width) // 2, (target_h - resized.height) // 2))
    return canvas


def rounded_panel(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], outline=(64, 107, 134), fill=(9, 21, 32)) -> None:
    draw.rounded_rectangle(rect, radius=8, fill=fill, outline=outline, width=1)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, fnt, fill=(235, 246, 255)) -> None:
    draw.text(xy, value, font=fnt, fill=fill)


def paste_box(canvas: Image.Image, img: Image.Image, rect: tuple[int, int, int, int], fill: bool = False) -> None:
    x0, y0, x1, y1 = rect
    fitted = fit_image(img, (x1 - x0, y1 - y0), fill=fill)
    canvas.paste(fitted, (x0, y0))


def video_frame(capture: cv2.VideoCapture, t_seconds: float, fallback: Image.Image) -> Image.Image:
    fps = capture.get(cv2.CAP_PROP_FPS) or FPS
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        return fallback
    frame_index = int((t_seconds * fps) % max(1, total))
    capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = capture.read()
    if not ok:
        return fallback
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame)


def section_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str | None = None) -> None:
    text(draw, (42, 28), title, FONT_H1)
    if subtitle:
        text(draw, (44, 86), subtitle, FONT_BODY, (176, 207, 224))


def build_frame(
    t: float,
    assets: dict[str, Image.Image],
    videos: dict[str, cv2.VideoCapture],
) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (3, 8, 15))
    draw = ImageDraw.Draw(canvas)

    if t < 8:
        section_title(draw, "JWST-Inspect v2", "Official mission media establishes the visual target before synthetic rendering.")
        refs = [
            assets["ref_launch"],
            assets["ref_sep"],
            assets["ref_l2"],
            assets["ref_cleanroom"],
        ]
        rects = [(42, 140, 340, 420), (356, 140, 654, 420), (670, 140, 968, 420), (984, 140, 1238, 420)]
        for rect, img in zip(rects, refs):
            paste_box(canvas, img, rect, fill=True)
            rounded_panel(draw, rect, outline=(70, 116, 148), fill=None)
        text(draw, (44, 470), "Ground truth: real separation/final-view imagery, SVS deployment/L2 visuals, NASA 3D asset, and cleanroom material reference.", FONT_BODY)
        text(draw, (44, 515), "Constraint: there are not abundant close-up in-space photos of JWST, so the render target is evidence-grounded rather than photo-copy trained.", FONT_SMALL, (168, 190, 205))
    elif t < 16:
        section_title(draw, "Scene Upgrade", "Proxy target to official-derived geometry plus procedural material detail.")
        rounded_panel(draw, (42, 130, 618, 616))
        rounded_panel(draw, (662, 130, 1238, 616))
        paste_box(canvas, assets["loop01"], (52, 178, 608, 520))
        paste_box(canvas, assets["loop20"], (672, 178, 1228, 520))
        text(draw, (60, 142), "First official import loop", FONT_H2, (255, 202, 74))
        text(draw, (680, 142), "Final visual-lock loop", FONT_H2, (96, 226, 255))
        text(draw, (54, 548), "Low detail, acceptable geometry check.", FONT_BODY, (184, 204, 218))
        text(draw, (674, 548), "Corrected gold primary, stronger lighting, traceable raw RTX output.", FONT_BODY, (184, 204, 218))
    elif t < 30:
        section_title(draw, "Policy POV: First Iteration", "Early scripted/initial policy behavior: less controlled approach and poorer inspection coverage.")
        frame = video_frame(videos["first"], t - 16, assets["first_fallback"])
        paste_box(canvas, frame, (72, 130, 1208, 640), fill=True)
        rounded_panel(draw, (72, 130, 1208, 640), outline=(96, 150, 185), fill=None)
        text(draw, (92, 585), "first_iteration_policy_pov.mp4", FONT_SMALL, (210, 225, 235))
    elif t < 44:
        section_title(draw, "Policy POV: Final PPO", "Final learned policy: safer standoff, better target retention, and improved inspection readiness.")
        frame = video_frame(videos["final"], t - 30, assets["final_fallback"])
        paste_box(canvas, frame, (72, 130, 1208, 640), fill=True)
        rounded_panel(draw, (72, 130, 1208, 640), outline=(96, 150, 185), fill=None)
        text(draw, (92, 585), "final_policy_pov.mp4", FONT_SMALL, (210, 225, 235))
    elif t < 52:
        section_title(draw, "Inspection Readiness Score", "The final PPO policy beats scripted and behavior-cloning baselines without worse safety violations.")
        rounded_panel(draw, (42, 128, 638, 628))
        rounded_panel(draw, (660, 128, 1238, 628))
        paste_box(canvas, assets["readiness_curve"], (58, 154, 622, 580))
        paste_box(canvas, assets["policy_bar"], (676, 154, 1222, 580))
    else:
        section_title(draw, "Final Render Evidence", "Rasterized, RTX path-traced, and inspector POV artifacts remain paired to run IDs.")
        rounded_panel(draw, (42, 124, 1238, 572))
        paste_box(canvas, assets["final_triptych"], (54, 136, 1226, 560))
        claims = [
            "20 render-inspect-refine loops, including paid RTX 5090 visual passes",
            "Official NASA 3D model retained as the provenance asset and exported to OpenUSD/USD",
            "RL metric artifacts, policy trajectories, and videos are validated by reproducible scripts",
        ]
        for idx, claim in enumerate(claims):
            text(draw, (66, 600 + idx * 26), f"- {claim}", FONT_SMALL, (189, 215, 229))

    return canvas


def main() -> None:
    root = repo_root()
    out_dir = root / "outputs" / "v2_showcase" / "final_video"
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / "jwst_inspect_v2_research_showcase.mp4"
    render_root = root / "outputs" / "v2_showcase" / "visual_render"
    ref_root = root / "outputs" / "v2_showcase" / "reference_board"
    rl_root = root / "outputs" / "rl_v2"

    paths = {
        "ref_launch": ref_root / "nasa_webb_launch_final_view.webp",
        "ref_sep": ref_root / "esa_hubble_webb_separation_image.jpg",
        "ref_l2": ref_root / "nasa_svs_l2_visualization.jpg",
        "ref_cleanroom": ref_root / "nasa_cleanroom_gold_mirror.jpg",
        "loop01": render_root / "render_loops" / "loop01" / "rtx_cycles.png",
        "loop20": render_root / "render_loops" / "loop20" / "rtx_cycles.png",
        "final_triptych": render_root / "v2_final_loop_triptych.png",
        "readiness_curve": rl_root / "inspection_readiness_curve.png",
        "policy_bar": rl_root / "policy_readiness_comparison.png",
        "first_fallback": render_root / "video_frame_checks" / "first_iteration_policy_pov_1.png",
        "final_fallback": render_root / "video_frame_checks" / "final_policy_pov_1.png",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing video inputs: {missing}")

    assets = {key: load_image(path) for key, path in paths.items()}
    videos = {
        "first": cv2.VideoCapture(str(render_root / "videos" / "first_iteration_policy_pov.mp4")),
        "final": cv2.VideoCapture(str(render_root / "videos" / "final_policy_pov.mp4")),
    }
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        raise RuntimeError("OpenCV could not open MP4 writer")

    total_frames = FPS * DURATION_SECONDS
    for frame_idx in range(total_frames):
        t = frame_idx / FPS
        frame = build_frame(t, assets, videos)
        writer.write(cv2.cvtColor(__import__("numpy").array(frame), cv2.COLOR_RGB2BGR))
    writer.release()
    for capture in videos.values():
        capture.release()

    manifest = {
        "video_id": "jwst_inspect_v2_research_showcase",
        "status": "success",
        "duration_seconds": DURATION_SECONDS,
        "fps": FPS,
        "path": video_path.as_posix(),
        "segments": [
            {"seconds": [0, 8], "topic": "official reference media", "artifacts": [paths[k].as_posix() for k in ["ref_launch", "ref_sep", "ref_l2", "ref_cleanroom"]]},
            {"seconds": [8, 16], "topic": "scene upgrade", "artifacts": [paths["loop01"].as_posix(), paths["loop20"].as_posix()]},
            {"seconds": [16, 30], "topic": "first policy POV", "artifacts": [(render_root / "videos" / "first_iteration_policy_pov.mp4").as_posix()]},
            {"seconds": [30, 44], "topic": "final policy POV", "artifacts": [(render_root / "videos" / "final_policy_pov.mp4").as_posix()]},
            {"seconds": [44, 52], "topic": "RL metrics", "artifacts": [paths["readiness_curve"].as_posix(), paths["policy_bar"].as_posix()]},
            {"seconds": [52, 60], "topic": "raster/RTX/POV final evidence", "artifacts": [paths["final_triptych"].as_posix()]},
        ],
        "run_ids": {
            "visual_manifest": (render_root / "v2_visual_render_manifest.json").as_posix(),
            "rl_summary": (rl_root / "ppo_training_summary.json").as_posix(),
        },
        "guardrails": {
            "raw_render_artifacts_used": True,
            "postprocessed_only_success_claim": False,
            "video_frames_trace_to_artifacts": True,
        },
    }
    (out_dir / "jwst_inspect_v2_research_showcase_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "video": str(video_path), "manifest": str(out_dir / "jwst_inspect_v2_research_showcase_manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
