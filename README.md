# CortexDB

CortexDB unifica dados relacionais, vetoriais e arquivos binários em uma única API. O gateway está implementado em FastAPI com integrações para Postgres, Qdrant, MinIO e serviços Gemini da Google para embeddings e OCR.

## Pré-requisitos

- Docker e Docker Compose
- Chave de API do Google Gemini (`GEMINI_API_KEY`)

## Quickstart via Docker Hub

### Opção A – Script automático (recomendado)

```bash
curl -fsSL https://raw.githubusercontent.com/Dooor-AI/cortex-db/main/scripts/install.sh | bash
```

O script:
- verifica a presença de Docker/Compose;
- baixa `docker-compose.prod.yml` (caso não exista);
- cria `.env` pedindo `GEMINI_API_KEY` e `CORTEXDB_ADMIN_KEY` (ou usa valores pré-exportados);
- executa `docker compose pull` + `docker compose up -d`.

Execução automática com chave admin fornecida:

```bash
curl -fsSL https://raw.githubusercontent.com/Dooor-AI/cortex-db/main/scripts/install.sh | \
  bash -s -- --admin-key SUA_CHAVE_ADMIN
```

Também é possível passar `--gemini-key` e/ou evitar prompts com `--non-interactive`. Alternativamente, defina variáveis antes de rodar:

```bash
export GEMINI_API_KEY=...        # opcional
export CORTEXDB_ADMIN_KEY=...
curl -fsSL https://raw.githubusercontent.com/Dooor-AI/cortex-db/main/scripts/install.sh | bash
```

### Opção B – Somente `docker pull` + `docker run`

1. **Configure as variáveis**: tenha `GEMINI_API_KEY` e uma `CORTEXDB_ADMIN_KEY` forte.
2. **Crie a rede compartilhada** (os contêineres precisam se enxergar): `docker network create cortexnet || true`
3. **Suba cada serviço** (cada comando faz `docker pull` automático na primeira execução):

```bash
# Postgres
docker run -d --name cortex-postgres --network cortexnet \
  -e POSTGRES_USER=cortex -e POSTGRES_PASSWORD=cortex_pass -e POSTGRES_DB=cortex \
  -v cortex_pg:/var/lib/postgresql/data -p 5432:5432 postgres:16-alpine

# Qdrant
docker run -d --name cortex-qdrant --network cortexnet \
  -v cortex_qdrant:/qdrant/storage -p 6333:6333 -p 6334:6334 qdrant/qdrant:1.11.3

# MinIO
docker run -d --name cortex-minio --network cortexnet \
  -e MINIO_ROOT_USER=cortex -e MINIO_ROOT_PASSWORD=cortex_pass \
  -v cortex_minio:/data -p 9000:9000 -p 9001:9001 \
  minio/minio:RELEASE.2024-10-02T17-50-41Z server /data --console-address ":9001"

# Gateway (API)
docker run -d --name cortex-gateway --network cortexnet \
  -e CORTEXDB_ADMIN_KEY=com_uma_chave_forte \
  -e GEMINI_API_KEY=sua_chave_gemini \
  -e GEMINI_EMBEDDING_MODEL=models/text-embedding-004 \
  -e GEMINI_VISION_MODEL=models/gemini-1.5-flash \
  -p 8000:8000 brunolaureano/cortexdb-gateway:latest

# Studio (Next.js)
docker run -d --name cortex-studio --network cortexnet \
  -e CORTEX_GATEWAY_URL=http://cortex-gateway:8000 \
  -e NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000 \
  -e NODE_ENV=production \
  -p 3000:3000 brunolaureano/cortexdb-studio:latest
```

4. **Acesse**: `http://SEU_IP:8000/docs` (API), `http://SEU_IP:3000` (Studio), `http://SEU_IP:9001` (console MinIO).
5. **Parar/remover**: `docker stop cortex-studio cortex-gateway cortex-minio cortex-qdrant cortex-postgres && docker rm ...`
6. **Atualizar versão**: `docker pull brunolaureano/cortexdb-gateway:<tag>` + `docker pull brunolaureano/cortexdb-studio:<tag>` antes de reiniciar.

### Opção C – Docker Compose manual

Prefere manter um arquivo de stack? Baixe `docker-compose.prod.yml` e rode:

```bash
curl -LO https://raw.githubusercontent.com/Dooor-AI/cortex-db/main/docker-compose.prod.yml
cat <<'EOF' > .env
GEMINI_API_KEY=...sua chave...
CORTEXDB_ADMIN_KEY=...uma chave forte...
EOF
docker compose -f docker-compose.prod.yml up -d
```

O compose usa as imagens publicadas (`brunolaureano/cortexdb-gateway`, `brunolaureano/cortexdb-studio`) e configura `restart: unless-stopped` pelos serviços de infraestrutura.

## Como iniciar

1. Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY`.
2. Execute `docker-compose up --build` para iniciar os serviços.
3. para parar o docker serv ice, docker compose down
4. Utilize os schemas de exemplo em `schemas/` para criar collections.
5. A documentação interativa estará disponível em `http://localhost:8000/docs`.

## Frontend (CortexDB Studio)

Uma interface Next.js está disponível em `frontend/` para navegar pelas collections, registros e resultados de busca híbrida.

### Rodando em modo de desenvolvimento

```bash
cd frontend
cp .env.example .env.local  # ajuste NEXT_PUBLIC_GATEWAY_URL se necessário
npm install
npm run dev
```

Acesse `http://localhost:3000` para abrir o painel.
Acesse `http://localhost:8000/docs` para abrir o api docs.

### Via Docker Compose

Ao executar `docker-compose up --build`, o serviço `studio` fica disponível em `http://localhost:3000`, apontando automaticamente para o gateway (`NEXT_PUBLIC_GATEWAY_URL=http://gateway:8000`).

### Docker run (alternativa)

Detalhes completos no [Quickstart via Docker Hub](#quickstart-via-docker-hub) (Opção B).

## Estrutura

Consulte `docs/` para quickstart, referência de schema e endpoints.
