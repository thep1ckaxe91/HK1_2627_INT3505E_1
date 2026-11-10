#!/usr/bin/env bash
set -euo pipefail

WHEELS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/wheels"
mkdir -p "${WHEELS_DIR}"

echo "=== Downloading Linux x86_64 wheels for Python 3.12 into ${WHEELS_DIR} ==="
pip download psycopg-binary \
    --platform manylinux_2_17_x86_64 \
    --only-binary=:all: \
    --python-version 312 \
    -d "${WHEELS_DIR}"

uv pip compile pyproject.toml -o /tmp/requirements.tmp.txt
pip download -r /tmp/requirements.tmp.txt \
    --platform manylinux_2_17_x86_64 \
    --only-binary=:all: \
    --python-version 312 \
    -d "${WHEELS_DIR}"
rm -f /tmp/requirements.tmp.txt

echo "=== Wheels successfully cached in ${WHEELS_DIR} ==="
