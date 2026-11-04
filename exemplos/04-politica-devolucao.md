# Aplicação da política de devolução por arrependimento

- **Cenário:** cliente se arrepende de uma compra online e pergunta se pode devolver; em seguida, informa que recebeu o produto há 5 dias.
- **Competências demonstradas:** recuperação de política, aplicação de prazo, uso do histórico, ausência de falsa capacidade de ação.
- **Conversa:** `8` no banco local.
- **Modelo:** `qwen3:4b` via Ollama.
- **Registro:** 03/11/2026.

> Transcrição real, obtida executando a API local. Nenhuma mensagem foi editada.

---

**Cliente:** Me arrependi da minha compra, posso devolver meu pedido?

**Agente:** Sim, se a compra foi feita online, você pode solicitar a devolução em até 7 dias corridos após o recebimento do produto, sem necessidade de justificativa. O produto deve estar em sua embalagem original, sem sinais de uso, com todos os acessórios e manuais. O reembolso será realizado na mesma forma de pagamento original em até 10 dias úteis. O frete de devolução é por conta da loja.

**Cliente:** Comprei online e recebi o produto há 5 dias. Tenho direito?

**Agente:** Sim, você tem direito a devolver o produto, pois recebeu há 5 dias, que está dentro do prazo de 7 dias corridos após o recebimento. A devolução pode ser solicitada sem necessidade de justificativa.

---

## O que este exemplo demonstra

- O agente explicou a política de arrependimento (art. 49 do CDC, reproduzida no manual) sem pedir o número do pedido e sem dizer que verificaria o caso.
- No segundo turno, aplicou corretamente o prazo de 7 dias ao dado informado pelo cliente.
- Mencionou as condições do produto e o prazo de reembolso, ambos presentes no contexto.

## Ponto de atenção

O agente não executa a devolução nem registra a solicitação: ele informa a política. O encaminhamento para o time de suporte é a ação possível neste protótipo. Para casos que fogem das condições gerais, a política manda consultar a gerência.
