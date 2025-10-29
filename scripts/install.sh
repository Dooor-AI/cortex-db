#!/usr/bin/env bash

set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
COMPOSE_URL="https://raw.githubusercontent.com/Dooor-AI/cortex-db/main/${COMPOSE_FILE}"

log() {
  printf "[cortexdb] %s\n" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Erro: comando '$1' não encontrado. Instale-o e tente novamente."
    exit 1
  fi
}

usage() {
  cat <<'EOF'
Uso: install.sh [opções]

Opções:
  --admin-key <valor>   Define o CORTEXDB_ADMIN_KEY sem prompt
  --gemini-key <valor>  Define o GEMINI_API_KEY sem prompt
  --non-interactive     Falha se valores obrigatórios estiverem ausentes
  -h, --help            Mostra esta ajuda

Exemplo:
  curl -fsSL https://raw.githubusercontent.com/Dooor-AI/cortex-db/main/scripts/install.sh | \
    bash -s -- --admin-key minha_chave_segura
EOF
}

CORTEXDB_ADMIN_KEY=${CORTEXDB_ADMIN_KEY:-}
GEMINI_API_KEY=${GEMINI_API_KEY:-}
NON_INTERACTIVE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --admin-key)
      if [[ $# -lt 2 ]]; then
        log "Erro: --admin-key requer um valor"
        usage
        exit 1
      fi
      CORTEXDB_ADMIN_KEY="$2"
      shift 2
      ;;
    --gemini-key)
      if [[ $# -lt 2 ]]; then
        log "Erro: --gemini-key requer um valor"
        usage
        exit 1
      fi
      GEMINI_API_KEY="$2"
      shift 2
      ;;
    --non-interactive)
      NON_INTERACTIVE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log "Erro: argumento desconhecido '$1'"
      usage
      exit 1
      ;;
  esac
done

require_cmd curl
require_cmd docker

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  log "Erro: nem 'docker compose' nem 'docker-compose' estão disponíveis. Atualize o Docker ou instale o docker-compose."
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  log "Baixando ${COMPOSE_FILE}…"
  curl -fsSL "$COMPOSE_URL" -o "$COMPOSE_FILE"
else
  log "Usando ${COMPOSE_FILE} existente. Apague o arquivo se quiser baixá-lo novamente."
fi

if [ -f "$ENV_FILE" ]; then
  log "Arquivo ${ENV_FILE} já existe. Mantendo valores atuais."
else
  if [ -z "$GEMINI_API_KEY" ]; then
    if $NON_INTERACTIVE; then
      log "Erro: GEMINI_API_KEY não definido (use --gemini-key ou export GEMINI_API_KEY)."
      exit 1
    fi
    read -rp "Informe o GEMINI_API_KEY: " GEMINI_API_KEY
  fi

  if [ -z "$CORTEXDB_ADMIN_KEY" ]; then
    if $NON_INTERACTIVE; then
      log "Erro: CORTEXDB_ADMIN_KEY não definido (use --admin-key, export, ou remova --non-interactive)."
      exit 1
    fi
    read -rp "Informe o CORTEXDB_ADMIN_KEY (vazio para gerar automaticamente): " CORTEXDB_ADMIN_KEY || true
    if [ -z "$CORTEXDB_ADMIN_KEY" ]; then
      if command -v openssl >/dev/null 2>&1; then
        CORTEXDB_ADMIN_KEY=$(openssl rand -hex 24)
      else
        CORTEXDB_ADMIN_KEY=$(python3 - <<'EOF'
import secrets
print(secrets.token_hex(24))
EOF
)
      fi
      log "Chave admin gerada automaticamente. Guarde-a com segurança: ${CORTEXDB_ADMIN_KEY}"
    fi
  fi

  cat > "$ENV_FILE" <<EOF
GEMINI_API_KEY=${GEMINI_API_KEY}
CORTEXDB_ADMIN_KEY=${CORTEXDB_ADMIN_KEY}
EOF

  log "Arquivo ${ENV_FILE} criado."
fi

log "Baixando imagens necessárias (docker compose pull)…"
$COMPOSE_CMD -f "$COMPOSE_FILE" pull

log "Subindo serviços (docker compose up -d)…"
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d

log "CortexDB disponível em http://localhost:8000/docs e http://localhost:3000"
log "Use '$COMPOSE_CMD -f $COMPOSE_FILE down' para parar os serviços."
