#!/usr/bin/env python3
"""
validate_brief.py — valida brief MÍNIMO da skill nextags-mcp-builder.

Escopo da skill é APENAS infraestrutura. Brief mínimo tem só 3 inputs:

  1. Nome da loja/cliente (pra naming dos workflows)
  2. Plataforma OU site (pra identificar qual recipe usar)
  3. Credenciais que o cliente já tem em mãos

Persona, flow_ids, cupons, política de envio, etc. NÃO vão aqui — esses
são responsabilidade da skill nextags-prompt-creator. Se aparecerem no
brief, são ignorados com aviso.

Uso:
    python validate_brief.py <brief.json>
    python validate_brief.py <brief.yaml>

Retorna exit 0 se ok, exit 1 se faltam campos críticos.

Estrutura mínima esperada:

{
  "cliente": {
    "nome": "Mayuí Fit Wear"        // OBRIGATÓRIO
  },
  "api": {
    "plataforma": "tray",            // OBRIGATÓRIO (ou "site")
    "site": "https://...",           // alternativa a plataforma
    "credenciais": {                 // OBRIGATÓRIO (não-vazio)
      "api_key": "...",
      "secret": "..."
    }
  }
}

Campos opcionais aceitos:
- cliente.slug (kebab-case) — se omitido, derivado do nome
- api.operacoes_extras — lista de operações além dos defaults da recipe
"""
import json
import sys
import re
from pathlib import Path


VALID_PLATFORMS = {
    "tray", "vtex", "shopify", "nuvemshop", "tiendanube",
    "bling", "martz", "yampi", "yever", "rd_station", "rd-station",
    "custom"  # pra API que ainda não tem recipe
}

OUT_OF_SCOPE_KEYS = {
    "persona", "tom_de_voz", "nome_agente", "nome_bot", "agente",
    "cupom", "cupom_venda", "cupom_desconto",
    "flow_id", "flow_id_sac", "flow_id_pipeline", "flow_ids",
    "politica_envio", "politica_troca", "prazo_envio",
    "cnpj", "endereco", "slogan", "slogan_marca",
    "frete_gratis", "horario_sac", "ticket_medio"
}


def get_nested(obj, path):
    parts = path.split(".")
    cur = obj
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def is_empty(v):
    if v is None:
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    if isinstance(v, (list, dict)) and len(v) == 0:
        return True
    return False


def derive_slug(nome):
    s = nome.lower()
    s = re.sub(r"[áàâãä]", "a", s)
    s = re.sub(r"[éèêë]", "e", s)
    s = re.sub(r"[íìîï]", "i", s)
    s = re.sub(r"[óòôõö]", "o", s)
    s = re.sub(r"[úùûü]", "u", s)
    s = re.sub(r"[ç]", "c", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def validate(brief):
    errors = []
    warnings = []

    nome = get_nested(brief, "cliente.nome")
    if is_empty(nome):
        errors.append("cliente.nome — Nome da loja/cliente (pra naming dos workflows no n8n)")

    plataforma = get_nested(brief, "api.plataforma")
    site = get_nested(brief, "api.site")
    if is_empty(plataforma) and is_empty(site):
        errors.append("api.plataforma OU api.site — qual API REST consumir (Tray/VTEX/Shopify/Nuvemshop/Bling/Martz/Yampi/Yever/RD Station/custom)")
    elif plataforma and plataforma.lower() not in VALID_PLATFORMS:
        warnings.append(
            f"api.plataforma='{plataforma}' nao esta na lista conhecida. "
            f"Vai precisar criar recipe nova. Conhecidas: {sorted(VALID_PLATFORMS)}"
        )

    creds = get_nested(brief, "api.credenciais")
    if is_empty(creds):
        errors.append("api.credenciais — credenciais fornecidas pelo cliente (varia por plataforma; ver recipe)")
    elif not isinstance(creds, dict):
        errors.append("api.credenciais — deve ser um objeto/dict")
    elif not any(not is_empty(v) for v in creds.values()):
        errors.append("api.credenciais — todos os campos estao vazios")

    slug = get_nested(brief, "cliente.slug")
    if is_empty(slug) and not is_empty(nome):
        suggested = derive_slug(nome)
        warnings.append(f"cliente.slug ausente. Sugestao derivada do nome: '{suggested}'")

    out_of_scope_found = []

    def scan(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                full = f"{prefix}.{k}" if prefix else k
                if k.lower() in OUT_OF_SCOPE_KEYS:
                    out_of_scope_found.append(full)
                if isinstance(v, (dict, list)):
                    scan(v, full)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                scan(item, f"{prefix}[{i}]")

    scan(brief)

    return errors, warnings, out_of_scope_found


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    p = Path(sys.argv[1])
    if not p.exists():
        sys.exit(f"Arquivo nao encontrado: {p}")

    content = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            sys.exit("Pra YAML, instale: pip install pyyaml")
        brief = yaml.safe_load(content)
    else:
        brief = json.loads(content)

    if not isinstance(brief, dict):
        sys.exit("Brief deve ser um objeto JSON/YAML no topo")

    errors, warnings, out_of_scope = validate(brief)

    print(f"\n[Validacao] {p.name}\n")

    if errors:
        print(f"[ERRO] {len(errors)} campo(s) obrigatorio(s) faltando:")
        for e in errors:
            print(f"  - {e}")
        print()

    if warnings:
        print(f"[AVISO] {len(warnings)} ponto(s) de atencao:")
        for w in warnings:
            print(f"  - {w}")
        print()

    if out_of_scope:
        print(f"[FORA DE ESCOPO] {len(out_of_scope)} campo(s) ignorados:")
        for k in out_of_scope:
            print(f"  - {k}")
        print(
            "  Esses campos sao de responsabilidade da skill nextags-prompt-creator,\n"
            "  nao do nextags-mcp-builder. Sao ignorados na geracao da infra.\n"
        )

    if not errors:
        print("[OK] Brief minimo valido. Pode prosseguir pra geracao de infra.\n")
        sys.exit(0)
    else:
        print("[BLOQUEADO] Brief nao esta pronto. Complete os campos obrigatorios.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
