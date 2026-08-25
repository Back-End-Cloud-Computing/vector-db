# vector-db

Microsservico responsavel exclusivamente pelo gerenciamento do banco vetorial
(ChromaDB) e pelas operacoes de busca/recomendacao relacionadas a vetores, no
projeto GANJJ.

## Escopo

- Persistencia de embeddings no ChromaDB (collection `products`), com
  MongoDB (no `product-service`) continuando como fonte de verdade dos dados
  estruturados do produto — este servico so guarda o necessario para
  operacoes vetoriais: `product_id`, embedding, metadata e o texto usado como
  representacao semantica.
- Insercao/atualizacao em batch via upsert, busca KNN/semantica com filtro de
  metadata, e remocao por ids e/ou filtro.
- Servico de recomendacao (similaridade de conteudo e sinais comportamentais
  mockados de Carrinho/Pedido/Cliente).

Este servico **nunca gera embeddings**: recebe vetores prontos do
`embedding-reranking` e nunca acessa o banco de outro servico.

## Endpoints

- `GET /vector_db/collections`
- `POST /vector_db/insert` — batch upsert de `{product_id, embedding, metadata, document}`.
- `POST /vector_db/search` — busca KNN por embedding, com `n_results` e filtro `where` opcional.
- `POST /vector_db/delete` — remove por `ids` e/ou `where`.
- `GET /vector_db/recommendations/products/{product_id}/similar`
- `GET /vector_db/recommendations/users/{user_id}`
- `GET /health`

As respostas de recomendacao trazem apenas `product_id` + `score` + `reasons`
(sem dados completos do produto), ja que este servico nao tem acesso ao
MongoDB. Quem consumir precisa hidratar via `POST /products/batch` no
`product-service`.

## Rodando localmente

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest

cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8002
```

Requer um ChromaDB acessivel (`CHROMA_HOST`/`CHROMA_PORT`), tipicamente via
`docker-compose.yml` na raiz do projeto.
