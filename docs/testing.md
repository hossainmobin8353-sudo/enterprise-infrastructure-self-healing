# Verification & evidence

## Automated tests (offline; no Hyper-V or Windows required)
- Policy allowlist, duplicate handling, and malformed policy rejection.
- Latest observation selection and OPEN incident generation.
- Missing/Unknown cannot receive remediation approval.
- HMAC approval binding, wrong secret and expiry rejection.
- Plan generates NOT_EXECUTED task, never invokes a host command.
- Hash-linked audit detects simple tampering.

## VM integration tests (MANUAL, NOT RUN IN CI)
- Provision authorized lab VM(s) attached to private switch; capture screenshot.
- Verify `Get-Service` inventory and the exported CSV contain no sensitive information.
- Confirm dry run outputs `DRY_RUN` without altering service state.
- Optionally verify approval-controlled recovery on a deliberately disposable test VM and a safe allowlisted service, only if approved and reversible.
- Validate system functionality and document before/after status, exit code, and logs.
- Explicitly record failures, not just successes; don't state VM integration passed unless you ran it.

## Security boundaries
Never automate service shutdown to manufacture an outage on production equipment. The Python demo's HMAC approval does not grant Windows access and does not replace enterprise RBAC/change approvals. Execution script does not independently validate the HMAC; it requires explicit operator action and confirmation.
