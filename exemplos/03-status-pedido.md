# Consulta de status e rastreamento de pedido

- **Cenário:** cliente informa o número do pedido e pergunta o status e o código de rastreamento.
- **Competências demonstradas:** consulta de dados operacionais, relato de status sem prometer ações.
- **Conversa:** `7` no banco local.
- **Modelo:** `qwen3:4b` via Ollama.
- **Registro:** 03/11/2026.

> Transcrição real, obtida executando a API local. Nenhuma mensagem foi editada.

---

**Cliente:** Qual o status e o código de rastreamento do pedido 1?

**Agente:** O status do pedido 1 é entregue e o código de rastreamento é BRAB1234567BR.

---

## O que este exemplo demonstra

- O identificador de pedido na pergunta ativou a consulta estruturada ao pedido correspondente (`service/router.py` + `service/store.py`); na versão original, o mesmo efeito era obtido incluindo chunks de pedidos no contexto do RAG.
- O agente respondeu apenas com dados do pedido correspondente, sem inventar prazo, transportadora ou confirmação de entrega.
- Não houve promessa de alteração, cancelamento ou reenvio — o agente apenas informa.

## Ponto de atenção

Não existe autenticação: qualquer pessoa que saiba um número de pedido pode consultar os dados daquele pedido. Em produção, seria necessário vincular a conversa ao cliente e autorizar a consulta.
