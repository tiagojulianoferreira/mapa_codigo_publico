#!/bin/bash
#python github_busca_ampla.py
sleep 2
python filtra_palavras_chave.py
sleep 2
python filtrar_idiomas.py
sleep 2 
#python clusterizador.py
#sleep 2
git add .
git commit -m "Atualização automática do mapa de código público"
git push origin main