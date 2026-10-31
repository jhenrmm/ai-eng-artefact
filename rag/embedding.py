from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"

model = SentenceTransformer(MODEL_NAME)


def embed(texts):
    return model.encode(
        texts,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )
