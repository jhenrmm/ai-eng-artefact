from sentence_transformers import SentenceTransformer
from config import ST_MODEL_NAME

model = SentenceTransformer(ST_MODEL_NAME)


def embed(texts):
    return model.encode(
        texts,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )
