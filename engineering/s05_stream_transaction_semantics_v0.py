#!/usr/bin/env python3
"""Abstract host CPI transaction policy checks (not UART/CRC/ACK or RTL)."""
from dataclasses import dataclass,field
import hashlib,json
from pathlib import Path

@dataclass
class HostCPI:
    cpi_id:int
    provisional:dict=field(default_factory=dict)
    committed:bool=False
    aborted:bool=False
    def record(self,cpi_id,record_id,payload):
        if cpi_id!=self.cpi_id or self.committed or self.aborted: return False
        if record_id in self.provisional:
            return self.provisional[record_id]==payload # idempotent retransmit only
        self.provisional[record_id]=payload
        return True
    def commit(self,cpi_id,count):
        if cpi_id!=self.cpi_id or self.committed or self.aborted or not 0<=count<=702:
            return False
        if len(self.provisional)!=count or set(self.provisional)!=set(range(count)):
            return False
        self.committed=True
        return True
    def abort(self,cpi_id):
        if cpi_id!=self.cpi_id or self.committed:return False
        self.aborted=True
        self.provisional.clear()
        return True
    def disconnect(self):
        if not self.committed:
            self.aborted=True
            self.provisional.clear()
    def accepted_count(self):
        return len(self.provisional) if self.committed else 0

results={}
h=HostCPI(4001)
for n in range(702):
    assert h.record(4001,n,f"record_{n}")
assert h.record(4001,700,"record_700")  # duplicate ACK/retransmit
assert not h.record(4001,700,"altered_record") # conflicting duplicate
assert not h.commit(4001,701)
assert h.accepted_count()==0
assert h.commit(4001,702) and h.accepted_count()==702
assert not h.abort(4001)
results["full_702_commit_after_exact_count"]="PASS"
results["duplicate_identical_idempotent_conflicting_rejected"]="PASS"
results["mismatched_commit_count_rejected"]="PASS"
results["abort_after_commit_rejected"]="PASS"
m=HostCPI(4002)
for n in range(11):assert m.record(4002,n,f"record_{n}")
m.disconnect()
assert not m.commit(4002,11) and m.accepted_count()==0
results["all_records_arrived_but_link_lost_before_commit_invalid"]="PASS"
m=HostCPI(4003)
for n in range(20):assert m.record(4003,n,f"r{n}")
assert m.abort(4003) and m.accepted_count()==0
assert not m.commit(4003,20)
results["abort_after_partial_records_rolls_back"]="PASS"
m=HostCPI(4004)
assert m.commit(4004,0) and m.accepted_count()==0
results["empty_cpi_zero_count_commit"]="PASS"
m=HostCPI(4005)
assert m.record(4005,0,"r0") and m.record(4005,2,"r2")
assert not m.commit(4005,2)
results["missing_record_id_rejects_commit"]="PASS"
summary={
 "scope":"abstract host transaction-state policy only; no FPGA UART, FIFO, CRC, ACK or timeout",
 "semantics":"CPI_START -> TARGET_RECORDS -> CPI_COMMIT or CPI_ABORT; provisional until exact count verified",
 "cases":results,"passed":len(results),
 "tests_are_not_complete_link_verification":True,
 "REQ_LIST_01":"OPEN_NOT_PASS"}
path=Path("engineering/S05-TRANSACTION-SEMANTICS-EVIDENCE-v0.1.json")
path.write_text(json.dumps(summary,indent=2)+"\n")
print("ABSTRACT_HOST_POLICY_PASS",len(results),"cases")
for label in results:print("PASS",label)
print("EVIDENCE_SHA256",hashlib.sha256(path.read_bytes()).hexdigest())
