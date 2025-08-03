import pandas as pd
import requests
import json
import time
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém o valor do token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Verifica se o token foi encontrado
if GITHUB_TOKEN:
    print(f"Token encontrado: {GITHUB_TOKEN}")
else:
    print("Token não encontrado no arquivo .env")


# --- 1. Configuração da API do GitHub ---
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# --- 2. Funções Auxiliares (mantidas as mesmas, mas com uma pequena alteração em get_repo_details) ---

def get_github_repos(query, per_page=100):
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={per_page}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar no GitHub para '{query}': {e}")
        return []
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON para '{query}'. Resposta: {response.text}")
        return []

def get_repo_details(repo):
    """
    Extrai detalhes relevantes de um objeto de repositório da API do GitHub,
    renomeando as chaves para o formato desejado no JSON.
    """
    license_name = repo.get('license', {}).get('spdx_id', 'N/A') if repo.get('license') else 'N/A'
    return {
        'Nome do Repositório': repo.get('name', 'N/A'),
        'Descricao': repo.get('description', 'N/A'),
        'Linguagem Principal': repo.get('language', 'N/A'),
        'Estrelas': repo.get('stargazers_count', 0),
        'Licenca': license_name,
        'Ultima Atualizacao': repo.get('updated_at', 'N/A'),
        'Link de Acesso': repo.get('html_url', 'N/A')
    }

def load_institutions_data(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {file_path}")
        return pd.DataFrame()

# --- 3. Nova Função para Processamento e Geração de JSON ---

def generate_institutions_repos_json(institutions_df, search_column):
    """
    Processa o DataFrame de instituições, busca repositórios e organiza os dados
    no formato JSON desejado.
    """
    json_output_data = []

    for index, row in institutions_df.iterrows():
        institution_acronym = row['Sigla']
        institution_full_name = row['Nome Completo']
        institution_url = row['URL Oficial']
        
        print(f"Buscando repositórios para: {institution_acronym} ({institution_full_name})")

        repos = get_github_repos(institution_acronym)
        
        institution_data = {
            'Sigla': institution_acronym,
            'Nome Completo': institution_full_name,
            'URL Oficial': institution_url,
            'Repositorios': []
        }

        if not repos:
            print(f"Nenhum repositório encontrado para {institution_acronym} ou erro na busca.")
            # Mesmo sem repositórios, a instituição é adicionada com uma lista vazia de repositórios
            json_output_data.append(institution_data)
            time.sleep(1) # Ainda atrasa para respeitar limites de taxa
            continue

        for repo in repos:
            repo_details = get_repo_details(repo)
            institution_data['Repositorios'].append(repo_details)
        
        json_output_data.append(institution_data)
        
        # Adiciona um pequeno atraso para respeitar os limites de taxa da API do GitHub
        time.sleep(1)

    return json_output_data

# --- 4. Execução Principal ---

if __name__ == "__main__":
    # Carregue o CSV de Institutos
    institutos_df = load_institutions_data('dados/institutos_federais.csv')
    # Carregue o CSV de Universidades
    universidades_df = load_institutions_data('dados/universidades_federais.csv')

    all_institutions_json_data = []

    # Processar Institutos
    if not institutos_df.empty:
        print("\n--- Gerando JSON para Institutos Federais ---")
        institutos_json = generate_institutions_repos_json(institutos_df, 'Sigla')
        all_institutions_json_data.extend(institutos_json)

    # Processar Universidades
    if not universidades_df.empty:
        print("\n--- Gerando JSON para Universidades Federais ---")
        universidades_json = generate_institutions_repos_json(universidades_df, 'Sigla')
        all_institutions_json_data.extend(universidades_json)
    
    # Salvar o JSON consolidado em um único arquivo
    output_json_filename = 'repositorios_federais.json'
    with open(output_json_filename, 'w', encoding='utf-8') as f:
        json.dump(all_institutions_json_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDados consolidados salvos em '{output_json_filename}'")
    print("\nProcesso concluído.")