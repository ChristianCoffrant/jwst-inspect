param(
    [string]$User = "ccoffrant",
    [string]$HostName = "jwst-ws",
    [string]$KeyPath = "$env:USERPROFILE\.ssh\jwst_christiancoffrant",
    [switch]$RunServerCheck
)

$ErrorActionPreference = "Stop"

Write-Host "== Local JWST remote preflight =="
if (-not (Get-Command tailscale -ErrorAction SilentlyContinue)) {
    throw "Tailscale CLI was not found."
}

tailscale status | Out-Host

if (-not (Test-Path $KeyPath)) {
    throw "SSH key not found: $KeyPath"
}

$port = Test-NetConnection -ComputerName $HostName -Port 22 -WarningAction SilentlyContinue
if (-not $port.TcpTestSucceeded) {
    throw "$HostName port 22 is not reachable. Confirm Tailscale is on the project tailnet."
}

Write-Host "SSH target: $User@$HostName"

if ($RunServerCheck) {
    $remote = @'
set -euo pipefail
bash /data/shared/project/first_login_check.sh
srun --version
command -v scrun
scrun --version
srun --help | grep -E -- '--container( |=|$)|--container-image|--container-mounts'
srun -p interactive --gres=gpu:1 nvidia-smi -L
'@
    ssh -i $KeyPath "$User@$HostName" $remote
}

Write-Host "JWST remote preflight passed."
