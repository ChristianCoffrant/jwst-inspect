# Final-Test Lock Artifacts

This directory stores machine-readable held-out final-test definitions.

Week 8 locks `week8_final_perception_test_definition.json` for
`week8-final-data-v1.0.0` / `scene-final-v1.0.0`. It contains seeds, camera
metadata, anomaly labels, counterpart links, planned output paths, and lock
policy fields.

It must not contain rendered final-test RGB, depth, semantic mask, or instance
mask media. Generated final-test media remains prohibited until the final
evaluation procedure explicitly releases it.

Week 9 adds the final evaluation run 1 request and run-manifest metadata:

- `week9_final_perception_run1_path_traced_requests.json` is the 120-frame
  path-traced RGB render request pack derived from the locked Week 8 definition.
- `week9_final_perception_run1_manifest.json` records the synced run ID and
  ignored generated output root after the official x090/Vast render.

These files do not include rendered media. The synced RGB outputs remain under
ignored `datasets/generated/week9_final_perception_run1/`.
