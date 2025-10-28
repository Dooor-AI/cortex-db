# CortexDB TypeScript SDK - Lista de Pendências

## ❌ Faltando (comparado com SDK Python)

### 1. Publicação no NPM
- [ ] Publicar no NPM Registry
- [ ] Configurar scoped package (@cortexdb/sdk ou @cortexdb/typescript)
- [ ] Adicionar versioning (começar em 0.1.0)
- [ ] Criar workflow de publish (manual ou CI/CD)

### 2. Testes Unitários
- [ ] Configurar Jest ou Vitest
- [ ] Testes para HTTPClient
- [ ] Testes para CollectionsAPI
- [ ] Testes para RecordsAPI
- [ ] Testes de integração (end-to-end)
- [ ] Coverage report

### 3. Exceptions/Error Handling
- [ ] Criar classes de erro dedicadas:
  - `CortexDBError` (base)
  - `CortexDBConnectionError`
  - `CortexDBTimeoutError`
  - `CortexDBNotFoundError`
  - `CortexDBValidationError`
  - `CortexDBAuthenticationError`
  - `CortexDBPermissionError`
  - `CortexDBServerError`
- [ ] Mapear códigos HTTP para erros específicos

### 4. Arquivos de Configuração
- [ ] Criar `.gitignore`
- [ ] Criar `.npmignore` (excluir src, examples, tests)
- [ ] Adicionar `LICENSE` file (MIT)
- [ ] Melhorar `README.md` com mais exemplos

### 5. Suporte a File Upload
- [ ] Implementar upload de arquivos com FormData
- [ ] Suporte a Buffer e File
- [ ] Exemplo de file upload
- [ ] Documentação de file upload

### 6. Exemplos Adicionais
- [ ] Exemplo de quickstart mais completo
- [ ] Exemplo de file upload
- [ ] Exemplo com embedding provider
- [ ] Exemplo de semantic search
- [ ] Exemplo de filters complexos

### 7. Modelos/Types Faltando
- [ ] `StoreLocation` enum
- [ ] `ExtractConfig` interface
- [ ] `VectorChunk` interface
- [ ] `EmbeddingProvider` interface completa
- [ ] `QueryRequest` interface

### 8. Features Faltando
- [ ] `client.healthcheck()` método
- [ ] Retry logic no HTTP client
- [ ] Timeout configurável por request
- [ ] Suporte a databases (DatabasesAPI?)
- [ ] Suporte a pagination completo
- [ ] Suporte a streaming (se aplicável)

### 9. Documentação
- [ ] JSDoc completo em todas as funções
- [ ] API Reference gerado (TypeDoc)
- [ ] Guia de contribuição
- [ ] Changelog
- [ ] Exemplos no README
- [ ] Link para documentação oficial

### 10. CI/CD
- [ ] GitHub Actions para testes
- [ ] GitHub Actions para build
- [ ] GitHub Actions para publish no NPM
- [ ] Linting (ESLint)
- [ ] Formatting (Prettier)

### 11. Package.json Improvements
- [ ] Adicionar `repository` field
- [ ] Adicionar `bugs` field
- [ ] Adicionar `homepage` field
- [ ] Adicionar mais `keywords`
- [ ] Adicionar `engines` requirement (Node >= 18)

## ✅ Completo

- [x] Estrutura básica de diretórios
- [x] TypeScript configuration
- [x] Build funcionando
- [x] HTTP Client básico
- [x] Collections API
- [x] Records API (create, get, list, update, delete, search)
- [x] Types básicos
- [x] README básico
- [x] Exemplo básico funcionando
- [x] Exports configurados

