from .embedding import embed
from .vector_store import search


def retrieve(query, vector_store, k=3):
    query_embedding = embed(query)
    return search(vector_store, query_embedding, k)
