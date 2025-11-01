# FroDB Vision & Technical Overview

## 1. Motivação: Por que a Dooor está construindo a FroDB

A Dooor opera como uma empresa de infraestrutura de IA e comunicação entre agentes com requisitos fortes de privacidade, verificação e incentivo a desenvolvedores. A plataforma combina:

- Ambientes de execução confiáveis baseados em TEEs (AMD SEV-SNP, Intel TDX, NVIDIA H100 Confidential Computing)
- Orquestração multi-agente (NestJS + LangGraph + BentoML)
- Contas multisig, tokenização de modelos e integrações DePIN quando necessário

Esse cenário demanda uma camada de dados que consiga unificar três dimensões que geralmente ficam separadas:

1. **Dados estruturados** para metadados e governança (ex.: permissões, contas multisig, auditorias)
2. **Dados vetoriais** para embeddings de texto, imagens, áudio e documentos
3. **Arquivos binários** (PDFs, planilhas, imagens, artefatos de modelos) com versionamento e políticas de retenção

Soluções isoladas existentes (Postgres, Qdrant, MinIO, Elastic, etc.) resolvem cada aspecto separadamente, mas impõem fricção na orquestração entre agentes: é difícil garantir atomicidade, rastreabilidade, versionamento conjunto e trilhas de auditoria quando as fontes de dados ficam espalhadas. A FroDB nasce para oferecer **uma API unificada** para a stack da Dooor, com garantias de segurança compatíveis com TEEs e integrações plug-and-play com os pipelines internos de agentes.

## 2. O que a FroDB oferece

- **Gateway único (FastAPI)** que coordena Postgres, Qdrant e MinIO como se fossem um só repositório lógico
- **Schemas declarativos** (via JSON) capazes de desenhar coleções híbridas: campos relacionais, campos vetoriais (com flags `vectorize` ou `store_in=[qdrant]`), blobs armazenados em bucket e metadados ricos
- **Suporte nativo a geração de embeddings e visão** com conectores para Gemini, OpenAI (text-embedding-3, o3-mini), Anthropic Claude (Tool use/Haiku), Voyage/BGE e modelos self-hosted via BentoML. A escolha do provider pode ser definida por schema, agente ou política centralizada, garantindo privacidade e conformidade.
- **MinIO** como camada de objetos S3-compatível com bucket por coleção, versionamento e trilhas de auditoria
- **Bootstrap automático** de chaves de API administrativas, com política de hash e prefixo para integração com o gerenciador de credenciais da Dooor
- **Frontend Studio (Next.js)** que expõe painéis para criação de bancos, coleções, schemata, ingestão de registros e visualização de resultados de busca híbrida
- **Playground Docling**: ingestão de documentos com OCR, conversão estruturada e vetorizações assistidas pelo `docling` (stack PDF da equipe de research)
- **Pipeline de imagens Docker multi-arquitetura** (amd64 + arm64) para ser executado em VMs x86 (GCP) e também em clusters com ARM (ex.: AWS Graviton, Macs M-series)

Esses blocos foram pensados para reduzir fricção entre squads de plataforma e times que constroem agentes/aplicações. A FroDB abstrai detalhes de conexão, versionamento de bucket, políticas de retention, reprocessamento de embeddings e logging estruturado. Cada mudança de schema gera eventos que podem alimentar LangGraph, enquanto o controle de acesso segue o modelo mínimo de privilégios exigido em ambientes regulados.

### 2.1 Decisões de design

- **API-first**: todo fluxo do Studio é um cliente da API do gateway; a documentação pública será exportada como OpenAPI, permitindo SDKs automáticos (TypeScript, Python, Go) usados pelos agentes.
- **Idempotência e retries**: ingestões e atualizações são idempotentes por design. Caso Qdrant ou MinIO falhe, o gateway registra tentativa e retoma com retentativa exponencial, evitando estados “meio salvos”.
- **Observabilidade contextual**: logs incluem `request_id`, `agent_id`, `db`, `collection` e `provider escolhido`, facilitando auditorias e cálculos de custo por cliente.
- **Config declarativa**: variáveis de ambiente (pref & defaults) permitem que equipes ajustem providers, limites de tamanho, políticas de retenção e timeouts conforme o ambiente (dev, staging, produção confidencial).

## 3. Arquitetura Técnica

### Componentes principais

| Componente | Função | Notas |
|------------|--------|-------|
| **Gateway (FastAPI)** | API REST unificada (`/databases`, `/collections`, `/records`, `/providers`, `/files`) | Executa bootstrap de chaves, sincroniza Postgres, enfileira jobs Gemini, publica eventos |
| **Postgres 16** | Fonte de verdade dos metadados, transações, permissões e payloads estruturados | Usamos `asyncpg` + migrações Alembic (em roadmap) |
| **Qdrant** | Vector search, payloads, filtragem híbrida (SIMD/ANN + filtros JSON) | Config padrão, volumes persistentes, upgrade path fácil |
| **MinIO** | Arquivos binários, versões originais de documentos, anexos, artefatos | Buckets por coleção com naming sanitizado |
| **Providers de embeddings/visão** | Conectores para Gemini, OpenAI, Anthropic (Claude), Voyage/BGE e modelos self-hosted | Seleção por schema/política; respeita limites de privacidade e custo |
| **Studio (Next.js 14)** | UI administrativa para times internos e parceiros | Rotas segmentadas por banco/coleção, usa `@/lib/cortex-client` |
| **Playground Docling** | Scripts Python para ingestão massiva e experimentos com embeddings/OCR | Ajustado para pipelines de compliance |

### Fluxo de ingestão de dados

1. Cliente envia `POST /collections/{name}/records` com JSON + arquivos (multipart)
2. Gateway normaliza o payload conforme schema:
   - Campos `store_in: postgres` são persistidos transacionalmente
   - Campos `vectorize` ou `store_in: qdrant` disparam pipeline de embeddings -> Qdrant
   - Campos `FILE` são enviados ao MinIO (com versionamento) e guardamos referencias na linha do Postgres/Qdrant payload
3. Transação somente é confirmada quando todas as partes retornam sucesso; caso contrário, rollback + cleanup de objetos temporários

### Integração com TEEs e segurança

- Os serviços podem ser empacotados em imagens “confidential containers” com runtime compatível (Confidential GKE, Azure CC)
- Chaves de API podem ser emitidas dentro de TEEs (ex.: processo de bootstrap controlado por attestation report)
- Metadata sensível pode ser criptografada em repouso via extensões Postgres (pgcrypto ou envelope keys KMS), e MinIO suporta SSE-KMS
- Todos os serviços expostos via Compose usam TLS opcional; para produção, recomendamos proxy reverso (Caddy/Traefik) com mTLS entre agentes

## 4. Integração com o ecossistema da Dooor

### Multi-agente & LangGraph
- Cada agente cadastrado no orquestrador terá uma chave de API gerenciada pela FroDB
- A modulação de permissões (`APIKeyPermissions`) permite restringir acesso por database/coleção, essencial para compartimentar times e fluxos de receita
- Logs de operações ficam disponíveis para trilhas de auditoria e atribuição de incentivos financeiros a desenvolvedores

### Infra confidential & DePIN
- Os conectores do gateway serão enviados para enclaves que processam dados sensíveis com atestação remota
- Projetos DePIN que dependem de storage/computação podem consumir FroDB como backend unificado, facilitando encadeamento de jobs (ex.: pipeline OCR -> embeddings -> proposta de pagamento)

### Roadmap interno
- **v0.2**: replicação multi-região (Patroni ou CloudSQL), streaming de eventos para LangGraph e caching de consultas vetoriais frequentes com warm indexes.
- **v0.3**: modo “standalone” (imagem única para demos), suporte oficial a embeddings self-hosted (BGE, Voyage, open-source multimodal) e otimizações em Qdrant (tuning de HNSW, shards adaptativos, quantização vetorial) para latência menor que alternativas padrão.
- **v0.4**: integrações com ledger (versionamento de coleções/records em blockchain permissionada), triggers assináveis e write-ahead vector logs para replay em auditorias.
- **v0.5**: camadas inspiradas em **medallion architecture** (bronze/silver/gold) acopladas a um data lake (Iceberg/Delta), com ingestão incremental e publicação automática do ouro na FroDB para consumo por agentes.
- **v0.6**: query planner híbrido que compartilha estatísticas entre Postgres e Qdrant, pré-carrega embeddings em TEEs com GPU e aplica compressão adaptativa para arquivos binários (vídeo/imagem/3D) visando throughput superior.
- **v0.6**: query planner híbrido que compartilha estatísticas entre Postgres e Qdrant, pré-carrega embeddings em TEEs com GPU e aplica compressão adaptativa para arquivos binários (vídeo/imagem/3D) visando throughput superior.
- **Pesquisa contínua**: avaliar novos backends vetoriais (ex.: TiDB Vector, Milvus) e extensões Postgres (pgvector v0.5+, Neon/pgmq) para manter a FroDB competitiva em latência e custo.

### 7.1 Query planner híbrido & aceleração multimodal

O item de roadmap “v0.6” merece atenção especial porque representa o salto em inteligência operacional da FroDB. A proposta envolve três pilares:

1. **Comparti lhamento de estatísticas entre Postgres e Qdrant**
   - Cada coleção possui uma visão combinada das cardinalidades, distribuição de filtros e padrões de consulta. Planejamos construir um “statistics service” que coleta amostras representativas (histogramas, count distinct, quantis) tanto de tabelas do Postgres quanto de payloads/Qdrant.
   - Com base nessas estatísticas, o gateway poderá escolher em tempo de execução a melhor estratégia: aplicar filtros no Postgres antes da consulta vetorial, usar `payload` filters do Qdrant, ou combinar ambos. Isso reduz overfetch e melhora latência em cenários com filtros complexos.

2. **Pré-carregamento de embeddings em TEEs com GPU**
   - Para workloads high-throughput (ex.: busca multimodal em tempo real), iremos preparar um “vector cache” residente em enclaves com GPU. A ideia é manter embeddings quentes em memória protegida, com uso de frameworks como `faiss-gpu` ou `qdrant-gpu` (quando disponível) dentro de enclaves TEE-friendly (H100, MI300 confidential).
   - O pipeline inclui pré-processamento de requisições, stream de atualizações assinado e validação de integridade. Dessa forma, agentes que precisam de respostas sub-10ms podem direcionar queries para esse cache antes de cair no armazenamento persistente.

3. **Compressão adaptativa de blobs (vídeo/imagem/3D)**
   - Dados brutos (vídeos, nuvens de pontos, CAD) são pesados e muitas vezes acessados parcialmente. Planejamos implementar um middleware de compressão adaptativa: ao ingerir arquivos, detectamos tipo/mime e aplicamos codecs apropriados (AV1, HEVC, Draco, Zstd) com metadados sobre chunking.
   - Na leitura, o gateway serve apenas os segmentos necessários (range requests) e pode gerar representações derivadas (thumbs, frames chave, previews 3D) armazenadas em caches de borda. Tudo versionado no MinIO com ponte para pipelines externos (ex.: renderização em H100).

Essa combinação permite que a FroDB responda consultas multimodais com a mesma fluidez de bancos especializados, mantendo governança unificada e compatibilidade com os requisitos de privacidade da Dooor.
- **Visão longo prazo**: transformar a FroDB na **camada final de agregação de dados para IA** da Dooor — consolidando texto, imagens, vídeos, áudio e streams multimodais — servindo pipelines de inferência/treinamento e alimentando o ecossistema de agentes com governança unificada.

## 5. Por que a FroDB é única em relação a Qdrant, Weaviate e LanceDB

| Tema | FroDB | Qdrant | Weaviate | LanceDB |
|------|----------|--------|----------|---------|
| **Modelo de dados** | Coleções híbridas com schema declarativo (relacional + vetorial + binário) | Segment-centric, payload JSON, mas sem camada relacional integrada | Schema GraphQL com modules; vetores + HNSW, documentos ficam externos | Colunas Parquet (PyArrow), pensado como vetor + storage local |
| **Transações cross-store** | Sim (coordenamos Postgres + Qdrant + MinIO com rollback) | Não (depende de client-side coordination) | Parcial (extensões com Postgres via `contextionary` ou third-party) | Não (persistência colunar/FS, transações simples) |
| **Governança/Permissions** | API keys com granularidade de database/coleção, auditável | API keys básicas; integrações via scripts | ACLs moduladas, mas dependem de módulos externos | ACL manual (ou rely on outer layer) |
| **Multi-arquitetura** | Imagens oficiais amd64+arm64; Compose & script automatizam setup | Sim (amd64/arm64) | Sim | Sim |
| **S3 nativo** | Sim (MinIO acoplado, buckets versionados) | Não integrado | Não integrado | Não |
| **Integração com TEEs** | Roadmap direto para enclaves, atestação e multisig | Não é foco | Não é foco | Não |
| **Objetivo final** | Backend único para infraestrutura de agentes da Dooor, com compliance | Vetor DB puro, foco em payloads e filtros | Plataforma vetorial + módulos (RAG, Q&A) | Vetor DB local, dev-first |

Em resumo, a FroDB não tenta substituir Qdrant ou Postgres isoladamente, e sim **combiná-los com governança e automatização** para o ecossistema da Dooor. A camada adicional (schemas híbridos, bootstrap controlado, UI, script de instalação) é o diferencial que reduz atrito para equipes internas/externas trabalharem em ambientes auditáveis.

## 6. Fluxo de Deploy e Operação

### Local / Dev
- `cp .env.example .env` + `docker compose up --build`
- Studio disponível em `http://localhost:3000`, API em `http://localhost:8000/docs`
- Hot reload habilitado (bind mounts no compose padrão)

### Deploy em VM da Dooor
1. `curl -fsSL https://raw.githubusercontent.com/Dooor-AI/cortex-db/main/scripts/install.sh | bash -s -- --admin-key ... --gemini-key ...`
2. Script instala `.env`, baixa `docker-compose.prod.yml`, faz pull das imagens (amd64) e sobe serviços
3. Service endpoints expostos nas portas 8000/3000/9000/9001 (TLS via proxy reverso recomendado)

### Produção gerenciada
- Publicar as imagens no registry interno (ou usar Docker Hub público atual)
- Deploy via Kubernetes (Helm chart em roadmap), com statefulsets para Postgres/Qdrant/MinIO e services para gateway/studio
- Integração com Vault/KMS para segredos e rotação de chaves Gemini/Admin
- Observabilidade: logs estruturados (JSON) + métricas (Prometheus exporters em desenvolvimento)

## 7. Próximos passos

- Concluir pipelines de build multi-arquitetura no GitHub Actions (workflow já adicionado)
- Remover dependências de `latest` no compose de produção, adotando tags versionadas (ex.: `postgres:16.4-alpine`)
- Otimizar tamanho das imagens (reduzir layers e dependências redundantes)
- Integrar com o sistema de billing/incentivos da Dooor para contabilizar consumo por agente/aplicação
- Publicar documentação oficial (este manual + guias de API + exemplos de schema) no portal interno

---

A FroDB representa a camada unificadora de dados para a missão da Dooor: entregar infra de agentes confiável, auditável e economicamente alinhada. Ao invés de replicar o que Qdrant, Weaviate ou LanceDB já fazem, nós os orquestramos sob uma API coesa, compatível com TEEs e com a governança que a Dooor exige.
