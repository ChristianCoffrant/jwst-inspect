#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <image-ref> <bundle-dir>" >&2
  exit 2
fi

image_ref="$1"
bundle_dir="$2"
tmp_oci="$(mktemp -d)"

cleanup() {
  rm -rf "$tmp_oci"
}
trap cleanup EXIT

for tool in skopeo umoci python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "missing required tool: $tool" >&2
    exit 1
  fi
done

if [[ -e "$bundle_dir" ]]; then
  echo "bundle dir already exists: $bundle_dir" >&2
  exit 1
fi

mkdir -p "$(dirname "$bundle_dir")"
skopeo copy "docker-daemon:${image_ref}" "oci:${tmp_oci}:latest"
umoci unpack --image "${tmp_oci}:latest" "$bundle_dir"

python3 "$(dirname "$0")/patch_bundle.py" "$bundle_dir"
find "$bundle_dir" -type f -print0 | sort -z | xargs -0 sha256sum > "${bundle_dir}.sha256"
echo "wrote OCI bundle: $bundle_dir"
echo "wrote checksum manifest: ${bundle_dir}.sha256"
