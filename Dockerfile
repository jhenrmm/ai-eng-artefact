# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/cache/sentence-transformers

WORKDIR /app

# libgomp1 é exigido pelo PyTorch; o restante do stack usa wheels binárias.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Instala o PyTorch CPU antes do restante para evitar baixar as wheels CUDA
# (~2 GB) que o PyPI usaria por padrão em Linux.
ARG TORCH_VERSION=2.15.0+cpu
RUN pip install "torch==${TORCH_VERSION}" \
        --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY . .

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /cache/huggingface /cache/sentence-transformers \
    && chown -R appuser:appuser /app /cache

USER appuser

EXPOSE 8000

ENTRYPOINT ["entrypoint.sh"]
