// ─────────────────────────────────────────────────────────────
// HELPERS COMPARTILHADOS — cole no topo do Code node de qualquer
// template deste diretório. Snippet ÚNICO e canônico: o corpus tem 4
// implementações divergentes da mesma lógica de telefone (Nordmann,
// Degan, Meiskin, WL, AliveMed) — não reescreva, reutilize.
// ─────────────────────────────────────────────────────────────

// Normalizador de telefone BR completo.
// ⚠️ O ChatRace/NexTags adiciona '9' cegamente a fixos, corrompendo o ID
// do contato. Normalize ANTES de enviar. (lição Alto Giro)
function formatarTelefone(rawNumber) {
  if (!rawNumber) return '';
  let digits = String(rawNumber).replace(/\D/g, '');
  if (!digits) return '';
  // Caso 1: já vem com DDI 55 (12 ou 13 dígitos)
  if (digits.startsWith('55') && (digits.length === 12 || digits.length === 13)) {
    const ddd = digits.substring(2, 4);
    const dddInt = parseInt(ddd, 10);
    let local = digits.substring(4);
    if (dddInt >= 11 && dddInt <= 29) {
      if (/^[2345]/.test(local)) { if (local.length === 9 && local.startsWith('9')) local = local.substring(1); }
      else { if (!local.startsWith('9')) local = '9' + local; }
    } else if (dddInt >= 30 && dddInt <= 99) {
      if (local.length === 9 && local.startsWith('9')) local = local.substring(1);
    }
    return '55' + ddd + local;
  }
  // Caso 2: sem DDI (10 ou 11 dígitos)
  const ddd = digits.substring(0, 2);
  const dddInt = parseInt(ddd, 10);
  let local = digits.substring(2);
  if (dddInt >= 11 && dddInt <= 29) {
    if (/^[2345]/.test(local)) { if (local.length === 9 && local.startsWith('9')) local = local.substring(1); }
    else { if (!local.startsWith('9')) local = '9' + local; }
  } else if (dddInt >= 30 && dddInt <= 99) {
    if (local.length === 9 && local.startsWith('9')) local = local.substring(1);
  }
  return '55' + ddd + local;
}

// Validação FINAL do telefone já normalizado (padrão AliveMed — a mais
// defensiva do corpus). Se não bater, NÃO manda: zera e descarta.
function telefoneValido(tel) {
  return /^55\d{10,11}$/.test(String(tel || ''));
}

// ⚠️ FIXO NÃO RECEBE send_flow/mensagem via API: a NexTags acrescenta o 9
// e o número vira inválido (evidência: dono do projeto 2026-09-03;
// Alto Giro/ChatRace). Fixo = DDD + local de 8 dígitos começando em 2-5.
// Use SEMPRE como guard antes do disparo → skip(item, 'telefone_fixo').
function ehTelefoneFixo(tel) {
  const d = String(tel || '').replace(/\D/g, '');
  if (!/^55\d{10}$/.test(d)) return false;   // fixo normalizado tem 12 dígitos: 55 + DDD + 8
  const local = d.substring(4);
  return local.length === 8 && /^[2345]/.test(local);
}

// Skip AUDITÁVEL: todo descarte carrega o motivo (padrão Degan Carrinho
// Polling). Skip silencioso (`return []`) é indepurável.
// Motivos canônicos: sem_telefone | telefone_invalido | telefone_fixo |
//                    flow_id_ausente:<stage> | fora_da_janela | ja_convertido | dedup
function skip(item, motivo) {
  return [{ json: Object.assign({}, item || {}, { _skip: true, _motivo: motivo }) }];
}

// Guard completo de telefone: normaliza, valida e barra fixo.
// Retorna { ok:true, phone } ou { ok:false, motivo }.
function guardTelefone(bruto) {
  const phone = formatarTelefone(bruto);
  if (!phone) return { ok: false, motivo: 'sem_telefone' };
  if (!telefoneValido(phone)) return { ok: false, motivo: 'telefone_invalido' };
  if (ehTelefoneFixo(phone)) return { ok: false, motivo: 'telefone_fixo' };
  return { ok: true, phone };
}

// NexTags rejeita null/undefined no payload. Todo campo que vira CUF passa aqui.
// ⚠️ CUF vazio que alimenta variável de template derruba o template INTEIRO
// (erro Meta #131008) — por isso o fallback nunca é string vazia.
function verificarDado(dado, valorPadrao = 'Não informado') {
  return (dado !== null && dado !== undefined && dado !== '') ? dado : valorPadrao;
}

// /api/contacts espera first_name + last_name separados (campos NATIVOS, no root).
function separarNomeSobrenome(nomeCompleto) {
  if (!nomeCompleto || typeof nomeCompleto !== 'string') return { nome: '', sobrenome: '' };
  const partes = nomeCompleto.trim().split(/\s+/);
  const nome = partes.shift() || '';
  return { nome, sobrenome: partes.join(' ') || '' };
}

// Concatena UTM sem quebrar a query string (bug real Mayuí: colar '&' sem '?').
function comUTM(url, medium, campaign) {
  if (!url) return '';
  const sep = url.includes('?') ? '&' : '?';
  return `${url}${sep}utm_source=whatsapp&utm_medium=${medium}&utm_campaign=${campaign}`;
}

// Valor decimal como a NexTags espera no CUF: "379.00" (ponto, sem R$).
// Aceita tanto número/string já decimal ("379.00") quanto string formatada
// BR com separador de milhar ("R$ 1.234,56"): sem isso, o milhar em ponto
// vira um segundo ponto decimal e Number() retorna NaN -> corrompe pra "0.00"
// silenciosamente (bug real: valorTexto('1.538,00') virava '0.00').
function valorTexto(v) {
  let s = String(v == null ? '' : v).replace(/[^\d.,-]/g, '');
  if (s.includes(',')) {
    // formato BR: ponto = milhar (remove), vírgula = decimal (vira ponto)
    s = s.replace(/\./g, '').replace(',', '.');
  }
  const n = Number(s);
  return Number.isFinite(n) ? n.toFixed(2) : '0.00';
}
