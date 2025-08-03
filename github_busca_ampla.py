
import pandas as pd
import requests
import json
import time
from dotenv import load_dotenv
import os
import re

# === 1. Carrega token do arquivo .env ===
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# === 2. Funções auxiliares ===

def get_github_repos(query, per_page=100):
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={per_page}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json().get('items', [])
    except Exception as e:
        print(f"Erro em busca (search) '{query}': {e}")
        return []

def filtrar_ruins(lista_repos, palavras_excluir=None):
    ruins = ["test", "template", "hello", "starter", "bot"]
    if palavras_excluir:
        ruins.extend(palavras_excluir)
    return [
        repo for repo in lista_repos
        if all(p not in (repo.get('name') or "").lower() for p in ruins)
    ]

def gerar_variacoes_query(sigla, nome, campus=None):
    termos = set()
    sigla_lower = sigla.lower()
    nome = nome.lower()

    termos.add(sigla_lower)

    if campus and isinstance(campus, str):
        campus_clean = re.sub(r"[^a-z0-9]", "", campus.lower())
        termos.update([
            f"{sigla_lower}-{campus_clean}",
            f"{sigla_lower}/{campus_clean}",
            f"{sigla_lower} {campus_clean}",
            f"{sigla} Campus {campus}",
            f"{sigla} {campus}",
        ])

    if "instituto federal" in nome:
        termos.add(nome.replace("instituto federal de educação, ciência e tecnologia", "instituto federal"))
        termos.add(nome)
    elif "universidade federal" in nome:
        termos.add(nome)

    return list(termos)

def get_repo_details(repo):
    owner = repo.get('owner', {})
    is_org = owner.get('type') == 'Organization'
    org_data = {
        "login": owner.get("login"),
        "url": owner.get("html_url"),
        "tipo": owner.get("type")
    } if is_org else None

    license_name = repo.get('license', {}).get('spdx_id', 'N/A') if repo.get('license') else 'N/A'
    return {
        'Nome do Repositório': repo.get('name', 'N/A'),
        'Descricao': repo.get('description', 'N/A'),
        'Linguagem Principal': repo.get('language', 'N/A'),
        'Estrelas': repo.get('stargazers_count', 0),
        'Licenca': license_name,
        'Ultima Atualizacao': repo.get('updated_at', 'N/A'),
        'Link de Acesso': repo.get('html_url', 'N/A'),
        'Organizacao': is_org,
        'Dados Organizacao': org_data
    }

def load_institutions_data(file_path):
    try:
        return pd.read_csv(file_path)
    except:
        print(f"Erro ao carregar {file_path}")
        return pd.DataFrame()

def buscar_repositorios_instituicao(sigla, nome, campus=None):
    resultados = []
    queries = gerar_variacoes_query(sigla, nome, campus)
    for termo in queries:
        query = f'"{termo}" in:name,description'
        encontrados = get_github_repos(query)
        resultados.extend(filtrar_ruins(encontrados))
        time.sleep(1)
    return resultados

def generate_institutions_repos_json(df):
    json_data = []
    for _, row in df.iterrows():
        sigla = row["Sigla"]
        nome = row["Nome Completo"]
        url = row["URL Oficial"]
        campus = row.get("Campus", None)

        print(f"🔍 Buscando repositórios para {sigla} ({nome})")

        repos_raw = buscar_repositorios_instituicao(sigla, nome, campus)

        repos_dict = {}
        for repo in repos_raw:
            detalhes = get_repo_details(repo)
            chave = (detalhes["Nome do Repositório"], detalhes["Link de Acesso"])
            repos_dict[chave] = detalhes

        json_data.append({
            "Sigla": sigla,
            "Nome Completo": nome,
            "URL Oficial": url,
            "Repositorios": list(repos_dict.values())
        })
    return json_data

# === 3. Execução principal ===

if __name__ == "__main__":
    df_if = load_institutions_data("dados/institutos_federais.csv")
    df_uf = load_institutions_data("dados/universidades_federais.csv")

    todos_dados = []

    if not df_if.empty:
        print("\n--- Institutos Federais ---")
        todos_dados.extend(generate_institutions_repos_json(df_if))

    if not df_uf.empty:
        print("\n--- Universidades Federais ---")
        todos_dados.extend(generate_institutions_repos_json(df_uf))

    # Desduplicação final global
    seen = set()
    saida = {"institutions_data": []}
    for inst in todos_dados:
        novos_repos = []
        for r in inst["Repositorios"]:
            k = (r["Nome do Repositório"], r["Link de Acesso"])
            if k not in seen:
                novos_repos.append(r)
                seen.add(k)
        if novos_repos:
            saida["institutions_data"].append({
                "Sigla": inst["Sigla"],
                "Nome Completo": inst["Nome Completo"],
                "URL Oficial": inst["URL Oficial"],
                "Repositorios": novos_repos
            })

    with open("repositorios_github.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print("\n✅ Arquivo 'repositorios_federais_desduplicados.json' gerado com sucesso!")
