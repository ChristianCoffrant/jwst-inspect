import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "file:///C:/Users/chris/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const ROOT = "C:/Users/chris/OneDrive/Documents/jwst-inspect-team2-worktree";
const OUT = path.join(ROOT, "outputs/final_presentation");
const RENDERED = path.join(OUT, "rendered");

const img = {
  nasaWide: path.join(ROOT, "validation/reference_images/spacecraft/nasa_jwst_cleanroom_sunshield_primary_mirror_2016_jwst1.jpg"),
  nasaClose: path.join(ROOT, "validation/reference_images/spacecraft/nasa_jwst_cleanroom_primary_mirror_close_2016_jwst2.jpg"),
  nasa3d: path.join(ROOT, "assets/official_nasa/James Webb Space Telescope (B).png"),
  originalWeek8: path.join(ROOT, "validation/renders/week8_final/vast_42853129_20260627_1253_utc/week8_final_contact_sheet.png"),
  comparison: path.join(ROOT, "outputs/visual_rescue/jwst_visual_comparison_panel.png"),
  cyclesWide: path.join(ROOT, "outputs/visual_rescue/vast_42930897/nasa_jwst_cycles_v2_sunshield_sweep.png"),
  cyclesClose: path.join(ROOT, "outputs/visual_rescue/vast_42930897/nasa_jwst_cycles_v2_mirror_close.png"),
  raster: path.join(ROOT, "outputs/visual_rescue/vast_42930897/nasa_jwst_eevee_v2_raster_overview.png"),
};

const data = {
  week10: path.join(ROOT, "runs/week10_final_results_lock/week10_final_results_report.json"),
  week11: path.join(ROOT, "runs/week11_release_package/week11_release_summary.json"),
  week12: path.join(ROOT, "runs/week12_final_evaluation_package/week12_final_evaluation_package.json"),
  rescue: path.join(ROOT, "outputs/visual_rescue/vast_42930897/visual_rescue_manifest.json"),
};

const color = {
  bg: "#071019",
  panel: "#0e1a25",
  panel2: "#122535",
  text: "#eef5f7",
  muted: "#9fb0bd",
  gold: "#f4bf45",
  cyan: "#55c7e7",
  green: "#61d394",
  red: "#ff6b6b",
  line: "#284356",
  white: "#ffffff",
};

function pos(left, top, width, height) {
  return { left, top, width, height };
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
    fontSize: style.fontSize ?? 20,
    bold: style.bold ?? false,
    color: style.color ?? color.text,
    alignment: style.alignment ?? "left",
  };
  return shape;
}

function addKicker(slide, text) {
  addText(slide, text.toUpperCase(), pos(72, 38, 720, 24), {
    fontSize: 12,
    bold: true,
    color: color.cyan,
  });
}

function addTitle(slide, title, subtitle = "") {
  addText(slide, title, pos(72, 74, 760, 94), { fontSize: 40, bold: true, color: color.text });
  if (subtitle) {
    addText(slide, subtitle, pos(72, 166, 800, 60), { fontSize: 18, color: color.muted });
  }
}

function addFootnote(slide, text) {
  addText(slide, text, pos(72, 672, 1136, 28), { fontSize: 10, color: color.muted });
}

function addStatusChip(slide, label, frame, fill) {
  addRect(slide, frame, fill, fill, 8);
  addText(slide, label, { left: frame.left + 10, top: frame.top + 6, width: frame.width - 20, height: frame.height - 8 }, {
    fontSize: 13,
    bold: true,
    color: color.bg,
    alignment: "center",
  });
}

function addMetric(slide, value, label, frame, accent = color.cyan) {
  addRect(slide, frame, color.panel, color.line, 8);
  addText(slide, String(value), pos(frame.left + 18, frame.top + 16, frame.width - 36, 44), {
    fontSize: 34,
    bold: true,
    color: accent,
    alignment: "center",
  });
  addText(slide, label, pos(frame.left + 18, frame.top + 62, frame.width - 36, 44), {
    fontSize: 13,
    color: color.muted,
    alignment: "center",
  });
}

function addBullets(slide, items, frame, options = {}) {
  const lines = items.map((item) => `- ${item}`).join("\n");
  addText(slide, lines, frame, {
    fontSize: options.fontSize ?? 18,
    color: options.color ?? color.text,
  });
}

function addDivider(slide, y = 628) {
  addRect(slide, pos(72, y, 1136, 1), color.line);
}

async function baseSlide(presentation, kicker, title, subtitle = "") {
  const slide = presentation.slides.add();
  slide.background.fill = color.bg;
  addKicker(slide, kicker);
  addTitle(slide, title, subtitle);
  return slide;
}

async function makeDeck() {
  await fs.mkdir(RENDERED, { recursive: true });
  const week10 = await readJson(data.week10);
  const week11 = await readJson(data.week11);
  const week12 = await readJson(data.week12);
  const rescue = await readJson(data.rescue);

  const presentation = Presentation.create({
    slideSize: { width: 1280, height: 720 },
  });

  // 1. Title
  {
    const slide = presentation.slides.add();
    slide.background.fill = color.bg;
    await addImage(slide, img.nasaWide, pos(0, 0, 1280, 720), "cover", "Real JWST cleanroom photo");
    addRect(slide, pos(0, 0, 1280, 720), "#00000099");
    addText(slide, "JWST-Inspect", pos(72, 78, 690, 78), { fontSize: 58, bold: true, color: color.white });
    addText(slide, "Final closeout: benchmark, data, policy evaluation, and visual fidelity rescue", pos(76, 164, 760, 64), {
      fontSize: 23,
      color: color.text,
    });
    addRect(slide, pos(74, 276, 522, 2), color.gold);
    addBullets(slide, [
      "Harvard capstone selected from NVIDIA sponsor brief",
      "Three integrated workstreams plus end-to-end validation",
      "Real JWST references compared against rasterized and path-traced visual outputs",
    ], pos(76, 310, 650, 126), { fontSize: 19 });
    addStatusChip(slide, "FINAL TECHNICAL GATES: PASS", pos(76, 524, 250, 36), color.green);
    addText(slide, "Visual status: showcase improved, Omniverse frame blocker remains documented", pos(76, 568, 620, 28), {
      fontSize: 15,
      color: color.muted,
    });
    addFootnote(slide, "Real image source: NASA Golden Mirror JWST cleanroom imagery. Deck generated from tracked repo evidence.");
  }

  // 2. Sponsor ask
  {
    const slide = await baseSlide(presentation, "First principles", "What NVIDIA wanted", "A benchmark to test whether autonomous inspection policies transfer from fast rasterized simulation to physically richer path-traced rendering.");
    const columns = [
      ["1", "Benchmark Scene", "Reusable OpenUSD scene: JWST geometry, inspector spacecraft, lighting variants, sensors, materials, safety regions."],
      ["2", "Synthetic Data Pipeline", "Replicator-style data package: RGB/depth/segmentation, poses, labels, metadata, manifests, validation split discipline."],
      ["3", "Policy Evaluation", "Scripted and learned baselines measured across rasterized and path-traced conditions with R2P gaps and failure modes."],
    ];
    for (let i = 0; i < columns.length; i += 1) {
      const x = 72 + i * 386;
      addRect(slide, pos(x, 288, 342, 250), color.panel, color.line, 8);
      addText(slide, columns[i][0], pos(x + 22, 310, 44, 44), { fontSize: 30, bold: true, color: color.gold, alignment: "center" });
      addText(slide, columns[i][1], pos(x + 78, 306, 230, 34), { fontSize: 21, bold: true, color: color.text });
      addText(slide, columns[i][2], pos(x + 26, 370, 288, 106), { fontSize: 16, color: color.muted });
    }
    addDivider(slide);
    addText(slide, "Validation standard: claims must trace to source files, run registries, cost logs, and reproducible clean-checkout validators.", pos(72, 642, 1030, 26), { fontSize: 15, color: color.text });
  }

  // 3. Workstream verdict
  {
    const slide = await baseSlide(presentation, "Integrated verdict", "Three workstreams are technically complete", "After the closeout repair, the integrated repository passes the Week 12 scene, data, evaluation, contract, dataset, registry, and smoke gates.");
    const rows = [
      ["Scene", "Week 12 release manifest, clean-checkout rehearsal, provenance appendix", "PASS"],
      ["Data", "Final package builder, validity claims, held-out reference discipline", "PASS"],
      ["Evaluation", "Final policy package, defense evidence, blocker manifests synced", "PASS"],
      ["Integration", "Clean checkout no longer depends on ignored local run artifacts", "PASS"],
    ];
    addRect(slide, pos(72, 260, 1136, 324), color.panel, color.line, 8);
    addText(slide, "Workstream", pos(98, 284, 180, 26), { fontSize: 13, bold: true, color: color.cyan });
    addText(slide, "Evidence", pos(320, 284, 650, 26), { fontSize: 13, bold: true, color: color.cyan });
    addText(slide, "Gate", pos(1040, 284, 100, 26), { fontSize: 13, bold: true, color: color.cyan, alignment: "center" });
    for (let i = 0; i < rows.length; i += 1) {
      const y = 326 + i * 58;
      addRect(slide, pos(96, y - 12, 1088, 1), color.line);
      addText(slide, rows[i][0], pos(98, y, 180, 30), { fontSize: 19, bold: true, color: color.text });
      addText(slide, rows[i][1], pos(320, y, 650, 34), { fontSize: 16, color: color.muted });
      addStatusChip(slide, rows[i][2], pos(1035, y - 2, 95, 30), color.green);
    }
    addMetric(slide, week10.row_count, "final policy rows", pos(72, 604, 178, 96), color.gold);
    addMetric(slide, week10.r2p_row_count, "raster to path pairs", pos(270, 604, 178, 96), color.cyan);
    addMetric(slide, week10.completed_row_count, "supported rows completed", pos(468, 604, 198, 96), color.green);
    addMetric(slide, "$0.00", "final held-out tuning", pos(686, 604, 178, 96), color.green);
    addMetric(slide, "blocker noted", "official Omniverse visual state", pos(884, 604, 324, 96), color.red);
  }

  // 4. Closeout repair
  {
    const slide = await baseSlide(presentation, "Closeout repair", "The missing piece was reproducibility", "Team 3 had valid local run evidence, but some clean-checkout validators depended on ignored run artifacts. I converted that evidence into tracked manifests and config fallbacks.");
    const beforeAfter = [
      ["Before", "Week 12 evaluation validator failed on a clean checkout because blocker evidence only existed under ignored run outputs.", color.red],
      ["After", "Tracked visual evidence manifests are referenced by Week 11 and Week 12 configs; validators pass without private local caches.", color.green],
    ];
    for (let i = 0; i < beforeAfter.length; i += 1) {
      const x = 72 + i * 580;
      addRect(slide, pos(x, 276, 524, 192), color.panel, beforeAfter[i][2], 8);
      addText(slide, beforeAfter[i][0], pos(x + 28, 300, 200, 34), { fontSize: 26, bold: true, color: beforeAfter[i][2] });
      addText(slide, beforeAfter[i][1], pos(x + 28, 354, 452, 70), { fontSize: 18, color: color.text });
    }
    addRect(slide, pos(72, 516, 1136, 86), color.panel2, color.line, 8);
    addText(slide, "Files changed", pos(100, 536, 160, 24), { fontSize: 15, bold: true, color: color.cyan });
    addText(slide, "validation/visual_evidence/*.json, configs/experiments/week11_release_package.yaml, configs/experiments/week12_final_evaluation_package.yaml, validation/evaluation fallback code, focused regression tests", pos(266, 536, 870, 38), {
      fontSize: 14,
      color: color.text,
    });
    addFootnote(slide, "This is the practical difference between a local demo and a defensible final submission.");
  }

  // 5. Visual audit
  {
    const slide = await baseSlide(presentation, "Visual audit", "The original visuals did not meet the ambition", "The benchmark worked technically, but the proxy scene and failed official capture path did not produce the kind of JWST evidence that wins a room.");
    await addImage(slide, img.comparison, pos(58, 230, 1164, 410), "contain", "Visual comparison panel");
    addRect(slide, pos(58, 230, 1164, 410), "#00000000", color.line, 8);
    addFootnote(slide, "Left to right comparison includes real NASA imagery, official 3D preview, original benchmark renders, and the Vast visual rescue outputs.");
  }

  // 6. Reference target
  {
    const slide = await baseSlide(presentation, "Reference target", "Real JWST validation images are now in scope", "The project now uses public NASA images as qualitative visual references, not training data. They set the visual bar for mirrors, sunshield, scale, and materials.");
    await addImage(slide, img.nasaWide, pos(72, 250, 548, 326), "cover", "JWST in cleanroom");
    await addImage(slide, img.nasaClose, pos(660, 250, 260, 326), "cover", "JWST mirror close view");
    await addImage(slide, img.nasa3d, pos(948, 250, 260, 326), "contain", "Official NASA 3D preview");
    addText(slide, "Visual reference only", pos(72, 596, 300, 26), { fontSize: 16, bold: true, color: color.gold });
    addBullets(slide, [
      "Reference images excluded from training and tuning",
      "Manifest entries are frozen outside the scored held-out split",
      "Visual comparison focuses on geometry, material identity, and scene plausibility",
    ], pos(384, 592, 740, 72), { fontSize: 15, color: color.text });
  }

  // 7. Vast loop
  {
    const slide = await baseSlide(presentation, "Paid visual rescue", "I spent GPU time where it changed the project", "The original Isaac/Omniverse capture path still failed. The rescue loop used Vast.ai and Blender 4.2 on an RTX 5090 to generate real high-fidelity comparison renders from the official NASA GLB.");
    const steps = [
      ["1", "Launch", "Vast instance 42930897 on RTX 5090"],
      ["2", "Fix deps", "Install Blender 4.2, NumPy, Draco, X11/EGL libs"],
      ["3", "Render", "Cycles OptiX path tracing and EEVEE raster"],
      ["4", "Close", "Sync artifacts, destroy instance, verify active instances = 0"],
    ];
    for (let i = 0; i < steps.length; i += 1) {
      const x = 72 + i * 284;
      addRect(slide, pos(x, 276, 246, 182), color.panel, color.line, 8);
      addText(slide, steps[i][0], pos(x + 18, 298, 36, 38), { fontSize: 28, bold: true, color: color.gold, alignment: "center" });
      addText(slide, steps[i][1], pos(x + 66, 300, 150, 30), { fontSize: 21, bold: true, color: color.text });
      addText(slide, steps[i][2], pos(x + 24, 356, 192, 58), { fontSize: 15, color: color.muted });
    }
    addMetric(slide, "RTX 5090", "GPU", pos(72, 508, 190, 104), color.cyan);
    addMetric(slide, "$0.192", "rescue spend", pos(292, 508, 190, 104), color.gold);
    addMetric(slide, rescue.status ?? "success", "render status", pos(512, 508, 190, 104), color.green);
    addMetric(slide, "0", "active instances after run", pos(732, 508, 220, 104), color.green);
    addMetric(slide, "2", "rendering modes", pos(982, 508, 226, 104), color.cyan);
    addFootnote(slide, "Rescue renders are visual-comparison artifacts, not replacements for the official Omniverse RTX benchmark capture.");
  }

  // 8. Raster vs path traced
  {
    const slide = await baseSlide(presentation, "Visual result", "Rasterized and path-traced views now look like JWST", "The rescue makes the inspection target recognizable: segmented gold mirrors, layered sunshield, and spacecraft bus detail are visible in both rendering modes.");
    await addImage(slide, img.raster, pos(72, 236, 548, 330), "cover", "EEVEE raster render");
    await addImage(slide, img.cyclesWide, pos(660, 236, 548, 330), "cover", "Cycles path-traced render");
    addRect(slide, pos(72, 236, 548, 330), "#00000000", color.line, 8);
    addRect(slide, pos(660, 236, 548, 330), "#00000000", color.line, 8);
    addText(slide, "Rasterized EEVEE", pos(92, 580, 240, 28), { fontSize: 18, bold: true, color: color.cyan });
    addText(slide, "Path traced Cycles OptiX", pos(680, 580, 280, 28), { fontSize: 18, bold: true, color: color.gold });
    addFootnote(slide, "The benchmark's official renderer-transfer metrics remain sourced from the Week 10/11 evaluation artifacts.");
  }

  // 9. Evaluation metrics
  {
    const slide = await baseSlide(presentation, "Policy evaluation", "The benchmark produced measurable renderer-transfer evidence", "The evaluation package compares rasterized and path-traced policy behavior and keeps unsupported learned-policy cases visible instead of hiding them.");
    slide.charts.add("bar", {
      position: pos(86, 258, 520, 300),
      categories: ["Total", "Completed", "Documented fail", "R2P pairs"],
      series: [{
        name: "Rows",
        values: [week10.row_count, week10.completed_row_count, week10.failed_row_count, week10.r2p_row_count],
        fill: color.cyan,
      }],
      hasLegend: false,
      barOptions: { direction: "bar", grouping: "clustered", gapWidth: 44 },
      xAxis: { visible: false, majorGridlines: null },
      yAxis: { textStyle: { fill: color.text, fontSize: 13 }, line: { style: "solid", fill: color.line, width: 1 } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: color.text, fontSize: 13, bold: true } },
      chartFill: color.bg,
      plotAreaFill: color.bg,
    });
    addRect(slide, pos(670, 256, 500, 300), color.panel, color.line, 8);
    addText(slide, "Core evaluation guardrails", pos(700, 284, 380, 30), { fontSize: 22, bold: true, color: color.gold });
    addBullets(slide, [
      `Expected policy rows match actual rows: ${week10.guardrails.expected_final_policy_rows_match}`,
      `Expected R2P rows match: ${week10.guardrails.expected_r2p_rows_match}`,
      `Dropped result rows: ${week10.guardrail_metrics.dropped_result_row_count}`,
      `Manual metrics edits: ${week10.guardrail_metrics.manual_metrics_edit_count}`,
      `Safety metric disables: ${week10.guardrail_metrics.safety_metric_disable_count}`,
      `Final held-out seed tuning: ${week10.guardrail_metrics.final_heldout_seed_tuning_count}`,
    ], pos(700, 342, 428, 154), { fontSize: 15, color: color.text });
    addFootnote(slide, "No RL loss curve is shown because the completed learned baseline is behavioral-cloning style evidence, not a claimed RL training run.");
  }

  // 10. Anti-gaming and validation
  {
    const slide = await baseSlide(presentation, "Validation discipline", "The project is defensible because it resists gaming", "The strongest part of the final package is not a single score. It is the evidence chain around claims, artifacts, costs, and guardrails.");
    const guards = [
      ["No data leakage", "Final held-out tuning and public-reference training use are recorded as zero."],
      ["No hidden failures", "Unsupported learned mirror-inspection cases remain visible and documented."],
      ["No fake visuals", "Official Omniverse visual success remains blocker_documented; rescue renders are separately labeled."],
      ["No cost ambiguity", "Paid GPU attempts appear in both cost log and GPU run registry."],
    ];
    for (let i = 0; i < guards.length; i += 1) {
      const x = 72 + (i % 2) * 568;
      const y = 256 + Math.floor(i / 2) * 164;
      addRect(slide, pos(x, y, 520, 120), color.panel, color.line, 8);
      addText(slide, guards[i][0], pos(x + 28, y + 24, 330, 28), { fontSize: 22, bold: true, color: color.green });
      addText(slide, guards[i][1], pos(x + 28, y + 66, 450, 38), { fontSize: 15, color: color.text });
    }
    addMetric(slide, week11.guardrail_metrics.visual_success_claim_without_artifact_count, "Week 11 unsupported visual claims", pos(72, 596, 254, 92), color.green);
    addMetric(slide, week12.guardrail_metrics.fabricated_or_placeholder_official_visual_count, "fabricated official visuals", pos(358, 596, 254, 92), color.green);
    addMetric(slide, week12.guardrail_metrics.clean_checkout_blocker_count, "clean-checkout blockers", pos(644, 596, 254, 92), color.green);
    addMetric(slide, "$0.116", "official Week 12 visual recovery spend", pos(930, 596, 278, 92), color.gold);
  }

  // 11. Completion status
  {
    const slide = await baseSlide(presentation, "Completion status", "Finished as a benchmark MVP, not yet as the highest-bar NVIDIA showcase", "The honest answer: the repo is technically shippable, but the sponsor-grade visual story still needs one more focused OpenUSD/Omniverse iteration.");
    const complete = [
      "Scene/data/evaluation package manifests and validators",
      "Synthetic data package with metadata and held-out references",
      "Raster-to-path policy comparisons and failure taxonomy",
      "Defense evidence, cost logs, and reproducible clean checkout",
    ];
    const remains = [
      "Replace proxy USD geometry with official JWST-derived OpenUSD asset",
      "Run official Omniverse/Isaac raster and RTX path-traced captures on that asset",
      "Produce a 60-90 second end-to-end video from the official renderer path",
      "Promote the benchmark as an open-source NVIDIA simulation reference repo",
    ];
    addRect(slide, pos(72, 254, 532, 330), color.panel, color.green, 8);
    addText(slide, "Complete now", pos(104, 284, 300, 32), { fontSize: 26, bold: true, color: color.green });
    addBullets(slide, complete, pos(104, 338, 440, 144), { fontSize: 17, color: color.text });
    addRect(slide, pos(676, 254, 532, 330), color.panel, color.gold, 8);
    addText(slide, "Highest-impact remaining work", pos(708, 284, 390, 32), { fontSize: 26, bold: true, color: color.gold });
    addBullets(slide, remains, pos(708, 338, 440, 156), { fontSize: 17, color: color.text });
    addFootnote(slide, "Recommended framing: ship the evidence package, then invest only in the official high-fidelity OpenUSD/RTX visual path.");
  }

  // 12. Final strategy
  {
    const slide = presentation.slides.add();
    slide.background.fill = color.bg;
    await addImage(slide, img.cyclesClose, pos(0, 0, 1280, 720), "cover", "Close path traced JWST mirror render");
    addRect(slide, pos(0, 0, 1280, 720), "#000000aa");
    addText(slide, "Winning strategy", pos(72, 68, 760, 68), { fontSize: 48, bold: true, color: color.white });
    addText(slide, "Do not chase every possible model. Make one public, reproducible benchmark that NVIDIA engineers would actually trust and want to run.", pos(76, 150, 840, 64), {
      fontSize: 23,
      color: color.text,
    });
    addBullets(slide, [
      "Lead with first-principles validation: renderer-transfer robustness, safety constraints, and traceable evidence.",
      "Use the visual rescue as a proof of what the asset path can become, then rebuild it in official OpenUSD/Omniverse.",
      "Publish the benchmark, docs, manifests, and failure cases. A clean, useful repo beats a brittle demo.",
      "Only attempt novel techniques after the benchmark is credible; a small, rigorous finding is better than broad unsupported claims.",
    ], pos(78, 272, 820, 190), { fontSize: 19, color: color.text });
    addRect(slide, pos(76, 544, 646, 2), color.gold);
    addText(slide, "Final recommendation: one more focused sprint on official JWST OpenUSD visual fidelity and Omniverse RTX capture would convert this from technically complete to sponsor-showcase caliber.", pos(78, 568, 820, 58), {
      fontSize: 17,
      color: color.gold,
    });
    addFootnote(slide, "Deck outputs: outputs/final_presentation/JWST-Inspect_Final_Closeout.pptx and rendered slide PNGs.");
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(RENDERED, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(RENDERED, `${stem}.layout.json`), await layout.text());
  }

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(path.join(OUT, "JWST-Inspect_Final_Closeout.pptx"));
}

makeDeck().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
