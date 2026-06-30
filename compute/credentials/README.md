# Local Credentials

Normal JWST-Inspect GPU work does not use repo-managed provider API keys.
Server access is managed outside this repository through Tailscale, SSH keys,
JupyterHub credentials, and Slurm permissions.

Do not commit:

- SSH private keys
- workstation passwords
- Tailscale auth material
- cloud/provider API tokens
- generated `.env` files

Run the local workstation preflight with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jwst_remote_preflight.ps1 -User ccoffrant
```
