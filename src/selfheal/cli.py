import argparse,json,os,sys
from pathlib import Path
from selfheal.core import load_policy,load_observations,evaluate,create_approval,action_plan,audit_append,audit_verify

def dump(v,path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(v,indent=2)+"\n",encoding="utf-8")

def main():
    p=argparse.ArgumentParser(description="Enterprise service monitoring; no automatic remediation")
    sub=p.add_subparsers(dest="cmd",required=True)
    scan=sub.add_parser("scan");scan.add_argument("--policy",default="config/policy.json");scan.add_argument("--observations",default="examples/service_observations.csv");scan.add_argument("--out",default="output/incidents.json");scan.add_argument("--audit",default="output/audit.jsonl")
    appr=sub.add_parser("approve");appr.add_argument("--incidents",default="output/incidents.json");appr.add_argument("--id",required=True);appr.add_argument("--operator",required=True);appr.add_argument("--out",default="output/approval.json");appr.add_argument("--audit",default="output/audit.jsonl")
    plan=sub.add_parser("plan");plan.add_argument("--incidents",default="output/incidents.json");plan.add_argument("--id",required=True);plan.add_argument("--approval",default="output/approval.json");plan.add_argument("--out",default="output/action_plan.json");plan.add_argument("--audit",default="output/audit.jsonl")
    check=sub.add_parser("verify-audit");check.add_argument("--audit",default="output/audit.jsonl")
    a=p.parse_args()
    try:
        if a.cmd=="scan":
            incidents=evaluate(load_policy(a.policy),load_observations(a.observations));dump(incidents,a.out);audit_append(a.audit,{"type":"SCAN","incidents":len(incidents)});print(f"Created {len(incidents)} incidents -> {a.out}")
        elif a.cmd=="verify-audit":
            result=audit_verify(a.audit);print("Audit valid" if result else "Audit tampered");return 0 if result else 1
        else:
            incidents=json.loads(Path(a.incidents).read_text(encoding="utf-8"))
            incident=next((i for i in incidents if i["id"]==a.id),None)
            if not incident: raise ValueError("incident ID not found")
            secret=os.getenv("SELFHEAL_APPROVAL_SECRET","")
            if len(secret)<24: raise ValueError("set SELFHEAL_APPROVAL_SECRET to 24+ character random secret")
            if a.cmd=="approve":
                approval=create_approval(incident,a.operator,secret);dump(approval,a.out);audit_append(a.audit,{"type":"APPROVAL_ISSUED","incident":a.id,"operator":a.operator});print(f"Approval issued -> {a.out}")
            else:
                approval=json.loads(Path(a.approval).read_text(encoding="utf-8"));task=action_plan(incident,approval,secret);dump(task,a.out);audit_append(a.audit,{"type":"ACTION_PLAN_CREATED","incident":a.id,"status":"NOT_EXECUTED"});print(f"Action plan created (NOT EXECUTED) -> {a.out}")
        return 0
    except (ValueError, OSError, KeyError, StopIteration) as e:
        print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__": raise SystemExit(main())
