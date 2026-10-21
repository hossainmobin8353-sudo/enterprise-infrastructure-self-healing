# Windows deployment runbook (isolated, owned lab only)

1. Install Python 3.10+, PowerShell 7+ (or Windows PowerShell 5.1), Git. Optional: enable Hyper-V on Windows Pro/Enterprise with administrator approval; reboot may be required.
2. Clone repository and install locally: `py -m pip install -e .` (prefer a Python virtual environment).
3. Run synthetic simulation before touching VMs: `selfheal scan` (see README).
4. Optional virtualization: create an isolated **private** virtual switch called `SelfHeal-Isolated` in Hyper-V Manager. Script `scripts/windows/New-IsolatedLabVM.ps1` dry-runs unless `-Execute` is specified. It creates only an empty VM; you must use properly licensed Windows install media, configure accounts, networking and services.
5. Optional lab topology: `LAB-DC1` Windows Server AD DS/DNS (manual install), `LAB-FS1` Windows Server file services, `LAB-APP1` Windows 11 application endpoint. Use RFC1918 addresses on an isolated private switch, e.g. 10.77.10.10/24, .20/24, .30/24; avoid routing to corporate networks. AD DS/DNS setup is an operator exercise, not automated by this repo.
6. Run read-only inventory **on each lab VM**, using `Get-LabServiceInventory.ps1`. Export each CSV and assemble observations using matching hostnames. Scanner only accepts three fixed lab hostnames (rename if needed in your own fork with corresponding policy updates).
7. For a safe reproducible demonstration, use the committed synthetic CSV, *not* service shutdown on any workstation used for real work.
8. If experimenting with a service restart on a disposable VM: use a documented change ticket, lab snapshot, and the local recovery script first without `-Execute` and then, only if necessary, `-Execute -Confirm`. Ensure your service selection does not affect your VM access. No remote restart, operating system reboot or forced service stop is implemented.
9. Capture sanitized output screenshots, the incident JSON, a manually verified service-status screenshot, and test output. Do not commit credentials, machine secrets, approval tokens or real user logs.
