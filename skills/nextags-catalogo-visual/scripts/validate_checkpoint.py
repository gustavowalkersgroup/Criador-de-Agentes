#!/usr/bin/env python3
"""Valida o inventário de um catálogo (JSON) e o checkpoint de resultados (JSONL)."""
import argparse
import json
import sys
from pathlib import Path


def load_inventory(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        products = data
    elif isinstance(data, dict):
        products = data.get("products") or data.get("items")
    else:
        products = None
    if not isinstance(products, list):
        raise ValueError("o inventário precisa ser um array JSON ou um objeto com o array products/items")
    return products


def get_id(record, index, id_field):
    value = record.get(id_field)
    return str(value) if value is not None else f"index:{index}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True, help="arquivo JSON do inventário")
    parser.add_argument("--results", required=True, help="checkpoint de resultados em JSONL")
    parser.add_argument("--id-field", default="product_id",
                        help="campo do ID estável; sem ele, vale o índice do item no inventário")
    parser.add_argument("--name-field", default="name", help="campo do nome do produto (informativo)")
    args = parser.parse_args(argv)

    try:
        products = load_inventory(args.inventory)
    except Exception as exc:
        print(f"ERRO inventário: {exc}", file=sys.stderr)
        return 2

    inventory_ids = {}
    ordered_keys = []
    for i, record in enumerate(products):
        if not isinstance(record, dict):
            print(f"ERRO inventário[{i}] não é um objeto", file=sys.stderr)
            return 2
        key = get_id(record, i, args.id_field)
        if key in inventory_ids:
            print(f"ERRO ID duplicado no inventário {key!r} nos índices {inventory_ids[key]} e {i}", file=sys.stderr)
            return 2
        inventory_ids[key] = i
        ordered_keys.append(key)

    valid = {}
    malformed = []
    duplicate_results = []
    results_path = Path(args.results)
    if results_path.exists():
        for line_no, line in enumerate(results_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("a linha não é um objeto JSON")
            except Exception as exc:
                malformed.append((line_no, str(exc)))
                continue
            if args.id_field in record and record[args.id_field] is not None:
                key = str(record[args.id_field])
            elif "inventory_index" in record:
                idx = record["inventory_index"]
                # product_id nulo no resultado: o índice aponta para o item do inventário
                if isinstance(idx, int) and not isinstance(idx, bool) and 0 <= idx < len(ordered_keys):
                    key = ordered_keys[idx]
                else:
                    key = f"index:{idx}"
            else:
                malformed.append((line_no, "sem product_id e sem inventory_index"))
                continue
            if key in valid:
                duplicate_results.append((key, valid[key][0], line_no))
                continue
            status = record.get("status", record.get("analysis_status", ""))
            # Marcador de conclusão sem payload analítico não vale como resultado.
            attrs = record.get("match_attributes") or record.get("analysis_record")
            has_payload = bool(record.get("visual_first_image") or record.get("official_description_summary") or attrs)
            if status in {"completed", "analyzed", "success"} and has_payload:
                valid[key] = (line_no, record)

    unknown = sorted(k for k in valid if k not in inventory_ids)
    done = {k for k in valid if k in inventory_ids}
    missing = [k for k in inventory_ids if k not in done]
    print(json.dumps({
        "inventory_count": len(products),
        "valid_results_count": len(done),
        "pending_count": len(missing),
        "pending_ids": missing,
        "unknown_result_ids": unknown,
        "malformed_lines": [{"line": n, "error": e} for n, e in malformed],
        "duplicate_result_ids": [{"id": k, "first_line": a, "duplicate_line": b} for k, a, b in duplicate_results],
        "coverage_complete": len(done) == len(products) and not malformed and not duplicate_results and not unknown
    }, ensure_ascii=False, indent=2))
    return 1 if malformed or duplicate_results or unknown or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
