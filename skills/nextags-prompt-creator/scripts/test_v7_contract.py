#!/usr/bin/env python3
"""Static contract checks for the V7 prompt-creator architecture."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text()
required_refs = [
    "arquitetura_suprema_v7.md",
    "campos_canonicos.md",
    "regras_absolutas.md",
    "contrato_canonico_ecommerce.md",
    "fluxos_canonicos_walkers.md",
]
required_rules = [
    "Truth before fluency",
    "Runtime truth",
    "Classify actions A0–A5",
    "P0/P1",
    "prompt injection",
    "send_flow",
    "stale state",
    "4–6",
]
assert len(skill.splitlines()) < 500, "SKILL.md must stay under 500 lines"
for ref in required_refs:
    assert ref in skill, f"missing navigation reference: {ref}"
    assert (ROOT / "references" / ref).is_file(), f"missing reference file: {ref}"
for rule in required_rules:
    assert rule.lower() in skill.lower(), f"missing V7 rule: {rule}"
assert not re.search(r"Transactonal|Transational", skill), "flow category typo"
assert "1782490224812" not in skill, "account-specific IDs must remain in references"
print("V7 contract: PASS")
print(f"SKILL.md lines: {len(skill.splitlines())}")
print(f"References checked: {len(required_refs)}")
