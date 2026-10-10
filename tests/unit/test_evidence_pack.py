from core.evidence.pack import EvidencePack
from core.audit_chain import append_chained
import hashlib


def test_evidence_zip_and_manifest(tmp_path, monkeypatch):
    logs = tmp_path / "logs"
    logs.mkdir()
    audit = logs / "cma_audit.jsonl"
    append_chained(audit, {
        "action": "block_ip", "target": "203.0.113.50", "severity": "HIGH",
        "legislative_justification": "test", "tag": "TT_CMA_TAG", "source": "CyberFortress",
    })
    monkeypatch.chdir(tmp_path)
    pack = EvidencePack(client_name="Demo", engagement_id="ENG-TEST")
    n = pack.load_from_audit_log(str(audit))
    assert n >= 1
    import core.evidence.pack as ep
    ep.EVIDENCE_ROOT = tmp_path / "evidence"
    d = pack.build()
    assert (d / "01_Executive_Report.md").exists()
    assert (d / "02_Full_Audit.json").exists()
    assert (d / "MANIFEST.sha256").exists()
    z = pack.zip()
    assert z.exists() and z.suffix == ".zip"
    for line in (d / "MANIFEST.sha256").read_text().splitlines():
        digest, name = line.split()
        assert hashlib.sha256((d / name).read_bytes()).hexdigest() == digest
