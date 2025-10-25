# CortexDB - Instruções de Desenvolvimento

## UI/Design
- **Tema obrigatório**: Dashboard dark com terminal vibes
- **Paleta de cores**: PRETO E BRANCO apenas - sem cores genéricos em cards
- **Tipografia**: IBM Plex Mono ou similar (fonte monospace)
- **Estilo**: Terminal/CLI aesthetic, ícones autênticos, sem elementos coloridos genéricos

## Frontend
- **IDIOMA OBRIGATÓRIO**: Todos os textos da UI devem estar em INGLÊS - labels, placeholders, mensagens de erro, botões, títulos, descrições, etc.
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

### ⚠️ IMPORTANTE: Serialização JSON/Dict
- **SEMPRE** verificar questões de dict vs JSON string em operações com Postgres JSONB
- Ao inserir: usar `json.dumps()` + `::jsonb` cast no SQL
- Ao ler: verificar se precisa `json.loads()` quando retorna string ao invés de dict
- Padrão comum: metadata, schema, e outros campos JSONB podem precisar parse
- PostgresClient usa `self.dsn` (NÃO `self._dsn`) - sempre verificar atributos corretos da classe

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


NUNCA RODE BUILDS OU RUN (A MENOS QUE PEDIDO PELO USUÁRIO)