# CortexDB

CortexDB unifica dados relacionais, vetoriais e arquivos binários em uma única API. O gateway está implementado em FastAPI com integrações para Postgres, Qdrant, MinIO e serviços Gemini da Google para embeddings e OCR.

## Pré-requisitos

- Docker e Docker Compose
- Chave de API do Google Gemini (`GEMINI_API_KEY`)

## Como iniciar

1. Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY`.
2. Execute `docker-compose up --build` para iniciar os serviços.
3. Utilize os schemas de exemplo em `schemas/` para criar collections.
4. A documentação interativa estará disponível em `http://localhost:8000/docs`.

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

## Estrutura

Consulte `docs/` para quickstart, referência de schema e endpoints.
