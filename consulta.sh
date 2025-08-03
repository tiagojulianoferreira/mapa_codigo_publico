#!/bin/bash

# Define o caminho para o interpretador python do ambiente virtual
PYTHON_VENV="./.venv/bin/python"

# Use a variável para chamar os scripts
sleep 2
$PYTHON_VENV filtra_palavras_chave.py
sleep 2
$PYTHON_VENV filtrar_idiomas.py
sleep 2

git add .
git commit -m "Atualização automática do mapa de código público"
git push origin main