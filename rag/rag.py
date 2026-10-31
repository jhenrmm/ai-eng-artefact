from .ingestion import ingest
from .retriever import retrieve


def run(pdf_path, query, k=3):
    chunks, vector_store = ingest(pdf_path)
    top_results = retrieve(query, vector_store, k)

    for score, idx in zip(top_results.values, top_results.indices):
        print(f"Similaridade: {score.item():.4f}")
        print(f"Conteúdo: {chunks[idx.item()]}")
        print("-" * 50)
