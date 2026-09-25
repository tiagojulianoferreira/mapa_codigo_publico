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

# === 2. Funções auxiliares (MANTENDO COMPATIBILIDADE) ===

def get_github_repos_com_paginacao(query, max_paginas=10):
    """
    Versão com paginação completa - CAPTURA TODAS AS PÁGINAS
    Mantém o mesmo formato de retorno da função original (lista de repositórios)
    """
    todos_repos = []
    page = 1
    per_page = 100
    
    print(f"    📊 Buscando todas as páginas para: {query[:50]}...")
    
    while page <= max_paginas:
        url = f"https://api.github.com/search/repositories"
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': per_page,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = data.get('items', [])
            total_count = data.get('total_count', 0)
            
            if not items:
                print(f"      ✅ Página {page}: sem resultados - fim da busca")
                break
                
            print(f"      📄 Página {page}: {len(items)} repositórios (total encontrado: {total_count})")
            todos_repos.extend(items)
            
            # Verifica se é a última página
            if len(items) < per_page or len(todos_repos) >= total_count:
                print(f"      ✅ Última página alcançada. Total desta query: {len(todos_repos)}")
                break
                
            page += 1
            time.sleep(0.5)  # Pequena pausa entre páginas
            
        except Exception as e:
            print(f"      ❌ Erro na página {page}: {e}")
            break
    
    return todos_repos

def filtrar_ruins(lista_repos, palavras_excluir=None):
    """Função original MANTIDA IDÊNTICA"""
    ruins = ["test", "template", "hello", "starter", "bot"]
    if palavras_excluir:
        ruins.extend(palavras_excluir)
    return [
        repo for repo in lista_repos
        if all(p not in (repo.get('name') or "").lower() for p in ruins)
    ]

def gerar_variacoes_query(sigla, nome, campus=None):
    """Função original MANTIDA IDÊNTICA"""
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
    """Função original MANTIDA IDÊNTICA"""
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
    """Função original MANTIDA IDÊNTICA"""
    try:
        return pd.read_csv(file_path)
    except:
        print(f"Erro ao carregar {file_path}")
        return pd.DataFrame()

def buscar_repositorios_instituicao_melhorado(sigla, nome, campus=None):
    """
    Versão melhorada que USA PAGINAÇÃO, mas mantém a mesma assinatura da função original
    """
    resultados = []
    queries = gerar_variacoes_query(sigla, nome, campus)
    
    for i, termo in enumerate(queries):
        print(f"    🔎 Termo {i+1}/{len(queries)}: '{termo}'")
        
        # Query principal (mesma da original, mas com paginação)
        query = f'"{termo}" in:name,description'
        encontrados = get_github_repos_com_paginacao(query)
        
        # Filtra os ruins (usa a mesma função original)
        encontrados_filtrados = filtrar_ruins(encontrados)
        print(f"      ✅ Após filtro: {len(encontrados_filtrados)} repositórios")
        
        resultados.extend(encontrados_filtrados)
        
        # Pausa entre termos para respeitar rate limit
        if i < len(queries) - 1:
            time.sleep(1)
    
    # Remove duplicatas locais (mesmo repositório encontrado por queries diferentes)
    repos_unicos = {repo['id']: repo for repo in resultados}.values()
    
    print(f"    📊 Total único para '{sigla}': {len(repos_unicos)} repositórios")
    return list(repos_unicos)

def generate_institutions_repos_json(df):
    """
    Função adaptada para usar a versão com paginação
    MAS MANTÉM EXATAMENTE O MESMO FORMATO DE SAÍDA
    """
    json_data = []
    
    for idx, row in df.iterrows():
        sigla = row["Sigla"]
        nome = row["Nome Completo"]
        url = row["URL Oficial"]
        campus = row.get("Campus", None)

        print(f"\n🔍 [{idx+1}/{len(df)}] Buscando repositórios para {sigla} ({nome})")
        print("-" * 60)

        # USA A VERSÃO MELHORADA COM PAGINAÇÃO
        repos_raw = buscar_repositorios_instituicao_melhorado(sigla, nome, campus)

        # Remove duplicatas (mesma lógica original)
        repos_dict = {}
        for repo in repos_raw:
            detalhes = get_repo_details(repo)
            chave = (detalhes["Nome do Repositório"], detalhes["Link de Acesso"])
            repos_dict[chave] = detalhes

        # MESMA ESTRUTURA ORIGINAL
        json_data.append({
            "Sigla": sigla,
            "Nome Completo": nome,
            "URL Oficial": url,
            "Repositorios": list(repos_dict.values())
        })
        
        print(f"  ✅ {sigla}: {len(repos_dict)} repositórios salvos")
        
        # Pausa entre instituições
        if idx < len(df) - 1:
            time.sleep(2)
    
    return json_data

# === 3. Execução principal (MANTENDO O MESMO NOME DE ARQUIVO) ===

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 INICIANDO BUSCA DE REPOSITÓRIOS FEDERAIS (COM PAGINAÇÃO COMPLETA)")
    print("=" * 70)
    
    # Carrega dados (MESMOS arquivos)
    df_if = load_institutions_data("dados/institutos_federais.csv")
    df_uf = load_institutions_data("dados/universidades_federais.csv")

    todos_dados = []

    # Processa Institutos Federais
    if not df_if.empty:
        print("\n📚 PROCESSTANDO INSTITUTOS FEDERAIS")
        print("=" * 40)
        todos_dados.extend(generate_institutions_repos_json(df_if))

    # Processa Universidades Federais
    if not df_uf.empty:
        print("\n📚 PROCESSTANDO UNIVERSIDADES FEDERAIS")
        print("=" * 40)
        todos_dados.extend(generate_institutions_repos_json(df_uf))

    # Desduplicação global final (MESMA LÓGICA ORIGINAL)
    print("\n🔄 REALIZANDO DESDUPLICAÇÃO GLOBAL...")
    print("=" * 40)
    
    seen = set()
    saida = {"institutions_data": []}
    
    total_repos_antes = 0
    for inst in todos_dados:
        total_repos_antes += len(inst["Repositorios"])
    
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
    
    total_repos_depois = sum(len(inst["Repositorios"]) for inst in saida["institutions_data"])

    # SALVA COM O MESMO NOME DO ARQUIVO ORIGINAL
    arquivo_saida = "repositorios_federais_desduplicados.json"
    
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    # Estatísticas finais
    print("\n" + "=" * 70)
    print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    print("=" * 70)
    print(f"📁 Arquivo gerado: {arquivo_saida}")
    print(f"📊 Total de instituições processadas: {len(todos_dados)}")
    print(f"📊 Total de instituições na saída: {len(saida['institutions_data'])}")
    print(f"📊 Total de repositórios (antes da desduplicação): {total_repos_antes}")
    print(f"📊 Total de repositórios únicos: {total_repos_depois}")
    print(f"📊 Repositórios duplicados removidos: {total_repos_antes - total_repos_depois}")
    print("=" * 70)
    
    # Salva um log com estatísticas detalhadas (opcional - não interfere no arquivo principal)
    with open("log_busca.txt", "w", encoding="utf-8") as f:
        f.write(f"Data da busca: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total de instituições: {len(saida['institutions_data'])}\n")
        f.write(f"Total de repositórios únicos: {total_repos_depois}\n\n")
        f.write("Detalhamento por instituição:\n")
        for inst in saida["institutions_data"]:
            f.write(f"  {inst['Sigla']}: {len(inst['Repositorios'])} repositórios\n")