# OCI Bundle Publishing

Native Slurm OCI uses an unpacked OCI runtime bundle, not an image tag. The
bundle must be staged on shared storage before `sbatch` or `srun` starts.

Expected toolchain in an admin or CI environment:

- image builder: Docker, Podman, or Buildah
- image copier: `skopeo`
- bundle unpacker: `umoci`
- Slurm runtime on server: `scrun`

Publish example:

```bash
containers/oci/export_bundle.sh \
  jwst-base:2026-06-30 \
  /data/shared/oci-bundles/jwst-base/2026-06-30
```

Then atomically repoint the `current` symlink after smoke tests pass:

```bash
ln -sfn /data/shared/oci-bundles/jwst-base/2026-06-30 \
  /data/shared/oci-bundles/jwst-base/current
```

If the native Slurm OCI smoke cannot see GPUs, keep using the existing Pyxis
bridge images only while the admin fixes site-level OCI GPU device injection.
