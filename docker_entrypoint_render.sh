#!/bin/sh
set -eu
# O disco persistente é montado em runtime: garantir apenas a permissão da raiz.
mkdir -p /app/dados
chown entrevistador:entrevistador /app/dados
chmod 0700 /app/dados
exec gosu entrevistador "$@"
