# Empório da Música — Agente de Atendimento

Protótipo de agente de atendimento ao cliente para a **Empório da Música**, loja fictícia de instrumentos musicais de Campo Grande/MS. O agente conversa em português brasileiro, responde dúvidas sobre produtos, preços, estoque, pedidos e políticas da loja, e recusa educadamente assuntos fora do escopo.

> Repositório: <https://github.com/jhenrmm/ai-eng-artefact>

---

## Sumário

- [Visão geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Stack utilizada](#stack-utilizada)
- [Decisões técnicas e justificativas](#decisões-técnicas-e-justificativas)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como rodar o projeto](#como-rodar-o-projeto)
- [Usando a API](#usando-a-api)
- [Exemplos de interação](#exemplos-de-interação)
- [Limitações conhecidas](#limitações-conhecidas)
- [O que eu faria com mais tempo](#o-que-eu-faria-com-mais-tempo)
- [Uso de assistentes de código](#uso-de-assistentes-de-código)
- [Suposições assumidas](#suposições-assumidas)

---

## Visão geral

O cenário do desafio é uma equipe de atendimento sobrecarregada com perguntas recorrentes: horário de funcionamento, status de pedido, preço e disponibilidade de produtos, regras de troca e devolução, formas de pagamento etc.

A solução é um agente que:

- assume a persona da loja (tom informal, mas profissional, conforme o manual de políticas);
- responde com base em duas fontes: o **manual de políticas** (PDF) e as **tabelas operacionais** (CSVs de produtos, pedidos, clientes, categorias e promoções);
- usa **RAG com índice único e unificado**: os chunks do PDF e os registros dos CSVs (serializados em texto com prefixo de origem, ex.: `[products]`, `[orders]`, `[promotions]`) são embaralhados no mesmo índice vetorial, de modo que uma mesma busca semântica pode recuperar tanto regras de política quanto dados factuais;
- evita inventar informação: o system prompt exige que a resposta use apenas fatos explícitos no contexto recuperado;
- lida com perguntas fora do escopo informando que só pode ajudar com assuntos relacionados à loja;
- mantém histórico de conversa persistido em PostgreSQL, permitindo retomar o atendimento pelo `conversation_id`.

O agente **não executa ações** (cancelar pedido, emitir reembolso, alterar cadastro). Ele apenas informa e encaminha para a equipe humana quando necessário — decisão deliberada para reduzir risco no protótipo.

---

## Arquitetura

```mermaid
flowchart TD
    U[Cliente] -->|POST /chat| API[FastAPI]
    API -->|carrega histórico| DB[(PostgreSQL<br/>conversations + messages)]
    API -->|embedding da pergunta| EMB[SentenceTransformers<br/>BAAI/bge-m3]
    EMB -->|similaridade de cosseno| IDX[Índice em memória<br/>chunks do PDF + registros dos CSVs]
    IDX -->|top-k chunks| LLM[Ollama<br/>qwen3:4b]
    LLM -->|resposta| API
    API -->|salva troca| DB
    API -->|JSON| U
```

O índice é construído **uma única vez por processo**, de forma lazy, na primeira chamada a `/chat` (*double-checked locking* em `api/app.py`).

Fluxo de uma requisição:

1. `POST /chat` recebe `message` e, opcionalmente, `conversation_id`.
2. Se houver `conversation_id`, o histórico é carregado do PostgreSQL (404 se não existir).
3. Na primeira chamada, o índice é construído: extração de texto do PDF com PyMuPDF, leitura dos CSVs, serialização dos registros em chunks com origem, geração de embeddings com `BAAI/bge-m3` e criação do índice em memória.
4. A pergunta do cliente é embutida e submetida a busca por similaridade de cosseno sobre o índice (top-k, padrão `k=3`).
5. O contexto selecionado é montado com os `top-k` chunks recuperados, injetado no system prompt junto com o histórico da conversa, e enviado ao Ollama.
6. A resposta é gerada pelo Ollama, devolvida ao cliente e a troca (mensagem do usuário + resposta) é persistida no PostgreSQL.
7. Em uma conversa nova, o `conversation_id` é criado no momento da persistência e devolvido na resposta.

---

## Stack utilizada

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11 |
| API | FastAPI + Uvicorn |
| LLM | `qwen3:4b` via [Ollama](https://ollama.com/) local (cliente HTTP puro com `urllib`, sem SDK) |
| Embeddings | `BAAI/bge-m3` via `sentence-transformers` (vetores normalizados) |
| Vetor store | Índice em memória + similaridade de cosseno (`sentence_transformers.util.cos_sim`), top-k fixo |
| Parsing do PDF | PyMuPDF (`pymupdf`) |
| Dados tabulares | `csv` da biblioteca padrão |
| Banco de dados | PostgreSQL + `psycopg` |
| Migrations | Alembic |
| Validação | Pydantic (via FastAPI) |
| Containerização | Docker + Docker Compose |

Não há LangChain, LlamaIndex nem SDK de provedor de LLM: o pipeline RAG é implementado diretamente, com poucas dependências e fluxo explícito.

---

## Decisões técnicas e justificativas

### 1. Abordagem: RAG com índice único e unificado

Optei por **RAG com busca semântica sobre um único índice**, combinando:

- os chunks de texto do manual de políticas (extraído com PyMuPDF, chunks fixos de 500 caracteres);
- os registros dos CSVs convertidos em descrições em linguagem natural, prefixados pela origem (`[products]`, `[orders]`, `[order_items]`, `[promotions]`, `[categories]`).

Chamei de "único e unificado" porque o índice contém dados **não estruturados** (políticas) e **estruturados serializados** (catálogo, pedidos, promoções), permitindo que a mesma pergunta recupere tanto regras quanto dados factuais com uma única chamada de busca.

Por que não um agente de SQL, function calling ou ReAct?

- O volume é pequeno (dezenas de produtos, pedidos, clientes e promoções). Não há ganho relevante de performance em consultas SQL dinâmicas.
- Um agente de SQL adiciona modos de falha (SQL inválido, alucinação de colunas, necessidade de retry e validação) sem melhorar a experiência neste escopo.
- A serialização dos registros em texto preserva o vocabulário do domínio ("violão clássico", "tampo sólido", "nylon"), o que funciona bem com embeddings multilíngues.

O trade-off é conhecido: como a recuperação é puramente semântica com top-k fixo (`k=3`), listagens exaustivas (ex.: "todos os violões até R$ 1.000") podem ficar incompletas se os produtos relevantes não estiverem entre os `k` mais similares. A evolução natural é adicionar roteamento com filtros determinísticos para consultas de catálogo e pedido.

### 2. Modelo e provedor

- **LLM: `qwen3:4b` via Ollama local.** Escolhi um modelo local por custo zero, privacidade dos dados fictícios de clientes e facilidade de reprodução (basta ter Ollama). O modelo tem bom desempenho em português e segue instruções de restrição de contexto. O tamanho (4B) mantém a latência aceitável em máquina de desenvolvimento e o timeout configurável em 120s cobre as respostas mais longas.
- **Embeddings: `BAAI/bge-m3`.** Modelo multilíngue com boa qualidade em português, vetores normalizados (norma 1), o que torna a similaridade de cosseno adequada.

A chamada ao Ollama é feita via HTTP puro (`urllib`), sem SDK, o que mantém a superfície de dependências pequena. Erros de conexão, timeout, HTTP e JSON inválido são convertidos em `OllamaError` e devolvidos como `503` pela API.

### 3. Interface de interação

**API HTTP com FastAPI**, documentada automaticamente em `/docs`. A escolha permite testar via `curl`, integrar com um front-end ou com o WhatsApp no futuro, e mantém o foco no agente. Não foi construída UI própria: o esforço foi direcionado ao pipeline e à persistência. O endpoint `GET /conversations/{id}` permite inspecionar o histórico e serve como ferramenta de depuração.

### 4. Persistência do histórico

**PostgreSQL + Alembic**, com duas tabelas:

- `conversations (id, created_at, updated_at)`;
- `messages (id, conversation_id, role, content, created_at)`, com FK `ON DELETE CASCADE` e `CHECK (role IN ('user','assistant'))`.

O histórico completo é enviado ao LLM a cada turno, o que dá continuidade ao atendimento (ex.: o cliente diz "e o preço dele?" depois de perguntar por um produto). A escolha por PostgreSQL se deve à robustez, ao versionamento de schema via migrations e à possibilidade de migrar o índice vetorial para `pgvector` sem trocar de banco.

A persistência só ocorre após uma resposta bem-sucedida do LLM: se o Ollama falhar, a troca não é salva, evitando histórico com mensagens sem resposta. O `conversation_id` de conversas inexistentes retorna `404`.

### 5. Estratégia de prompt

O system prompt (`service/rag.py`) é deliberadamente restritivo:

- **Fonte única de verdade:** responder apenas com fatos explícitos no contexto; proibido inferir, deduzir, assumir, combinar, completar ou especular sobre qualquer informação.
- **Antialucinação em pedidos:** nunca afirmar que um pedido foi cancelado, entregue, reembolsado, trocado, reservado ou cobrado sem que o contexto diga isso.
- **Sem falsa capacidade de ação:** o agente não tem acesso a sistemas, então não pode dizer "vou verificar", "vou consultar o sistema" ou prometer executar algo. Isso evita a pior experiência possível: o cliente acreditar que uma ação foi tomada.
- **Trocas e devoluções:** para perguntas de devolução, o agente explica apenas a política e oferece encaminhamento ao time de suporte. Ele não pede ID de pedido nesse fluxo, para não criar expectativa de análise individual.
- **Pedidos:** quando a pergunta contém um ID, o agente pode relatar status/rastreamento do pedido correspondente, mas sem prometer alterações.
- **Fora de escopo:** informa educadamente que só pode ajudar com assuntos relacionados à Empório da Música.
- **Idioma e persona:** sempre em português brasileiro, tom cordial e conciso, alinhado ao manual ("informal mas profissional").

O contexto RAG é montado com até 3 chunks (`k=3`). O prompt inclui o histórico da conversa antes da pergunta atual.

### 6. Tratamento dos dados

- CSVs lidos com `utf-8-sig` (os arquivos têm BOM).
- O nome da tabela é derivado do nome do arquivo após `" - "` (`desafio_tecnico_ai_eng - products.csv` → `products`).
- Chaves estrangeiras são resolvidas na ingestão: produto → nome da categoria; pedido → nome do cliente; item de pedido → nome do produto e status do pedido; promoção → nome do produto.
- Preços são formatados com duas casas decimais no padrão brasileiro (`R$ 2199.00`); `specs` é um JSON por produto, convertido em pares `chave=valor`.
- O PDF é extraído com PyMuPDF e dividido em chunks fixos de 500 caracteres (`CHUNK_SIZE`), descartando trechos vazios.
- A atividade da promoção é derivada do campo `is_active` (`1`/`0`).
- Dados de clientes não são indexados como chunks próprios; aparecem apenas como nome associado ao pedido (telefone/e-mail não são usados).

A ingestão e o carregamento das tabelas operacionais são executados na primeira requisição a `/chat`, não em background. O agente reflete o snapshot dos CSVs/PDF no momento em que o índice é construído; alterações nos arquivos exigem reinício do processo.

### 7. Containerização

O `docker-compose.yml` sobe a API, o PostgreSQL e o Ollama em uma rede interna, com três volumes nomeados (`pgdata`, `ollama`, `hf_cache`) para persistir banco e modelos entre reinícios. As decisões principais:

- **Migrations no entrypoint, com retry.** `docker/entrypoint.sh` executa `alembic upgrade head` antes do Uvicorn, com retentativas enquanto o banco estiver indisponível.
- **`ollama-pull` como serviço one-shot.** A API só sobe depois que o modelo de chat foi baixado (`condition: service_completed_successfully`). Isso evita a primeira requisição falhar por modelo ausente.
- **PyTorch CPU.** O `Dockerfile` instala `torch` do índice CPU antes das demais dependências. Sem isso, o PyPI baixaria as wheels CUDA e a imagem cresceria vários GB sem ganho em um host sem GPU.
- **Cache de modelos em volume.** `HF_HOME` e `SENTENCE_TRANSFORMERS_HOME` apontam para `/cache`, montado no volume `hf_cache`; o `bge-m3` não é baixado de novo a cada `docker compose up`.
- **Superfície mínima exposta.** Apenas a API publica porta no host (`8001`). PostgreSQL e Ollama ficam acessíveis somente na rede do Compose.
- **Healthchecks.** PostgreSQL (`pg_isready`), Ollama (`ollama list`) e API (`/health`) têm verificações próprias; o `start_period` da API é longo para acomodar o carregamento do modelo de embeddings.

O usuário do container é não-root (`appuser`, UID 10001), e as dependências são instaladas em uma camada separada do código para aproveitar o cache de build.

---

## Estrutura do repositório

```text
.
├── api/
│   └── app.py               # endpoints /health, /chat e /conversations/{id};
│                              índice lazy com double-checked locking
├── service/
│   ├── __init__.py
│   ├── database.py          # conexão PostgreSQL, histórico e persistência de trocas
│   ├── embedding.py         # SentenceTransformer BAAI/bge-m3 e geração de embeddings
│   ├── ingestion.py         # PDF (PyMuPDF) + CSVs -> chunks com origem
│   ├── ollama.py            # cliente HTTP puro do Ollama (urllib)
│   ├── rag.py               # system prompt, montagem de contexto (top-k) e chamada ao LLM
│   ├── retriever.py         # embedding da query + busca por similaridade (top-k)
│   └── vector_store.py      # índice em memória + cos_sim top-k
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 0001_create_chat_tables.py
├── docker/
│   └── entrypoint.sh        # aplica migrations com retry e inicia a API
├── Dockerfile               # Python 3.11-slim, PyTorch CPU, usuário não-root (appuser)
├── docker-compose.yml       # postgres + ollama + ollama-pull + api (rede interna)
├── data/
│   ├── desafio_tecnico_ai_eng - categories.csv
│   ├── desafio_tecnico_ai_eng - customers.csv
│   ├── desafio_tecnico_ai_eng - orders.csv
│   ├── desafio_tecnico_ai_eng - order_items.csv
│   ├── desafio_tecnico_ai_eng - products.csv
│   ├── desafio_tecnico_ai_eng - promotions.csv
│   └── políticas_da_loja.pdf
├── exemplos/                # 5 transcrições reais de interação + README
├── desafio_tecnico_ai_eng_artefact.pdf
├── .env.example
├── .gitignore
├── .dockerignore
├── alembic.ini
├── config.py                # leitura de variáveis de ambiente
├── main.py                  # entrypoint (Uvicorn)
├── README.md
└── requirements.txt
```

---

## Como rodar o projeto

Há dois caminhos: **Docker Compose** (recomendado, sobe API + PostgreSQL + Ollama juntos) e **execução local** (para desenvolvimento).

### Opção 1 — Docker Compose (recomendado)

Pré-requisitos:

- **Docker Engine** ou **Docker Desktop** com Compose v2
- ~10 GB de disco livre (imagens, modelos e banco)
- ~8 GB de RAM disponíveis para os containers

Na raiz do repositório:

```bash
docker compose up --build
```

O Compose sobe quatro serviços:

| Serviço | Papel |
|---|---|
| `postgres` | banco `artefact`, com volume persistente |
| `ollama` | servidor do modelo de chat, com volume persistente |
| `ollama-pull` | serviço one-shot que baixa o `qwen3:4b` antes da API subir |
| `api` | build da imagem, migrations automáticas e Uvicorn em `0.0.0.0:8000` |

A API fica disponível em <http://localhost:8001> e a documentação em <http://localhost:8001/docs>. O PostgreSQL e o Ollama **não são expostos** para o host por padrão; a comunicação acontece na rede interna do Compose.

Na primeira execução, o processo pode levar vários minutos:

1. build da imagem (instala PyTorch CPU, FastAPI, PyMuPDF etc.);
2. download da imagem do Ollama e do modelo `qwen3:4b` (~2,5 GB) pelo `ollama-pull`;
3. download do modelo de embeddings `BAAI/bge-m3` (~2,3 GB) na primeira subida da API / primeira chamada a `/chat`.

Acompanhe com:

```bash
docker compose logs -f api
```

Comandos úteis:

```bash
docker compose up --build -d      # sobe em background
docker compose ps                 # status dos serviços
docker compose logs -f api        # logs da API
docker compose down               # para os containers (mantém volumes)
docker compose down -v            # para e apaga banco e modelos baixados
docker compose up --build -d      # reaplica mudanças de código
```

> O Compose lê o `.env` da raiz apenas para interpolar variáveis como `API_PORT`, `OLLAMA_MODEL`, `ST_MODEL_NAME` e `POSTGRES_*`. O `DATABASE_URL` usado dentro dos containers é montado automaticamente apontando para o serviço `postgres`, então não é necessário ter PostgreSQL ou Ollama instalados no host. Se alterar `POSTGRES_PASSWORD` depois do primeiro start, o volume antigo mantém a senha anterior; use `docker compose down -v` para recriar.

> **Solução de problemas:** se a porta `8001` estiver ocupada, ajuste `API_PORT` no `.env` e rode `docker compose up -d` novamente. Se o download do modelo falhar, execute `docker compose up ollama-pull` para repetir apenas essa etapa. Para inspecionar o banco sem expor a porta, use `docker compose exec postgres psql -U postgres -d artefact`.

### Opção 2 — Execução local (sem Docker)

#### Pré-requisitos

- **Python 3.11+**
- **PostgreSQL** em execução
- **Ollama** instalado e em execução ([download](https://ollama.com/download))
- ~5 GB de disco livre para o modelo de chat (~2,5 GB) e o de embeddings (~2,3 GB; baixado no primeiro uso)

#### 1. Clonar e criar o ambiente

```bash
git clone https://github.com/jhenrmm/ai-eng-artefact.git
cd ai-eng-artefact
```

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Baixar e subir o modelo

```bash
ollama serve          # se ainda não estiver rodando como serviço
ollama pull qwen3:4b
```

#### 3. Criar o banco

```bash
createdb -U postgres artefact
```

Ou, via `psql`:

```sql
CREATE DATABASE artefact;
```

#### 4. Configurar as variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

**Windows:**

```powershell
Copy-Item .env.example .env
```

| Variável | Obrigatória | Padrão no código | Descrição |
|---|---|---|---|
| `OLLAMA_URL` | sim | — | URL base do Ollama (ex.: `http://localhost:11434`) |
| `OLLAMA_MODEL` | sim | — | Modelo de chat (ex.: `qwen3:4b`) |
| `OLLAMA_TIMEOUT` | não | `120` | Timeout da chamada ao LLM, em segundos |
| `DATABASE_URL` | sim | — | Conexão PostgreSQL (ex.: `postgresql://postgres:postgres@localhost:5432/artefact`) |
| `DATABASE_CONNECT_TIMEOUT` | não | `5` | Timeout de conexão com o banco, em segundos |
| `API_HOST` | sim | — | Host do Uvicorn (ex.: `127.0.0.1`) |
| `API_PORT` | sim | — | Porta do Uvicorn (ex.: `8001`) |
| `ST_MODEL_NAME` | sim | — | Modelo de embeddings (ex.: `BAAI/bge-m3`) |
| `PDF_PATH` | não | `data/políticas_da_loja.pdf` | Caminho do manual de políticas |
| `DATA_DIR` | não | `data` | Diretório dos CSVs |
| `CHUNK_SIZE` | não | `500` | Tamanho dos chunks do PDF, em caracteres |
| `CHAT_MAX_MESSAGE_CHARS` | não | `1000` | Tamanho máximo de uma mensagem do usuário |

Exemplo de `.env`:

```dotenv
PDF_PATH=data/políticas_da_loja.pdf
CHUNK_SIZE=500

OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
OLLAMA_TIMEOUT=120

CHAT_MAX_MESSAGE_CHARS=1000

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/artefact
DATABASE_CONNECT_TIMEOUT=5

API_HOST=127.0.0.1
API_PORT=8001

ST_MODEL_NAME=BAAI/bge-m3
```

#### 5. Aplicar as migrations

```bash
alembic upgrade head
```

#### 6. Subir a API

```bash
python main.py
```

A API ficará em `http://127.0.0.1:8001`, com documentação interativa em <http://127.0.0.1:8001/docs>.

> **Primeira execução:** o `BAAI/bge-m3` é baixado (~2,3 GB) e o índice é construído na primeira chamada a `/chat` (extração do PDF + leitura dos CSVs + geração de embeddings). Isso pode levar alguns minutos. As chamadas seguintes reutilizam o índice em memória.

---

## Usando a API

### Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Verificação simples de saúde (`{"status": "ok"}`) |
| `POST` | `/chat` | Envia uma mensagem; cria ou continua uma conversa |
| `GET` | `/conversations/{id}` | Retorna o histórico da conversa |

### Iniciar uma conversa

```bash
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quanto custa o Takamine GD20?"}'
```

Resposta:

```json
{
  "conversation_id": 1,
  "message": "O Takamine GD20 custa R$ ..."
}
```

### Continuar a conversa

```bash
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "E ele está disponível em estoque?", "conversation_id": 1}'
```

### Consultar o histórico

```bash
curl http://127.0.0.1:8001/conversations/1
```

```json
{
  "conversation_id": 1,
  "messages": [
    {"role": "user", "content": "Quanto custa o Takamine GD20?"},
    {"role": "assistant", "content": "..."}
  ]
}
```

### Códigos de erro

| Status | Situação |
|---|---|
| `422` | Payload inválido (mensagem vazia ou acima de `CHAT_MAX_MESSAGE_CHARS`) |
| `404` | `conversation_id` inexistente |
| `503` | Ollama indisponível/timeout ou banco inacessível |

---

## Exemplos de interação

As conversas de exemplo estão em [`exemplos/`](exemplos/). São transcrições reais, geradas executando a API local com o `qwen3:4b`, sem edição das mensagens:

| # | Cenário | O que demonstra |
|---|---|---|
| [01](exemplos/01-consulta-catalogo.md) | "Quais opções de violões disponíveis custando até R$ 1000?" | consulta ao catálogo e filtro de preço via recuperação semântica |
| [02](exemplos/02-preco-estoque-promocao.md) | "Quanto custa o Takamine GD20 e ele está disponível em estoque?" | preço, estoque, promoção e uso do histórico |
| [03](exemplos/03-status-pedido.md) | "Qual o status e o código de rastreamento do pedido 1?" | consulta de pedido e relato sem promessa de ação |
| [04](exemplos/04-politica-devolucao.md) | "Me arrependi da minha compra, posso devolver meu pedido?" | aplicação da política de arrependimento |
| [05](exemplos/05-fora-de-escopo.md) | "Qual é a previsão do tempo em Campo Grande amanhã?" | recusa educada de assunto fora do escopo |

Cada arquivo inclui a transcrição e uma análise curta do comportamento, com pontos de atenção quando aplicável.

> Nota: como a recuperação é puramente semântica com top-k fixo (3 chunks), respostas que exigem listagem exaustiva de catálogo podem ficar incompletas (ver [Limitações conhecidas](#limitações-conhecidas)).

---

## Limitações conhecidas

- **Recuperação puramente semântica, sem roteamento estruturado.** Não há filtros determinísticos nem consulta direta a tabelas: tudo depende da busca semântica com top-k fixo (`k=3`). Listagens exaustivas de catálogo (ex.: "todos os violões até R$ 1.000") podem ficar incompletas se os produtos relevantes não estiverem entre os `k` mais similares.
- **Top-k fixo em 3 chunks para políticas.** Perguntas textuais sobre políticas ainda são limitadas a 3 chunks e podem perder trechos relevantes do manual.
- **Chunking fixo de 500 caracteres, sem overlap.** Pode cortar tabelas, listas e seções do manual no meio, prejudicando a recuperação de políticas específicas.
- **Índice vetorial e embeddings em memória, por processo.** Ambos são reconstruídos a cada reinício, não são compartilhados entre workers e não há persistência de embeddings. Com `--workers > 1`, cada worker mantém sua própria cópia.
- **Snapshot dos dados.** Alterações nos CSVs/PDF só valem após reiniciar o processo.
- **Histórico sem limite.** Todo o histórico é enviado ao LLM; conversas longas podem estourar a janela de contexto ou aumentar a latência.
- **Sem streaming.** A resposta só é devolvida após a geração completa; o timeout é de 120s.
- **Qualidade dependente de um modelo 4B.** Não há avaliação automatizada, reranking nem verificação de groundedness. O prompt reduz alucinação, mas não a elimina.
- **Promoções sem validação temporal.** O agente considera apenas o campo `is_active` do CSV; não há verificação de vigência por data.
- **Status de pedido é estático.** Os dados vêm do CSV, não de um sistema logístico em tempo real.
- **Sem ações transacionais.** O agente não cancela pedidos, não emite reembolsos e não altera cadastros — apenas informa e encaminha.
- **Sem autenticação e sem vínculo cliente↔conversa.** Qualquer pessoa que informe um ID de pedido pode receber dados daquele pedido. Em produção seria necessário vincular a conversa ao cliente e autorizar a consulta.
- **Mensagens limitadas a 1000 caracteres.**
- **Dependência de serviços locais.** Ollama e PostgreSQL precisam estar acessíveis; não há fallback para outro provedor.
- **O modelo de embeddings (~2,3 GB) é carregado na primeira requisição**, quando a ingestão do índice é disparada.

---

## O que eu faria com mais tempo

Os próximos passos seriam:

1. **Roteamento entre consultas estruturadas e RAG.** Adicionar classificação de intenção e filtros determinísticos (categoria, preço, estoque, pedido) para consultas de catálogo e pedido, mantendo o RAG para políticas — item de maior impacto e ainda não implementado.
2. **Autenticação e escopo por cliente.** Vincular a conversa a um cliente e permitir consulta apenas aos próprios pedidos, com auditoria.
3. **Índice vetorial persistente com `pgvector`.** Eliminar a reconstrução a cada start e permitir atualização incremental.
4. **Chunking semântico com overlap e citação de fontes.** Dividir por seções do manual, preservar tabelas e retornar a origem da informação ao cliente.
5. **Function calling no roteador.** Substituir regras por tool calling do LLM, mantendo a camada de consulta estruturada e ampliando a cobertura de paráfrases.
6. **Reranking e query rewriting.** Melhorar a precisão do top-k, especialmente para perguntas ambíguas e filtros numéricos.
7. **Avaliação e testes.** Golden set de perguntas/respostas, testes de fumaça da API, testes de retrieval e avaliação de groundedness (LLM-as-judge), integrados a CI.
8. **Guardrails.** Classificador de escopo, detecção de prompt injection, redação de PII e limite de histórico por sumarização.
9. **Streaming e handoff humano.** Respostas via SSE, integração com WhatsApp e transferência para atendente com resumo da conversa.
10. **Observabilidade.** Logs estruturados, métricas de latência/tokens, tracing do pipeline e alertas de erro.
11. **CI/CD e deploy.** GitHub Actions para lint, testes, build da imagem e publicação em um registry.

---

## Uso de assistentes de código

Usei o **OpenCode** como assistente de código ao longo do desenvolvimento. Meu workflow foi dividir o projeto em etapas e usar o agente para implementar uma parte por vez. Antes de avançar para a etapa seguinte, eu revisava o código gerado e testava a funcionalidade daquela parte, confirmando que estava funcionando antes de prosseguir. Isso manteve as mudanças pequenas e verificáveis, e me permitiu corrigir rumo cedo quando alguma decisão não funcionava como esperado.

As decisões de arquitetura, as escolhas de tecnologia e a validação final do comportamento do agente foram minhas. A redação deste README também contou com o auxílio do OpenCode a partir do PDF do desafio.

---

## Suposições assumidas

- O repositório público é <https://github.com/jhenrmm/ai-eng-artefact> e o projeto é executado a partir da raiz do repositório.
- O `.env` não é versionado; apenas `.env.example` é entregue.
- A loja fictícia e seus dados podem ser usados livremente para o protótipo.
- "Consultar dados em tempo real" foi interpretado como consultar o snapshot operacional disponibilizado nos CSVs, já que não há integração com sistemas externos da loja.
- **Acesso a dados de pedidos:** o agente apenas consulta o snapshot de pedidos dos CSVs (status, rastreamento, itens). Ele só devolve dados de um pedido quando o cliente fornece um ID correspondente a um registro existente; não consulta sistemas externos, não confirma a identidade do cliente e não promete qualquer ação sobre o pedido.
- O agente responde em português brasileiro, idioma do enunciado e do público da loja.
