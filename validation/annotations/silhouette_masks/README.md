# Silhouette Mask Annotation Staging

Week 4 only defines the mask and sparse-keypoint candidate workflow. Public JWST reference imagery is used for validation and reporting, not for training or model tuning.

Do not commit large mask rasters, downloaded public images, or generated render outputs to Git. Store external annotation artifacts in the agreed dataset store and keep only small manifests, templates, and validation notes in this repository.

Every mask candidate must map back to `validation/reference_manifest.csv`, set `excluded_from_training=true`, and record whether it belongs to `dev` or `heldout` validation use.
