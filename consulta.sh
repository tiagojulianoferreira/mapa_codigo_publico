#!/bin/bash

# Define o caminho completo para o interpretador Python do seu ambiente virtual
PYTHON_VENV="./.venv/bin/python"

# Usa o caminho direto para o interpretador Python
$PYTHON_VENV filtra_palavras_chave.py
sleep 2
$PYTHON_VENV filtrar_idiomas.py
sleep 2

git add .
git commit -m "Atualização automática do mapa de código público"
git push origin main