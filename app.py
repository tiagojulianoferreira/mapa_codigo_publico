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

# --- 2. Funções Auxiliares (mantidas as mesmas) ---

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

# --- 3. Função para Processamento e Geração de JSON (alterada para não adicionar duplicatas intra-instituição) ---

def generate_institutions_repos_json(institutions_df, search_column):
    """
    Processa o DataFrame de instituições, busca repositórios e organiza os dados
    no formato JSON desejado. A função agora garante que não haja duplicatas
    de repositórios DENTRO da lista de repositórios de uma mesma instituição.
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
            json_output_data.append(institution_data)
            time.sleep(1)
            continue

        repositorios_unicos_para_instituicao = {} # Usar um dict para desduplicação (chave: (nome, link), valor: repo_details)

        for repo in repos:
            repo_details = get_repo_details(repo)
            chave_repo = (repo_details['Nome do Repositório'], repo_details['Link de Acesso'])
            # Adiciona ou substitui (se for uma atualização, o que não é o caso aqui)
            # Garante que cada combinação (Nome, Link) seja única para esta instituição
            repositorios_unicos_para_instituicao[chave_repo] = repo_details
        
        # Converte de volta para lista
        institution_data['Repositorios'] = list(repositorios_unicos_para_instituicao.values())
        
        json_output_data.append(institution_data)
        
        time.sleep(1)

    return json_output_data

# --- 4. Execução Principal (com desduplicação final) ---

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
    
    # --- NOVA ETAPA DE DESDUPLICAÇÃO FINAL ---
    # Esta etapa irá garantir que se o mesmo repositório aparecer em diferentes instituições,
    # ele só seja adicionado ao JSON final uma vez.
    
    final_json_output_data = {
        "institutions_data": []
    }
    
    # Um conjunto para rastrear (Sigla da Instituição, Nome do Repositório, Link de Acesso)
    # se o objetivo é ter um repositório único por Instituição + Repositório
    # OU
    # Um conjunto para rastrear (Nome do Repositório, Link de Acesso)
    # se o objetivo é ter cada repositório único em TODO o arquivo final,
    # independente da instituição.

    # Vou assumir a segunda opção, que um repositório com o mesmo nome e link
    # só deve aparecer uma vez em todo o arquivo JSON final.
    
    seen_repos_global = set()
    
    for institution_data in all_institutions_json_data:
        current_institution_repos = []
        for repo in institution_data.get('Repositorios', []):
            repo_key = (repo.get('Nome do Repositório'), repo.get('Link de Acesso'))
            if repo_key not in seen_repos_global:
                current_institution_repos.append(repo)
                seen_repos_global.add(repo_key)
        
        # Adiciona a instituição apenas se ela tiver repositórios únicos a serem incluídos
        if current_institution_repos:
            # Criar uma nova entrada de instituição para evitar referências indesejadas
            # e adicionar apenas os repositórios únicos.
            new_institution_entry = {
                'Sigla': institution_data['Sigla'],
                'Nome Completo': institution_data['Nome Completo'],
                'URL Oficial': institution_data['URL Oficial'],
                'Repositorios': current_institution_repos
            }
            final_json_output_data['institutions_data'].append(new_institution_entry)
        # Se uma instituição não tiver nenhum repo único (todos já foram vistos), ela não será adicionada.
        # Se você quiser que a instituição seja adicionada mesmo com lista de repositórios vazia,
        # ajuste a lógica.

    # Salvar o JSON consolidado em um único arquivo
    output_json_filename = 'repositorios_federais_desduplicados.json' # Novo nome para o arquivo de saída
    with open(output_json_filename, 'w', encoding='utf-8') as f:
        json.dump(final_json_output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDados consolidados e desduplicados salvos em '{output_json_filename}'")
    print("\nProcesso concluído.")