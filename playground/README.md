# Playground - Testes e Experimentos

Pasta para rodar testes rápidos e experimentar funcionalidades do CortexDB.

## Quick Start

```bash
# 1. Certifique-se que o gateway está rodando
docker compose up -d

# 2. Configurar API key (para testes com vectorização)
# Edite .env no root e adicione: GEMINI_API_KEY=sua-chave

# 3. Instalar SDK (escolha um)
pip install cortexdb                    # Do PyPI
pip install -e clients/python/          # Modo dev (recomendado)

# 4. Instalar dependências extras
pip install httpx                       # Para helpers

# 5. Rodar testes
./playground/run.sh                     # Menu interativo
python3 playground/test_basic.py        # Ou roda direto
```

## Scripts Disponíveis

### Testes Automatizados

| Script | Descrição | Duração |
|--------|-----------|---------|
| `test_basic.py` | CRUD básico de collections e records | ~5s |
| `test_files.py` | Upload e download de arquivos | ~10s |
| `test_docling.py` | **Docling** - processamento avançado de documentos | ~15s |
| `test_rag.py` | **RAG completo** - busca semântica vetorial | ~20s |
| `test_search.py` | Busca semântica com vectorização | ~15s |
| `test_filters.py` | Filtros avançados ($gte, $lt, etc) | ~15s |

### Exemplos Práticos

| Script | Descrição |
|--------|-----------|
| `backend_example.py` | Backend FastAPI completo usando SDK |
| `interactive.py` | Modo interativo no terminal Python |
| `run.sh` | Menu helper para rodar testes |

## Como Usar

### 1. Testes Rápidos

```bash
# Rodar teste específico
python3 playground/test_basic.py

# Rodar todos os testes
./playground/run.sh
# Escolha opção 6
```

### 2. Backend de Exemplo

```bash
# Instalar deps
pip install fastapi uvicorn

# Rodar
python3 playground/backend_example.py

# Testar endpoints
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop","description":"Gaming laptop","price":1999.99,"stock":10}'

curl http://localhost:8001/products/search?q=laptop

# Docs: http://localhost:8001/docs
```

### 3. Modo Interativo

```bash
# Abrir terminal Python interativo
python3 -i playground/interactive.py

# No terminal Python:
>>> await create_collection()
>>> await create_sample_data()
>>> await search("python programming")
>>> await cleanup()

# Ou use run() para sync:
>>> run(create_collection())
```

## Estrutura

```
playground/
├── README.md              # Este arquivo
├── run.sh                 # Helper menu
├── requirements.txt       # Dependências
├── .gitignore            # Ignora arquivos gerados
│
├── test_basic.py          # Teste CRUD
├── test_files.py          # Teste files
├── test_search.py         # Teste busca
├── test_filters.py        # Teste filtros
│
├── backend_example.py     # Backend FastAPI
├── interactive.py         # Modo interativo
│
└── sample_files/          # Gerado automaticamente
    └── (arquivos de teste)
```

## Casos de Uso

### Testar nova feature
```bash
# Edite test_basic.py
# Adicione seu teste
python3 playground/test_basic.py
```

### Debugar problema
```python
# Em qualquer script, adicione:
import pdb; pdb.set_trace()

# Ou rode em modo verbose:
python3 -i playground/test_basic.py
```

### Criar backend rapidamente
```bash
# Copie backend_example.py
cp playground/backend_example.py meu_backend.py

# Edite e rode
python3 meu_backend.py
```

## Dicas

- **Logs do gateway**: `docker compose logs gateway -f`
- **Resetar tudo**: `docker compose down -v && docker compose up -d`
- **Modo dev SDK**: `pip install -e clients/python/` (mudanças são aplicadas automaticamente)
- **Debug**: Use `import pdb; pdb.set_trace()` ou `python3 -i script.py`
- **Performance**: Rode com `time python3 playground/test_basic.py`

## Troubleshooting

### Gateway não está rodando
```bash
docker compose up -d
# Aguarde ~10s para inicializar
curl http://localhost:8000/health
```

### SDK não encontrada
```bash
# Instale do PyPI
pip install cortexdb

# Ou modo dev
pip install -e clients/python/
```

### Erro de embedding provider

Os testes de busca semântica (`test_search.py`, `test_filters.py`) requerem `GEMINI_API_KEY` configurada.

**Setup automático (recomendado):**

1. Adicione sua key no `.env` do root do projeto:
```bash
# No arquivo .env (root do projeto)
GEMINI_API_KEY=sua-chave-aqui
```

2. Os testes irão configurar o provider automaticamente usando o helper `ensure_gemini_provider()`.

**Setup manual via API:**

Se preferir configurar manualmente:
```bash
curl -X POST http://localhost:8000/settings/embeddings/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gemini-default",
    "provider": "gemini",
    "api_key": "sua-api-key-aqui",
    "embedding_model": "models/embedding-001",
    "enabled": true
  }'
```

**Testes sem embedding:**

Use apenas `test_basic.py` e `test_files.py` - funcionam sem provider configurado.
