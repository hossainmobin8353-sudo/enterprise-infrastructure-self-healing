# Architecture & trust boundaries

```
Windows isolated LAB-DC1 / LAB-FS1 / LAB-APP1
    | local Get-Service snapshots (read-only)
    v
CSV observations -> Python policy evaluator -> incident JSON -> append-only hash-linked audit log
                                                       |
                                            human approval (expiring HMAC)
                                                       |
                                  structured action plan (NOT_EXECUTED)
                                                       |
                                 operator on approved local lab VM
                                                       |
                         PowerShell Start-Service (-Execute + confirm)
                                                       |
                               local verification + test evidence
```

No remote administration or production integration is implemented. A signature on a local approval is a **demonstration control**, not enterprise authorization. The local lab operator must independently verify approval from an established change process; the PowerShell script checks ticket formatting and local hostname, not cryptographic approval validity. Do not treat either as a production security boundary.

**Design trade-off:** detection and planning are decoupled from execution. The Python API deliberately cannot start services; only explicit operator action on a lab VM can do so.

**Idempotency:** Running service yields no incident; attempting local recovery of already-running service exits without action.

**Missing/Unknown:** generate incidents but are not eligible for restart approval.

**Audit limitation:** hash-linked logs provide tamper evidence for simple modifications, not protection against an attacker who can rewrite the entire chain. Use a protected central logging system in production.
