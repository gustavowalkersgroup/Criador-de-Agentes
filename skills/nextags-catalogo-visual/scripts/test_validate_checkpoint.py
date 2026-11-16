#!/usr/bin/env python3
"""Testes do validate_checkpoint.py. Roda standalone (`python test_validate_checkpoint.py`) ou com pytest."""
import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import validate_checkpoint as vc


def run(inventory, lines):
    with tempfile.TemporaryDirectory() as d:
        inv, res = Path(d, "inv.json"), Path(d, "res.jsonl")
        inv.write_text(json.dumps(inventory), encoding="utf-8")
        res.write_text("\n".join(lines), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = vc.main(["--inventory", str(inv), "--results", str(res)])
        return code, json.loads(buf.getvalue())


def ok(**kw):
    base = {"status": "completed", "match_attributes": {"product_type": "sandália"}}
    base.update(kw)
    return json.dumps(base)


def test_cobertura_completa_por_product_id():
    code, out = run([{"product_id": "a"}, {"product_id": "b"}],
                    [ok(product_id="a"), ok(product_id="b")])
    assert code == 0 and out["coverage_complete"] is True


def test_marcador_sem_payload_nao_conta():
    code, out = run([{"product_id": "a"}], [json.dumps({"product_id": "a", "status": "completed"})])
    assert code == 1 and out["pending_ids"] == ["a"] and out["coverage_complete"] is False


def test_status_parcial_nao_conta():
    code, out = run([{"product_id": "a"}], [ok(product_id="a", status="partial_text_only")])
    assert code == 1 and out["valid_results_count"] == 0


def test_inventory_index_com_product_id_nulo_aponta_para_o_item():
    # inventário com ID, resultado só com índice (product_id nulo, como no schema recomendado)
    code, out = run([{"product_id": "x1"}, {"product_id": "x2"}],
                    [ok(product_id=None, inventory_index=1)])
    assert out["valid_results_count"] == 1 and out["pending_ids"] == ["x1"] and out["unknown_result_ids"] == []


def test_sem_id_no_inventario_usa_indice():
    code, out = run([{"name": "A"}, {"name": "B"}], [ok(inventory_index=0), ok(inventory_index=1)])
    assert code == 0 and out["coverage_complete"] is True


def test_duplicado_e_linha_invalida_bloqueiam():
    code, out = run([{"product_id": "a"}], [ok(product_id="a"), ok(product_id="a"), "{nao e json"])
    assert code == 1 and out["coverage_complete"] is False
    assert out["duplicate_result_ids"] and out["malformed_lines"]


def test_id_desconhecido_bloqueia():
    code, out = run([{"product_id": "a"}], [ok(product_id="a"), ok(product_id="zzz")])
    assert code == 1 and out["unknown_result_ids"] == ["zzz"]


def test_id_duplicado_no_inventario_e_erro():
    code, _ = (None, None)
    with tempfile.TemporaryDirectory() as d:
        inv = Path(d, "inv.json")
        inv.write_text(json.dumps([{"product_id": "a"}, {"product_id": "a"}]), encoding="utf-8")
        assert vc.main(["--inventory", str(inv), "--results", str(Path(d, "nao-existe.jsonl"))]) == 2


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} testes passaram")
