#!/usr/bin/env bash
#SBATCH --job-name=jwst-pyxis-e2e
#SBATCH --partition=interactive
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

repo="${JWST_REPO_ROOT:-/data/groups/autonomous/jwst-inspect-current}"
run_dir="${JWST_RUN_DIR:-/data/groups/autonomous/runs/${SLURM_JOB_ID:-manual}-pyxis-e2e}"
lab_image="${JWST_PYXIS_ISAAC_LAB_IMAGE:-/data/shared/containers/isaac-lab.sqsh}"
sim_image="${JWST_PYXIS_ISAAC_SIM_IMAGE:-/data/shared/containers/isaac-sim.sqsh}"
isaac_cache="${JWST_ISAAC_CACHE:-/data/groups/autonomous/isaac-cache}"
ov_cache="${JWST_OV_CACHE:-/data/groups/autonomous/ov-cache}"
lab_mounts="/data:/data"
sim_mounts="/data:/data,${isaac_cache}:/isaac-sim/kit/cache,${ov_cache}:/root/.cache/ov"

mkdir -p "$run_dir/logs" "$run_dir/usd" "$run_dir/replicator" "$run_dir/isaaclab" "$run_dir/evaluation" "$isaac_cache" "$ov_cache"

cat > "$run_dir/run-runtime.py" <<'PY'
from jwst_inspect.smoke import runtime_info_main
raise SystemExit(runtime_info_main())
PY

cat > "$run_dir/run-usd.py" <<'PY'
from jwst_inspect.smoke import usd_smoke_main
raise SystemExit(usd_smoke_main())
PY

cat > "$run_dir/run-replicator.py" <<'PY'
from jwst_inspect.smoke import replicator_smoke_main
raise SystemExit(replicator_smoke_main())
PY

cat > "$run_dir/run-isaaclab.py" <<'PY'
from jwst_inspect.smoke import isaaclab_smoke_main
raise SystemExit(isaaclab_smoke_main())
PY

cat > "$run_dir/run-r2p.py" <<'PY'
from jwst_inspect.smoke import r2p_smoke_main
raise SystemExit(r2p_smoke_main())
PY

cat > "$run_dir/run-artifact-validate.py" <<'PY'
from jwst_inspect.smoke import artifact_validate_main
raise SystemExit(artifact_validate_main())
PY

write_summary() {
  local status="$1"
  local failed_step="${2:-}"
  python3 - "$run_dir" "$status" "$failed_step" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

run_dir = Path(sys.argv[1])
status = sys.argv[2]
failed_step = sys.argv[3]
steps = ["base", "usd", "replicator", "isaaclab", "r2p", "artifact_validate"]
payload = {
    "status": status,
    "runtime_model": "pyxis-enroot-bridge",
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "run_dir": run_dir.as_posix(),
    "failed_step": failed_step or None,
    "steps": {},
}
for step in steps:
    exitcode_path = run_dir / "logs" / f"{step}.exitcode"
    payload["steps"][step] = {
        "exitcode": int(exitcode_path.read_text().strip()) if exitcode_path.exists() else None,
        "log": f"logs/{step}.log",
    }
(run_dir / "validation_summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

write_native_oci_probe() {
  local status="blocked"
  local reason="Slurm exposes --container, but native OCI cannot pivot until the site provides /etc/slurm/oci.conf."
  if [ -f /etc/slurm/oci.conf ]; then
    status="not_validated_by_bridge_job"
    reason="/etc/slurm/oci.conf exists; run slurm/submit-e2e-smoke.sh for native OCI validation."
  fi
  python3 - "$run_dir" "$status" "$reason" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

run_dir = Path(sys.argv[1])
payload = {
    "status": sys.argv[2],
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "reason": sys.argv[3],
    "required_admin_file": "/etc/slurm/oci.conf",
}
(run_dir / "native_oci_probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

run_step() {
  local name="$1"
  shift
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ${name}"
  set +e
  "$@" > "$run_dir/logs/${name}.log" 2>&1
  local rc=$?
  set -e
  echo "$rc" > "$run_dir/logs/${name}.exitcode"
  if [ "$rc" -ne 0 ]; then
    tail -n 120 "$run_dir/logs/${name}.log" || true
    write_summary failed "$name"
    exit "$rc"
  fi
}

write_native_oci_probe

run_step base \
  srun --input=none --ntasks=1 \
    --container-image="$lab_image" \
    --container-mounts="$lab_mounts" \
    bash -lc "export TERM=xterm PYTHONPATH=$repo/src; cd /data/shared/env/IsaacLab && ./isaaclab.sh -p $run_dir/run-runtime.py --root $repo --out $run_dir/base-runtime.json --require-gpu"

run_step usd \
  srun --input=none --ntasks=1 \
    --container-image="$lab_image" \
    --container-mounts="$lab_mounts" \
    bash -lc "export TERM=xterm PYTHONPATH=$repo/src; cd /data/shared/env/IsaacLab && ./isaaclab.sh -p $run_dir/run-usd.py --root $repo --run-dir $run_dir/usd"

run_step replicator \
  srun --input=none --ntasks=1 \
    --container-image="$sim_image" \
    --container-mounts="$sim_mounts" \
    bash -lc "export PYTHONPATH=$repo/src; /isaac-sim/python.sh $run_dir/run-replicator.py --root $repo --run-dir $run_dir/replicator --frames ${JWST_REPLICATOR_SMOKE_FRAMES:-2} --seed ${JWST_REPLICATOR_SMOKE_SEED:-20260630} --require-isaac"

run_step isaaclab \
  srun --input=none --ntasks=1 \
    --container-image="$lab_image" \
    --container-mounts="$lab_mounts" \
    bash -lc "export TERM=xterm PYTHONPATH=$repo/src; cd /data/shared/env/IsaacLab && ./isaaclab.sh -p $run_dir/run-isaaclab.py --run-dir $run_dir/isaaclab --episodes ${JWST_ISAACLAB_SMOKE_EPISODES:-1} --steps ${JWST_ISAACLAB_SMOKE_STEPS:-32} --require-isaaclab"

run_step r2p \
  srun --input=none --ntasks=1 \
    --container-image="$lab_image" \
    --container-mounts="$lab_mounts" \
    bash -lc "export TERM=xterm PYTHONPATH=$repo/src; cd /data/shared/env/IsaacLab && ./isaaclab.sh -p $run_dir/run-r2p.py --root $repo --run-dir $run_dir/evaluation --raster-frames ${JWST_R2P_RASTER_FRAMES:-2} --pathtraced-frames ${JWST_R2P_PATHTRACED_FRAMES:-1}"

run_step artifact_validate \
  srun --input=none --ntasks=1 \
    --container-image="$lab_image" \
    --container-mounts="$lab_mounts" \
    bash -lc "export TERM=xterm PYTHONPATH=$repo/src; cd /data/shared/env/IsaacLab && ./isaaclab.sh -p $run_dir/run-artifact-validate.py --run-dir $run_dir --out $run_dir/artifact_manifest.json"

write_summary passed
echo "$run_dir" > /data/groups/autonomous/latest_pyxis_validation_run.txt
echo "JWST_RUN_DIR=$run_dir"
