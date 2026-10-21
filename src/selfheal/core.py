"""Safe, deterministic monitoring + approval-controlled remediation orchestration.
No production command execution: remediation emits a constrained PowerShell plan.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone, timedelta
import csv, hashlib, hmac, json, secrets

ALLOWED_STATES = {"Running", "Stopped", "Missing", "Unknown"}

def utcnow():
    return datetime.now(timezone.utc)

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def validate_policy(policy):
    if not isinstance(policy, dict) or not isinstance(policy.get("targets"), list):
        raise ValueError("policy requires targets list")
    ids=set()
    for t in policy["targets"]:
        if set(("host", "service", "expected"))-set(t):
            raise ValueError("target requires host/service/expected")
        if not all(isinstance(t[k],str) and t[k] for k in ("host","service","expected")):
            raise ValueError("invalid target field")
        if t["expected"] != "Running":
            raise ValueError("only Running service expectation supported")
        if t["host"] not in ("LAB-DC1","LAB-FS1","LAB-APP1"):
            raise ValueError("outside fixed lab host allowlist")
        if t["service"] not in ("Spooler","W32Time","Dnscache"):
            raise ValueError("outside service allowlist")
        ident=(t["host"],t["service"])
        if ident in ids: raise ValueError("duplicate target")
        ids.add(ident)
    return policy

def load_policy(path):
    return validate_policy(json.loads(Path(path).read_text(encoding="utf-8")))

def load_observations(path):
    with open(path, newline="", encoding="utf-8") as f:
        records=list(csv.DictReader(f))
    if any(set(("host","service","status","timestamp"))-set(r) or r["status"] not in ALLOWED_STATES for r in records):
        raise ValueError("invalid observations CSV")
    return records

def evaluate(policy, observations):
    # Latest observation per target, deterministic tie break by input order.
    latest={}
    for row in observations:
        key=(row["host"],row["service"])
        try: stamp=datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))
        except ValueError as exc: raise ValueError("invalid timestamp") from exc
        if stamp.tzinfo is None: raise ValueError("timestamp must include timezone")
        if key not in latest or stamp >= latest[key][0]: latest[key]=(stamp,row)
    incidents=[]
    for target in policy["targets"]:
        key=(target["host"],target["service"])
        rec=latest.get(key)
        actual=rec[1]["status"] if rec else "Unknown"
        if actual != target["expected"]:
            ident=hashlib.sha256(f"{key[0]}|{key[1]}|{actual}".encode()).hexdigest()[:16]
            incidents.append({"id":ident,"host":key[0],"service":key[1],"expected":"Running","observed":actual,"severity":"high" if actual=="Stopped" else "medium","state":"OPEN","automated_action":"NONE","reason":"Manual approval required"})
    return incidents

def create_approval(incident, operator, secret, now=None, ttl_minutes=15):
    now=now or utcnow()
    if not operator.strip(): raise ValueError("operator required")
    if incident["observed"] != "Stopped": raise ValueError("only Stopped eligible")
    if not 1 <= ttl_minutes <= 60: raise ValueError("invalid TTL")
    payload={"incident_id":incident["id"],"host":incident["host"],"service":incident["service"],"operator":operator,"nonce":secrets.token_hex(12),"expires":(now+timedelta(minutes=ttl_minutes)).isoformat()}
    signature=hmac.new(secret.encode(),canonical(payload).encode(),hashlib.sha256).hexdigest()
    return {"payload":payload,"signature":signature}

def verify_approval(approval, incident, secret, now=None):
    now=now or utcnow()
    payload=approval.get("payload",{})
    signature=approval.get("signature","")
    expected=hmac.new(secret.encode(),canonical(payload).encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,signature): raise ValueError("approval signature invalid")
    if any(payload.get(k)!=incident[k] for k in ("host","service")) or payload.get("incident_id")!=incident["id"]:
        raise ValueError("approval bound to different incident")
    expiry=datetime.fromisoformat(payload["expires"])
    if now>=expiry: raise ValueError("approval expired")
    if incident["observed"]!="Stopped": raise ValueError("remediation not eligible")
    return True

def action_plan(incident,approval,secret,now=None):
    verify_approval(approval,incident,secret,now)
    # No host shell interpolation. This is a structured task ticket for a local operator.
    return {"host":incident["host"],"service":incident["service"],"action":"Start-Service","approval_id":approval["payload"]["nonce"],"requires_local_operator":True,"execution_status":"NOT_EXECUTED","verification":"Service status must be Running after local execution"}

def audit_append(path,event):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    previous="GENESIS"
    if path.exists():
        lines=path.read_text(encoding="utf-8").splitlines()
        if lines: previous=json.loads(lines[-1])["hash"]
    record={"at":utcnow().isoformat(),"event":event,"previous_hash":previous}
    record["hash"]=hashlib.sha256(canonical(record).encode()).hexdigest()
    with path.open("a",encoding="utf-8") as f: f.write(canonical(record)+"\n")
    return record

def audit_verify(path):
    previous="GENESIS"
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        record=json.loads(line)
        digest=record.pop("hash")
        if record["previous_hash"]!=previous or hashlib.sha256(canonical(record).encode()).hexdigest()!=digest:
            return False
        previous=digest
    return True
