# Pergunta fora do escopo da loja

- **Cenário:** cliente pergunta sobre previsão do tempo, assunto sem relação com a loja.
- **Competências demonstradas:** reconhecimento de escopo, recusa educada, manutenção da persona.
- **Conversa:** `9` no banco local.
- **Modelo:** `qwen3:4b` via Ollama.
- **Registro:** 03/11/2026.

> Transcrição real, obtida executando a API local. Nenhuma mensagem foi editada.

---

**Cliente:** Qual é a previsão do tempo em Campo Grande amanhã?

**Agente:** Lamento, mas não tenho acesso à informação do tempo e não posso ajudar com previsões meteorológicas. Meu foco é apenas oferecer suporte relacionado às políticas e procedimentos do Empório da Música. 😊

---

## O que este exemplo demonstra

O agente não tentou responder ao assunto externo, não inventou dados meteorológicos e redirecionou a conversa para o escopo da loja, mantendo o tom cordial.

## Ponto de atenção

A formulação "políticas e procedimentos" é mais restrita do que o escopo real do agente, que também consulta catálogo, preços, estoque e pedidos. Um ajuste de prompt deixaria a mensagem mais precisa: "assuntos relacionados à Empório da Música".
