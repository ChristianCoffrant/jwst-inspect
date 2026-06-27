# Reference Images

Downloaded public reference images should not be committed to Git.

Track every selected reference in `validation/reference_manifest.csv` and store large files in external storage if needed.

Public reference images are validation-only unless a separate experiment explicitly declares otherwise. They are not part of the official training data.

Week 6 freezes five dev references and five held-out references in `validation/reference_sets/week6_reference_freeze.yaml`. Held-out references must not be used for geometry, material, lighting, perception-threshold, anomaly, or policy tuning.

