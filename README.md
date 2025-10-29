# CortexDB

CortexDB unifica dados relacionais, vetoriais e arquivos binários em uma única API. O gateway está implementado em FastAPI com integrações para Postgres, Qdrant, MinIO e serviços Gemini da Google para embeddings e OCR.

## Pré-requisitos

- Docker e Docker Compose
- Chave de API do Google Gemini (`GEMINI_API_KEY`)

## Quickstart via Docker Hub (sem clonar o repositório)

Use o arquivo de produção com imagens publicadas no Docker Hub (gateway e studio) e imagens oficiais (Postgres, Qdrant, MinIO):

1. Crie um arquivo `.env` no diretório onde rodará o compose, contendo:

```
GEMINI_API_KEY=...sua chave...
CORTEXDB_ADMIN_KEY=...uma-chave-forte...
```

2. Baixe o `docker-compose.prod.yml` deste repositório (ou copie o conteúdo) e rode:

```bash
docker compose -f docker-compose.prod.yml up -d
```

3. Acesse `http://localhost:8000/docs` (API) e `http://localhost:3000` (Studio).

Observações:
- Em produção, use um `CORTEXDB_ADMIN_KEY` forte e configure TLS por trás de um proxy (Caddy/Traefik/Nginx).
- Para persistência, os volumes `postgres_data`, `qdrant_data` e `minio_data` são mapeados automaticamente.

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

### Docker run (alternativa sem Compose)

Se preferir comandos `docker run` separados (ex.: em uma VM sem compose), crie uma rede e suba os serviços:

```bash
docker network create cortexnet || true

# Postgres
docker run -d --name cortex-postgres --network cortexnet \
  -e POSTGRES_USER=cortex -e POSTGRES_PASSWORD=cortex_pass -e POSTGRES_DB=cortex \
  -v cortex_pg:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16-alpine

# Qdrant
docker run -d --name cortex-qdrant --network cortexnet \
  -v cortex_qdrant:/qdrant/storage \
  -p 6333:6333 -p 6334:6334 \
  qdrant/qdrant:latest

# MinIO
docker run -d --name cortex-minio --network cortexnet \
  -e MINIO_ROOT_USER=cortex -e MINIO_ROOT_PASSWORD=cortex_pass \
  -v cortex_minio:/data \
  -p 9000:9000 -p 9001:9001 \
  minio/minio:latest server /data --console-address ":9001"

# Gateway (CortexDB API)
docker run -d --name cortex-gateway --network cortexnet \
  -e CORTEXDB_ADMIN_KEY=...uma-chave-forte... \
  -e GEMINI_API_KEY=...sua-chave... \
  -e GEMINI_EMBEDDING_MODEL=models/text-embedding-004 \
  -e GEMINI_VISION_MODEL=models/gemini-1.5-flash \
  -p 8000:8000 \
  brunolaureano/cortexdb-gateway:latest

# Studio (painel Next.js)
docker run -d --name cortex-studio --network cortexnet \
  -e CORTEX_GATEWAY_URL=http://cortex-gateway:8000 \
  -e NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000 \
  -e NODE_ENV=production \
  -p 3000:3000 \
  brunolaureano/cortexdb-studio:latest
```

Volumes nomeados: `cortex_pg`, `cortex_qdrant`, `cortex_minio`. Remova `-p` se expor por proxy reverso com TLS.

## Estrutura

Consulte `docs/` para quickstart, referência de schema e endpoints.
