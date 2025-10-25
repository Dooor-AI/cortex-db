# CortexDB - Instruções de Desenvolvimento

## UI/Design
- **Tema obrigatório**: Dashboard dark com terminal vibes
- **Paleta de cores**: PRETO E BRANCO apenas - sem cores genéricos em cards
- **Tipografia**: IBM Plex Mono ou similar (fonte monospace)
- **Estilo**: Terminal/CLI aesthetic, ícones autênticos, sem elementos coloridos genéricos

## Frontend
- Usar shadcn para componentes de UI
- Se um componente já existe (Button, Input, etc), SEMPRE reusar - nunca criar do zero
- Next.js está em `frontend/`
- Build de produção: `npm run build`

## Backend
- Gateway FastAPI em Python está em `gateway/`
- Postgres para dados estruturados
- Qdrant para vetores
- MinIO para arquivos
- Gemini para embeddings

## Banco de Dados
- **NÃO** usa Prisma (isso é um projeto Python, não Node.js no backend)
- Tabelas são gerenciadas via SQL direto no código Python
- Migrations acontecem automaticamente no startup via `postgres.py`

## Docker
- Sempre rodar via `docker compose up --build`
- Serviços: postgres, qdrant, minio, gateway, studio

## Embedding Providers
- Sistema de providers customizados implementado
- Cada collection pode ter seu próprio provider ou usar o padrão (env vars)
- API keys são armazenadas de forma segura no backend
- Frontend: `/settings/embeddings` para gerenciar providers

## Comandos CLI
- Para comandos bash/sh com timeout disponível: sempre usar timeouts longos (10 min+)
