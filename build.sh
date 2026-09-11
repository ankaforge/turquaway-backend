#!/usr/bin/env bash
set -o errexit

python_bin="$(command -v python || command -v python3)"
"${python_bin}" manage.py migrate --no-input
"${python_bin}" manage.py collectstatic --no-input