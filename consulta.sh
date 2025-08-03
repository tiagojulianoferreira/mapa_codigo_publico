#!/bin/bash

# O caminho completo para o diretório do projeto
PROJETO_DIR="/home/tiago/Documentos/projetos/mapa_codigo_publico/"

# Ativa o ambiente virtual
source "$PROJETO_DIR/.venv/bin/activate"

# Use o caminho completo para os scripts
sleep 2
python "$PROJETO_DIR/filtra_palavras_chave.py"
sleep 2
python "$PROJETO_DIR/filtrar_idiomas.py"
sleep 2

# Os comandos do git também podem precisar de caminhos absolutos, dependendo de onde o script é executado
# Exemplo: git -C "$PROJETO_DIR" add .
# Mas se você for usar o 'cd' da primeira opção, não precisa se preocupar com isso.
git add .
git commit -m "Atualização automática do mapa de código público"
git push origin main