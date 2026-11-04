#!/bin/sh
set -eu

ATTEMPTS="${MIGRATION_ATTEMPTS:-30}"
SLEEP_SECONDS="${MIGRATION_RETRY_SECONDS:-2}"

echo "Aplicando migrations do banco..."
attempt=1
until alembic upgrade head; do
    if [ "$attempt" -ge "$ATTEMPTS" ]; then
        echo "Não foi possível aplicar as migrations após ${ATTEMPTS} tentativas." >&2
        exit 1
    fi
    echo "Banco indisponível ou migration falhou (tentativa ${attempt}/${ATTEMPTS}). Nova tentativa em ${SLEEP_SECONDS}s..." >&2
    attempt=$((attempt + 1))
    sleep "$SLEEP_SECONDS"
done

echo "Migrations aplicadas. Iniciando a API..."
exec python main.py
