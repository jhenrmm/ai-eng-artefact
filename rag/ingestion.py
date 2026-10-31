import pymupdf

from .embedding import embed

CHUNK_SIZE = 500


def ingest(pdf_path):
    doc = pymupdf.open(pdf_path)

    document_text = "\n".join(
        page.get_text()
        for page in doc
    )

    chunks = [
        document_text[i:i + CHUNK_SIZE]
        for i in range(0, len(document_text), CHUNK_SIZE)
        if document_text[i:i + CHUNK_SIZE].strip()
    ]

    embeddings = embed(chunks)
    return chunks, embeddings
