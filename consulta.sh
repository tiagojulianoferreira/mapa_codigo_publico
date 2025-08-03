source .venv/bin/activate
#python github_busca_ampla.py
sleep 2
python3 filtrar_palavras_chave.py
sleep 2
python3 filtrar_idiomas.py
sleep 2 
#python clusterizador.py
#sleep 2
git add .
git commit -m "Atualização automática do mapa de código público"
git push origin main