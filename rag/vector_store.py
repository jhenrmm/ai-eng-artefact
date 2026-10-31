from sentence_transformers import util


def search(vector_store, query_embedding, k=3):
    similarities = util.cos_sim(query_embedding, vector_store)[0]
    return similarities.topk(k=min(k, len(vector_store)))
