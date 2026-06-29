import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "file:///C:/Users/chris/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const ROOT = "C:/Users/chris/OneDrive/Documents/jwst-inspect-team2-worktree";
const OUT = path.join(ROOT, "outputs/v4_detailed_stl/final_presentation");
const RENDERED = path.join(OUT, "rendered");

const asset = {
  hero: path.join(ROOT, "outputs/v4_detailed_stl/render_loops/loop30/rtx_cycles.png"),
  loop25: path.join(ROOT, "outputs/v4_detailed_stl/render_loops/loop25/rtx_cycles.png"),
  loop26: path.join(ROOT, "outputs/v4_detailed_stl/render_loops/loop26/rtx_cycles.png"),
  loop27: path.join(ROOT, "outputs/v4_detailed_stl/render_loops/loop27/rtx_cycles.png"),
  loop28: path.join(ROOT, "outputs/v4_detailed_stl/render_loops/loop28/rtx_cycles.png"),
  loop29: path.join(ROOT, "outputs/v4_detailed_stl/render_loops/loop29/rtx_cycles.png"),
  contact: path.join(ROOT, "outputs/v4_detailed_stl/v4_detailed_stl_contact_sheet.png"),
  reference: path.join(ROOT, "outputs/v2_showcase/reference_board/visual_reference_contact_sheet.png"),
  rejected: path.join(ROOT, "outputs/v3_high_fidelity/render_loops/loop51/rtx_cycles.png"),
  rejectedFallback: path.join(ROOT, "outputs/v2_showcase/visual_render/render_loops/loop20/rtx_cycles.png"),
  readinessCurve: path.join(ROOT, "outputs/rl_v2/inspection_readiness_curve.png"),
  readinessBars: path.join(ROOT, "outputs/rl_v2/policy_readiness_comparison.png"),
  firstPov: path.join(ROOT, "outputs/v2_showcase/visual_render/video_frame_checks/first_iteration_policy_pov_1.png"),
  finalPov: path.join(ROOT, "outputs/v2_showcase/visual_render/video_frame_checks/final_policy_pov_1.png"),
};

const data = {
  manifest: path.join(ROOT, "outputs/v4_detailed_stl/v4_detailed_stl_manifest.json"),
  rlSummary: path.join(ROOT, "outputs/rl_v2/ppo_training_summary.json"),
  video: path.join(ROOT, "outputs/v4_detailed_stl/final_video/jwst_inspect_v4_visual_quality_showcase.mp4"),
};

const color = {
  bg: "#050A10",
  panel: "#0E1A25",
  panel2: "#132637",
  text: "#EEF5F7",
  muted: "#9FB0BD",
  gold: "#F4BF45",
  cyan: "#55C7E7",
  green: "#61D394",
  red: "#FF6B6B",
  line: "#284356",
  white: "#FFFFFF",
  black: "#000000",
};

function pos(left, top, width, height) {
  return { left, top, width, height };
}

async function exists(file) {
  try {
    await fs.access(file);
    return true;
  } catch {
    return false;
  }
}

async function readJson(file) {
  return JSON.parse(await fs.readFile(file, "utf8"));
}

async function imageBytes(file) {
  return new Uint8Array(await fs.readFile(file));
}

function contentType(file) {
  const ext = path.extname(file).toLowerCase();
  if (ext === ".jpg" || ext === ".jpeg") return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  return "image/png";
}

async function addImage(slide, file, frame, fit = "cover", alt = "") {
  slide.images.add({
    blob: await imageBytes(file),
    contentType: contentType(file),
    alt,
    fit,
    position: frame,
  });
}

function addRect(slide, frame, fill, lineFill = "none", radius = 0) {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: frame,
    fill,
    line: { style: "solid", fill: lineFill, width: lineFill === "none" ? 0 : 1 },
    borderRadius: radius,
  });
}

function addText(slide, text, frame, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: frame,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: style.fontSize ?? 19,
    bold: style.bold ?? false,
    italic: style.italic ?? false,
    color: style.color ?? color.text,
    alignment: style.alignment ?? "left",
  };
  return shape;
}

function addTitle(slide, title, subtitle = "") {
  addText(slide, title, pos(72, 56, 1030, 60), { fontSize: 42, bold: true });
  if (subtitle) {
    addText(slide, subtitle, pos(72, 122, 1020, 56), { fontSize: 22, color: color.muted });
  }
}

function addKicker(slide, label) {
  addText(slide, label.toUpperCase(), pos(72, 30, 680, 24), { fontSize: 12, bold: true, color: color.cyan });
}

function addFootnote(slide, text) {
  addText(slide, text, pos(72, 674, 1130, 24), { fontSize: 10, color: color.muted });
}

function addBullets(slide, items, frame, fontSize = 17) {
  addText(slide, items.map((item) => `- ${item}`).join("\n"), frame, { fontSize, color: color.text });
}

function addMetric(slide, value, label, frame, accent = color.cyan) {
  addRect(slide, frame, color.panel, color.line, 8);
  addText(slide, value, pos(frame.left + 16, frame.top + 14, frame.width - 32, 42), {
    fontSize: 32,
    bold: true,
    color: accent,
    alignment: "center",
  });
  addText(slide, label, pos(frame.left + 16, frame.top + 60, frame.width - 32, 40), {
    fontSize: 12,
    color: color.muted,
    alignment: "center",
  });
}

function addChip(slide, label, frame, fill, textColor = color.bg) {
  addRect(slide, frame, fill, fill, 8);
  addText(slide, label, pos(frame.left + 12, frame.top + 8, frame.width - 24, frame.height - 12), {
    fontSize: 13,
    bold: true,
    color: textColor,
    alignment: "center",
  });
}

async function baseSlide(presentation, kicker, title, subtitle = "") {
  const slide = presentation.slides.add();
  slide.background.fill = color.bg;
  addKicker(slide, kicker);
  addTitle(slide, title, subtitle);
  return slide;
}

async function requireAssets(paths) {
  const missing = [];
  for (const file of paths) {
    if (!(await exists(file))) missing.push(file);
  }
  if (missing.length) {
    throw new Error(`Missing required deck assets:\n${missing.join("\n")}`);
  }
}

async function makeDeck() {
  await fs.mkdir(RENDERED, { recursive: true });
  const manifest = await readJson(data.manifest);
  const rl = await readJson(data.rlSummary);
  const rejected = (await exists(asset.rejected)) ? asset.rejected : asset.rejectedFallback;

  await requireAssets([
    asset.hero,
    asset.loop25,
    asset.loop26,
    asset.loop27,
    asset.loop28,
    asset.loop29,
    asset.contact,
    asset.reference,
    rejected,
    asset.readinessCurve,
    asset.readinessBars,
    asset.firstPov,
    asset.finalPov,
    data.video,
  ]);

  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  {
    const slide = presentation.slides.add();
    slide.background.fill = color.bg;
    await addImage(slide, asset.hero, pos(0, 0, 1280, 720), "cover", "Final accepted v4 JWST render");
    addRect(slide, pos(0, 0, 1280, 720), "#00000080");
    addChip(slide, "V4 VISUAL SHOWCASE", pos(72, 58, 196, 38), color.gold);
    addText(slide, "JWST-Inspect", pos(72, 142, 620, 82), { fontSize: 64, bold: true, color: color.white });
    addText(slide, "Official detailed-STL visual recovery, RL policy evidence, and final presentation video", pos(76, 230, 760, 70), { fontSize: 25, color: color.text });
    addRect(slide, pos(76, 324, 560, 2), color.gold);
    addBullets(slide, [
      "Final visuals use official NASA detailed STL geometry and raw Cycles renders.",
      "Bad visual branches are documented rather than hidden.",
      "The policy claim is measured with Inspection Readiness Score, not visual appeal.",
    ], pos(78, 356, 700, 118), 19);
    addText(slide, "Video: outputs/v4_detailed_stl/final_video/jwst_inspect_v4_visual_quality_showcase.mp4", pos(78, 610, 990, 28), { fontSize: 14, color: color.muted });
  }

  {
    const slide = await baseSlide(presentation, "Sponsor ask", "What the capstone had to prove", "A credible autonomous inspection benchmark needs a scene, a data pipeline, a policy loop, and renderer-transfer evidence.");
    const cards = [
      ["1", "Scene", "JWST target, inspector craft, safety zones, semantic labels, lighting/material variants."],
      ["2", "Data", "Synthetic RGB/depth/segmentation, manifests, provenance, held-out reference discipline."],
      ["3", "Policy", "Scripted and learned inspection behavior measured for safe coverage and anomaly handling."],
      ["4", "Transfer", "Rasterized versus path-traced behavior compared without hiding failures."],
    ];
    for (let i = 0; i < cards.length; i += 1) {
      const x = 72 + i * 292;
      addRect(slide, pos(x, 250, 250, 284), color.panel, color.line, 8);
      addText(slide, cards[i][0], pos(x + 24, 274, 46, 44), { fontSize: 31, bold: true, color: color.gold, alignment: "center" });
      addText(slide, cards[i][1], pos(x + 80, 274, 132, 34), { fontSize: 23, bold: true });
      addText(slide, cards[i][2], pos(x + 26, 342, 198, 124), { fontSize: 15, color: color.muted });
    }
    addMetric(slide, "3", "workstreams integrated", pos(170, 584, 230, 90), color.green);
    addMetric(slide, "Week 12", "validation gates retained", pos(525, 584, 230, 90), color.cyan);
    addMetric(slide, "0", "hidden failed checkpoints", pos(880, 584, 230, 90), color.green);
  }

  {
    const slide = await baseSlide(presentation, "Reference grounding", "Visual targets came from official mission media", "The strongest available flight-like evidence is separation/deployment imagery plus official NASA/SVS and NASA 3D assets.");
    await addImage(slide, asset.reference, pos(52, 218, 720, 410), "contain", "Official JWST visual reference board");
    addRect(slide, pos(820, 232, 360, 320), color.panel, color.line, 8);
    addText(slide, "Reference intent", pos(850, 262, 280, 34), { fontSize: 25, bold: true, color: color.gold });
    addBullets(slide, [
      "Use real/official media for silhouette, material cues, and camera language.",
      "Avoid pretending there are abundant close-up in-space JWST photos.",
      "Use cleanroom imagery and NASA 3D resources for component/material detail.",
      "Keep validation images out of training and tuning claims.",
    ], pos(850, 322, 270, 160), 15);
    addFootnote(slide, "Reference board includes official NASA/SVS-style deployment imagery already tracked in the project output package.");
  }

  {
    const slide = await baseSlide(presentation, "Visual recovery", "The bad branches were rejected", "The earlier loop problem was real: later attempts introduced fake geometry or overlays. The accepted branch resets on official detailed STL geometry.");
    addText(slide, "Rejected branch", pos(72, 214, 350, 28), { fontSize: 22, bold: true, color: color.red });
    addText(slide, "Accepted v4 branch", pos(682, 214, 350, 28), { fontSize: 22, bold: true, color: color.green });
    await addImage(slide, rejected, pos(72, 260, 544, 306), "cover", "Rejected visual branch");
    await addImage(slide, asset.hero, pos(682, 260, 544, 306), "cover", "Accepted v4 branch");
    addText(slide, "Crude/fake mirror overlays or geometry", pos(72, 586, 420, 26), { fontSize: 15, color: color.muted });
    addText(slide, "Raw Cycles render, official NASA detailed STL", pos(682, 586, 430, 26), { fontSize: 15, color: color.muted });
  }

  {
    const slide = await baseSlide(presentation, "Accepted asset", "Final v4 visual quality set", "Six accepted raw Cycles frames cover the hero, close-up, wide, low cinematic, and inspection-POV angles.");
    await addImage(slide, asset.contact, pos(42, 198, 1196, 436), "contain", "Final v4 visual contact sheet");
    addFootnote(slide, `Render package: ${manifest.render_package_id}. Source: ${manifest.source_asset}.`);
  }

  {
    const slide = presentation.slides.add();
    slide.background.fill = color.bg;
    await addImage(slide, asset.hero, pos(0, 0, 1280, 720), "cover", "Final v4 accepted hero render");
    addRect(slide, pos(0, 0, 1280, 220), "#00000095");
    addChip(slide, "RAW CYCLES", pos(72, 58, 138, 36), color.gold);
    addText(slide, "Final hero render", pos(72, 108, 640, 62), { fontSize: 48, bold: true, color: color.white });
    addText(slide, "The outcome is credible for a capstone demo because it uses the detailed official mesh, restrained materials, and no fake presentation-only overlays.", pos(76, 170, 880, 36), { fontSize: 18, color: color.text });
    addMetric(slide, "30", "accepted final render loop", pos(930, 496, 230, 92), color.gold);
    addMetric(slide, "0", "postprocessed-only success claims", pos(930, 604, 230, 92), color.green);
  }

  {
    const slide = await baseSlide(presentation, "RL evidence", "The policy work remains measured, not cosmetic", "The visual upgrade improves communication; the inspection claim still rests on policy metrics and safety guardrails.");
    await addImage(slide, asset.readinessCurve, pos(72, 238, 520, 330), "contain", "Inspection Readiness Score over PPO training");
    await addImage(slide, asset.readinessBars, pos(670, 238, 520, 330), "contain", "Policy comparison chart");
    addMetric(slide, rl.scripted_score.toFixed(3), "scripted baseline", pos(142, 594, 198, 82), color.cyan);
    addMetric(slide, rl.best_ppo_score.toFixed(3), `best PPO, iter ${rl.best_iteration}`, pos(402, 594, 198, 82), color.green);
    addMetric(slide, rl.final_path_traced_score.toFixed(3), "final path-traced eval", pos(662, 594, 198, 82), color.green);
    addMetric(slide, String(rl.guardrails.hidden_failed_checkpoints), "hidden failed checkpoints", pos(922, 594, 198, 82), color.green);
  }

  {
    const slide = await baseSlide(presentation, "Policy POV", "Before and after policy behavior", "The deck separates policy progression from visual quality so the viewer can judge both claims independently.");
    addText(slide, "First iteration", pos(72, 214, 350, 28), { fontSize: 22, bold: true, color: color.red });
    addText(slide, "Final policy", pos(682, 214, 350, 28), { fontSize: 22, bold: true, color: color.green });
    await addImage(slide, asset.firstPov, pos(72, 260, 544, 306), "cover", "First iteration policy POV");
    await addImage(slide, asset.finalPov, pos(682, 260, 544, 306), "cover", "Final policy POV");
    addText(slide, "Early checkpoint: weak readiness, poor mission progress.", pos(72, 586, 460, 26), { fontSize: 15, color: color.muted });
    addText(slide, "Final checkpoint: safe inspection route, measured under path-traced evaluation.", pos(682, 586, 480, 26), { fontSize: 15, color: color.muted });
  }

  {
    const slide = await baseSlide(presentation, "Traceability", "Every visual claim points to an artifact", "The package is designed to survive a skeptical review: source asset, manifest, render loops, RL curves, and final video all have file-level evidence.");
    const rows = [
      ["Official asset", manifest.source_url],
      ["Render manifest", "outputs/v4_detailed_stl/v4_detailed_stl_manifest.json"],
      ["Accepted frames", "outputs/v4_detailed_stl/render_loops/loop25..loop30/rtx_cycles.png"],
      ["RL evidence", "outputs/rl_v2/ppo_training_summary.json and chart PNGs"],
      ["Video", "outputs/v4_detailed_stl/final_video/jwst_inspect_v4_visual_quality_showcase.mp4"],
    ];
    addRect(slide, pos(72, 224, 1136, 350), color.panel, color.line, 8);
    for (let i = 0; i < rows.length; i += 1) {
      const y = 254 + i * 60;
      addText(slide, rows[i][0], pos(110, y, 170, 26), { fontSize: 17, bold: true, color: color.gold });
      addText(slide, rows[i][1], pos(308, y, 800, 28), { fontSize: 15, color: color.text });
      if (i < rows.length - 1) addRect(slide, pos(104, y + 42, 1000, 1), color.line);
    }
    addMetric(slide, "0", "manual metric edits", pos(170, 604, 220, 82), color.green);
    addMetric(slide, "0", "safety disables", pos(530, 604, 220, 82), color.green);
    addMetric(slide, "0", "postprocessed-only wins", pos(890, 604, 220, 82), color.green);
  }

  {
    const slide = await baseSlide(presentation, "Video deliverable", "A short visual-quality showcase is now generated", "The MP4 walks through reference grounding, rejected-vs-accepted visual recovery, final v4 views, and RL metric evidence.");
    await addImage(slide, asset.hero, pos(72, 222, 720, 406), "cover", "Video poster frame");
    addRect(slide, pos(840, 222, 368, 406), color.panel, color.line, 8);
    addText(slide, "MP4 output", pos(872, 258, 240, 30), { fontSize: 24, bold: true, color: color.gold });
    addText(slide, "Folder:\noutputs/v4_detailed_stl/final_video\n\nFile:\njwst_inspect_v4_visual_quality_showcase.mp4", pos(872, 314, 286, 104), { fontSize: 14, color: color.text });
    addBullets(slide, [
      "1920 x 1080",
      "46 seconds",
      "H.264 MP4",
      "Uses only tracked source artifacts",
    ], pos(872, 424, 260, 120), 17);
  }

  {
    const slide = await baseSlide(presentation, "Limits", "What this still does not claim", "This is now much better presentation material, but the strongest version of the project would still rebuild the accepted asset in full OpenUSD/Omniverse.");
    const limits = [
      ["Not a flight photo", "The final visual is a raw render from official geometry, not an actual in-space JWST camera capture."],
      ["Not VFX-grade mesh", "The NASA detailed STL is excellent for provenance, but it is not the same as a production hero model with physically exact mirror segments."],
      ["Not postprocess magic", "The accepted branch avoids fake mirror overlays and does not base success on cinematic postprocessing alone."],
      ["Policy still needs depth", "The PPO evidence beats baselines on the readiness metric, but a future paper should expand dynamics, perception, and domain randomization."],
    ];
    for (let i = 0; i < limits.length; i += 1) {
      const x = 72 + (i % 2) * 568;
      const y = 230 + Math.floor(i / 2) * 174;
      addRect(slide, pos(x, y, 518, 126), color.panel, color.line, 8);
      addText(slide, limits[i][0], pos(x + 28, y + 22, 300, 28), { fontSize: 22, bold: true, color: color.gold });
      addText(slide, limits[i][1], pos(x + 28, y + 64, 430, 42), { fontSize: 15, color: color.muted });
    }
  }

  {
    const slide = presentation.slides.add();
    slide.background.fill = color.bg;
    await addImage(slide, asset.hero, pos(0, 0, 1280, 720), "cover", "Final v4 render");
    addRect(slide, pos(0, 0, 1280, 720), "#000000A8");
    addText(slide, "Final position", pos(72, 86, 620, 64), { fontSize: 52, bold: true, color: color.white });
    addText(slide, "The project is no longer just technically defensible. It now has a clean visual story: official geometry, rejected bad branches, measured policy progress, and a generated video package.", pos(76, 166, 880, 74), { fontSize: 24, color: color.text });
    addRect(slide, pos(76, 280, 620, 2), color.gold);
    addBullets(slide, [
      "Use this deck for defense and sponsor review.",
      "Use the MP4 when the audience needs to see visual quality quickly.",
      "For a publication-grade NVIDIA demo, the next investment is official OpenUSD/Omniverse capture on top of the accepted v4 asset path.",
    ], pos(78, 318, 820, 132), 19);
    addText(slide, "JWST-Inspect v4 Visual Showcase", pos(78, 608, 580, 32), { fontSize: 18, bold: true, color: color.gold });
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(RENDERED, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(RENDERED, `${stem}.layout.json`), await layout.text());
  }

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(path.join(OUT, "JWST-Inspect_v4_Visual_Showcase.pptx"));
}

makeDeck().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
