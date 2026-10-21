import json, tempfile, unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from selfheal.core import validate_policy,evaluate,create_approval,verify_approval,action_plan,audit_append,audit_verify

POLICY={"targets":[{"host":"LAB-FS1","service":"Spooler","expected":"Running"}]}
OBS=[{"host":"LAB-FS1","service":"Spooler","status":"Stopped","timestamp":"2026-10-20T10:00:00Z"}]
SECRET="demo-very-long-random-test-secret-123"
class CoreTests(unittest.TestCase):
 def test_stopped_generates_incident(self):
  inc=evaluate(validate_policy(POLICY),OBS)
  self.assertEqual(len(inc),1);self.assertEqual(inc[0]["automated_action"],"NONE")
 def test_running_no_incident(self):
  self.assertEqual(evaluate(POLICY,[dict(OBS[0],status="Running")]),[])
 def test_unknown_generates_nonrecoverable_incident(self):
  self.assertEqual(evaluate(POLICY,[])[0]["observed"],"Unknown")
 def test_latest_wins(self):
  newer=dict(OBS[0],status="Running",timestamp="2026-10-20T11:00:00Z")
  self.assertEqual(evaluate(POLICY,[newer,OBS[0]]),[])
 def test_policy_rejects_unauthorized_host(self):
  with self.assertRaises(ValueError): validate_policy({"targets":[{"host":"prod-1","service":"Spooler","expected":"Running"}]})
 def test_policy_rejects_unauthorized_service(self):
  with self.assertRaises(ValueError): validate_policy({"targets":[{"host":"LAB-FS1","service":"TermService","expected":"Running"}]})
 def test_policy_rejects_duplicates(self):
  with self.assertRaises(ValueError): validate_policy({"targets":POLICY["targets"]*2})
 def test_approval_expiry(self):
  inc=evaluate(POLICY,OBS)[0];now=datetime(2026,10,20,tzinfo=timezone.utc)
  ap=create_approval(inc,"lab-operator",SECRET,now=now)
  with self.assertRaises(ValueError): verify_approval(ap,inc,SECRET,now+timedelta(hours=1))
 def test_approval_wrong_secret(self):
  inc=evaluate(POLICY,OBS)[0];ap=create_approval(inc,"lab-operator",SECRET)
  with self.assertRaises(ValueError): verify_approval(ap,inc,"another-long-secret-1234567890")
 def test_approval_binding(self):
  inc=evaluate(POLICY,OBS)[0];ap=create_approval(inc,"lab-operator",SECRET)
  other=dict(inc,service="Dnscache")
  with self.assertRaises(ValueError): verify_approval(ap,other,SECRET)
 def test_plan_is_not_execution(self):
  inc=evaluate(POLICY,OBS)[0];ap=create_approval(inc,"lab-operator",SECRET)
  self.assertEqual(action_plan(inc,ap,SECRET)["execution_status"],"NOT_EXECUTED")
 def test_non_stopped_cannot_approve(self):
  inc=evaluate(POLICY,[])[0]
  with self.assertRaises(ValueError): create_approval(inc,"lab-operator",SECRET)
 def test_audit_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"audit.jsonl";audit_append(path,{"type":"SCAN"});audit_append(path,{"type":"APPROVAL"})
   self.assertTrue(audit_verify(path))
   t=path.read_text();path.write_text(t.replace('SCAN','FAKE'))
   self.assertFalse(audit_verify(path))
if __name__=="__main__": unittest.main()
