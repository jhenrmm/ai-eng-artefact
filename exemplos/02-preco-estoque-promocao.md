# Preço, estoque e promoção de um produto

- **Cenário:** cliente pergunta o preço e a disponibilidade de um modelo específico e, em seguida, se ele está em promoção.
- **Competências demonstradas:** consulta de preço/estoque, consulta de promoções, uso do histórico da conversa.
- **Conversa:** `5` no banco local.
- **Modelo:** `qwen3:4b` via Ollama.
- **Registro:** 03/11/2026.

> Transcrição real, obtida executando a API local. Nenhuma mensagem foi editada.

---

**Cliente:** Quanto custa o Takamine GD20 e ele está disponível em estoque?

**Agente:** O Takamine GD20 custa R$ 2199.00 e está disponível em estoque com 5 unidades.

**Cliente:** Ele está em promoção?

**Agente:** Não, o Takamine GD20 não está em promoção. Os promoções listadas no contexto são para outros produtos (PRS SE Custom 24 e Martin D-28 Dreadnought Natural) e estão inativas.

---

## O que este exemplo demonstra

- O agente localizou o produto pelo nome e cruzou preço e estoque no mesmo registro.
- O segundo turno usou o histórico: "Ele" foi resolvido como o Takamine GD20 sem o cliente repetir o nome.
- A resposta sobre promoção considerou apenas o campo de atividade da promoção, sem prometer desconto.
- O agente não afirmou que consultaria o sistema nem prometeu reservar o produto.

## Ponto de atenção

Há um erro gramatical ("Os promoções") produzido pelo modelo. Também não há validação de vigência por data: a resposta usa somente o campo `is_active` do CSV.
