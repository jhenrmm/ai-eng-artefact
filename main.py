import pymupdf
from sentence_transformers import SentenceTransformer, util

doc = pymupdf.open("data/políticas_da_loja.pdf")

document_text = "\n".join(
    page.get_text()
    for page in doc
)

chunk_size = 500

chunks = [
    document_text[i:i + chunk_size]
    for i in range(0, len(document_text), chunk_size)
    if document_text[i:i + chunk_size].strip()
]

model = SentenceTransformer(
    "BAAI/bge-m3"
)

embeddings = model.encode(
    chunks,
    convert_to_tensor=True,
    normalize_embeddings=True
)

query = model.encode(
    "Quantos reais para frete grátis?",
    convert_to_tensor=True,
    normalize_embeddings=True
)

similarities = util.cos_sim(query, embeddings)[0]

top_results = similarities.topk(k=min(3, len(chunks)))

for score, idx in zip(top_results.values, top_results.indices):
    print(f"Similaridade: {score.item():.4f}")
    print(f"Conteúdo: {chunks[idx.item()]}")
    print("-" * 50)
