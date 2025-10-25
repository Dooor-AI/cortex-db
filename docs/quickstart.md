# CortexDB Quickstart

1. Copy `.env.example` to `.env` and provide your Gemini API key.
2. Start the stack:

   ```bash
   docker-compose up --build
   ```

3. Create a collection from one of the sample schemas:

   ```bash
   curl -X POST http://localhost:8000/collections \
     -H "Content-Type: application/x-yaml" \
     --data-binary @schemas/faqs.yml
   ```

4. Insert a record:

   ```bash
   curl -X POST http://localhost:8000/collections/faqs/records \
     -H "Content-Type: application/json" \
     -d '{"question": "Como funciona?", "answer": "É simples...", "category": "geral"}'
   ```

5. Run a hybrid search:

   ```bash
   curl -X POST http://localhost:8000/collections/faqs/search \
     -H "Content-Type: application/json" \
     -d '{"query": "funcionamento do sistema"}'
   ```

6. Explore interactive documentation at `http://localhost:8000/docs`.

## CortexDB Studio (UI)

1. `cd frontend`
2. `cp .env.example .env.local`
3. `npm install`
4. `npm run dev`
5. Abra `http://localhost:3000` para navegar pelas collections e registros.

Ao usar `docker-compose up --build`, o serviço `studio` é disponibilizado automaticamente na porta 3000.
