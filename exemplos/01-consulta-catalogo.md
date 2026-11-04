# Consulta de catálogo com filtro de preço

- **Cenário:** cliente procura violões disponíveis até R$ 1.000.
- **Competências demonstradas:** consulta ao catálogo, filtro por preço, verificação de disponibilidade.
- **Conversa:** `4` no banco local.
- **Modelo:** `qwen3:4b` via Ollama.
- **Registro:** 03/11/2026.

> Transcrição real, obtida executando a API local. Nenhuma mensagem foi editada.

> **Atualização:** este registro é anterior ao roteamento estruturado. Na versão atual, a mesma pergunta é resolvida por consulta determinística ao catálogo e retorna os 12 violões ativos abaixo de R$ 1.000 (ver [decisão 8](../README.md#8-roteamento-entre-consultas-estruturadas-e-rag)).

---

**Cliente:** Quais opções de violões disponíveis custando até R$ 1000?

**Agente:** Existem duas opções de violões disponíveis com preço até R$ 1000:
- Product 87: Yamaha F310 Aço Natural (R$ 699.90)
- Product 91: Tagima Woodstock Dreadnought Natural (R$ 899.00)

---

## O que este exemplo demonstra

O agente consultou o catálogo, aplicou o teto de preço e considerou apenas produtos com estoque, sem inventar modelos ou valores. A resposta é fiel ao contexto recuperado.

## Ponto de atenção (na versão original)

O CSV possui **12 violões ativos abaixo de R$ 1.000**, mas apenas 2 apareceram no contexto. Como o RAG recuperava no máximo 3 chunks de produto por pergunta, listagens amplas ficavam truncadas. O agente não errava os dados que citava, mas a resposta era incompleta. A correção aplicada foi encaminhar filtros estruturados para uma consulta determinística ao catálogo (ver [decisão 8](../README.md#8-roteamento-entre-consultas-estruturadas-e-rag)).

Além disso, o identificador interno (`Product 87`) apareceu na resposta porque fazia parte do texto do chunk. Na versão atual, o bloco estruturado omite IDs internos e o prompt proíbe explicitamente que sejam repetidos.
