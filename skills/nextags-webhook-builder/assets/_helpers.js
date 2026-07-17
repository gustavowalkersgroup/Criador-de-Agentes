// ─────────────────────────────────────────────────────────────
// HELPERS COMPARTILHADOS — cole no topo do Code node de qualquer
// template deste diretório. Validados em produção (referência Rafa).
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

// NexTags rejeita null/undefined no payload. Todo campo que vira CUF passa aqui.
function verificarDado(dado, valorPadrao = 'Não informado') {
  return (dado !== null && dado !== undefined && dado !== '') ? dado : valorPadrao;
}

// /api/contacts espera first_name + last_name separados.
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
