#!/usr/bin/env python3
"""
parse_openapi.py — extrai estrutura essencial de uma OpenAPI 3.x spec
                   pra alimentar a geração de workflows MCP.

Uso:
    python parse_openapi.py <path-or-url> [--filter <substring>] [--output <json-path>]

Exemplos:
    python parse_openapi.py vtex-openapi.json --filter products --output vtex-products.json
    python parse_openapi.py https://api.example.com/openapi.json

Output:
    JSON estruturado com:
    - servers
    - securitySchemes (auth detectada)
    - endpoints (filtrados, com params + response shape)

Roda em Python 3.8+. Sem dependências externas (usa apenas stdlib).
"""
import json
import sys
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


def load_spec(path_or_url: str) -> dict:
    """Carrega OpenAPI spec de arquivo local ou URL."""
    if path_or_url.startswith(("http://", "https://")):
        try:
            with urllib.request.urlopen(path_or_url, timeout=10) as resp:
                content = resp.read().decode("utf-8")
        except urllib.error.URLError as e:
            sys.exit(f"Erro ao fetchar URL: {e}")
    else:
        p = Path(path_or_url)
        if not p.exists():
            sys.exit(f"Arquivo não encontrado: {path_or_url}")
        content = p.read_text(encoding="utf-8")

    # Detecta YAML vs JSON
    if path_or_url.endswith((".yaml", ".yml")):
        try:
            import yaml  # type: ignore
        except ImportError:
            sys.exit("Pra ler YAML, instale: pip install pyyaml")
        return yaml.safe_load(content)
    return json.loads(content)


def extract_servers(spec: dict) -> list[dict]:
    """Lista os ambientes/servers definidos na spec."""
    servers = spec.get("servers", [])
    return [
        {
            "url": s.get("url"),
            "description": s.get("description", ""),
            "variables": s.get("variables", {}),
        }
        for s in servers
    ]


def extract_security_schemes(spec: dict) -> dict:
    """Extrai securitySchemes (auth) com mapeamento sugerido pra n8n."""
    schemes = spec.get("components", {}).get("securitySchemes", {})
    result = {}
    for name, scheme in schemes.items():
        s_type = scheme.get("type")
        suggested_n8n_auth = None

        if s_type == "apiKey":
            in_ = scheme.get("in")
            param_name = scheme.get("name")
            if in_ == "header":
                suggested_n8n_auth = f"httpHeaderAuth (Name={param_name})"
            elif in_ == "query":
                suggested_n8n_auth = f"httpQueryAuth (Name={param_name})"
            elif in_ == "cookie":
                suggested_n8n_auth = "httpCustomAuth (cookie em header Cookie)"

        elif s_type == "http":
            scheme_name = scheme.get("scheme", "").lower()
            if scheme_name == "basic":
                suggested_n8n_auth = "httpBasicAuth"
            elif scheme_name == "bearer":
                suggested_n8n_auth = "httpHeaderAuth (Name=Authorization, Value='Bearer <token>')"

        elif s_type == "oauth2":
            flows = scheme.get("flows", {})
            if "authorizationCode" in flows:
                ac = flows["authorizationCode"]
                suggested_n8n_auth = (
                    "OAuth full (Caso B). Setup completo: "
                    f"authorize={ac.get('authorizationUrl')}, "
                    f"token={ac.get('tokenUrl')}, "
                    f"refresh={ac.get('refreshUrl', '(mesmo que token)')}"
                )
            elif "clientCredentials" in flows:
                suggested_n8n_auth = "OAuth client_credentials (sem refresh, trata como Caso A)"

        result[name] = {
            "type": s_type,
            "scheme": scheme.get("scheme"),
            "in": scheme.get("in"),
            "name": scheme.get("name"),
            "flows": scheme.get("flows"),
            "n8n_mapping_suggestion": suggested_n8n_auth or "manual (consultar auth_patterns.md)",
        }
    return result


def resolve_ref(spec: dict, ref: str) -> dict:
    """Resolve $ref simples (#/components/schemas/X)."""
    if not ref.startswith("#/"):
        return {}
    parts = ref[2:].split("/")
    obj: Any = spec
    for p in parts:
        if not isinstance(obj, dict) or p not in obj:
            return {}
        obj = obj[p]
    return obj if isinstance(obj, dict) else {}


def extract_response_shape(spec: dict, response_def: dict) -> dict:
    """Tenta extrair shape simplificado da response 200 (campos top-level)."""
    content = response_def.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])

    return _summarize_schema(schema, spec, depth=0)


def _summarize_schema(schema: dict, spec: dict, depth: int) -> dict:
    """Resume schema OpenAPI em estrutura simples (limite de profundidade)."""
    if depth > 3 or not isinstance(schema, dict):
        return {"_truncated": True}

    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])

    s_type = schema.get("type")

    if s_type == "object":
        props = schema.get("properties", {})
        return {
            "type": "object",
            "fields": {
                name: _summarize_schema(p, spec, depth + 1)
                for name, p in list(props.items())[:20]  # limita 20 fields
            },
        }
    elif s_type == "array":
        items = schema.get("items", {})
        return {"type": "array", "items": _summarize_schema(items, spec, depth + 1)}
    else:
        return {"type": s_type or "any", **({"format": schema["format"]} if "format" in schema else {})}


def extract_endpoints(spec: dict, filter_substring: str | None = None) -> list[dict]:
    """Lista endpoints relevantes com params + response shape resumido."""
    endpoints = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        if filter_substring and filter_substring.lower() not in path.lower():
            # Verifica também na descrição/summary dos methods
            descriptions = " ".join([
                str(path_item.get(m, {}).get("summary", "")) + " " + str(path_item.get(m, {}).get("description", ""))
                for m in ("get", "post", "put", "delete", "patch")
            ])
            if filter_substring.lower() not in descriptions.lower():
                continue

        for method in ("get", "post", "put", "delete", "patch"):
            op = path_item.get(method)
            if not op:
                continue

            params = []
            for p in op.get("parameters", []) + path_item.get("parameters", []):
                if "$ref" in p:
                    p = resolve_ref(spec, p["$ref"])
                params.append({
                    "name": p.get("name"),
                    "in": p.get("in"),
                    "required": p.get("required", False),
                    "type": p.get("schema", {}).get("type"),
                    "description": (p.get("description") or "")[:200],
                })

            responses = op.get("responses", {})
            success_resp = responses.get("200") or responses.get("201") or {}
            response_shape = extract_response_shape(spec, success_resp) if success_resp else None

            endpoints.append({
                "method": method.upper(),
                "path": path,
                "summary": op.get("summary", "")[:200],
                "description": (op.get("description") or "")[:500],
                "operationId": op.get("operationId"),
                "tags": op.get("tags", []),
                "parameters": params,
                "response_shape_summary": response_shape,
            })

    return endpoints


def main():
    parser = argparse.ArgumentParser(description="Parse OpenAPI 3.x spec pra MCP builder")
    parser.add_argument("spec", help="Path ou URL pra OpenAPI JSON/YAML")
    parser.add_argument("--filter", help="Filtrar endpoints por substring (em path, summary ou desc)")
    parser.add_argument("--output", help="Salvar JSON estruturado em arquivo")
    parser.add_argument("--summary-only", action="store_true", help="Só lista endpoints (sem response shape)")
    args = parser.parse_args()

    spec = load_spec(args.spec)

    result = {
        "title": spec.get("info", {}).get("title"),
        "version": spec.get("info", {}).get("version"),
        "servers": extract_servers(spec),
        "security_schemes": extract_security_schemes(spec),
        "endpoints": extract_endpoints(spec, args.filter),
    }

    if args.summary_only:
        for ep in result["endpoints"]:
            ep.pop("response_shape_summary", None)

    output_str = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"Salvo em {args.output}")
        print(f"Endpoints encontrados: {len(result['endpoints'])}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
