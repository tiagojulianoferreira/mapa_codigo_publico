import pandas as pd
import requests
import json
import time
from dotenv import load_dotenv
import os

# === 1. Carrega token do arquivo .env ===
# Certifique-se de ter um arquivo .env no mesmo diretório com GITHUB_TOKEN=SEU_TOKEN_AQUI
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Verifica se o token foi carregado
if not GITHUB_TOKEN:
    print("Erro: GITHUB_TOKEN não encontrado no arquivo .env. Por favor, crie um arquivo .env com 'GITHUB_TOKEN=SEU_TOKEN_AQUI'.")
    exit()

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# === 2. Funções auxiliares ===

def get_github_repos(query, per_page=100, retries=3, backoff_factor=0.5):
    """
    Busca repositórios no GitHub com tratamento de rate limit e retentativas aprimoradas.
    """
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={per_page}"
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status() # Lança um HTTPError para respostas de erro (4xx ou 5xx)

            # --- Tratamento de Rate Limit ---
            remaining_requests = int(response.headers.get('X-RateLimit-Remaining', 0))
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            current_time = int(time.time())

            if remaining_requests == 0:
                sleep_duration = max(reset_time - current_time + 1, 0) # Adiciona +1 segundo para segurança
                print(f"🚨 Rate limit atingido. Dormindo por {sleep_duration} segundos até o reset.")
                time.sleep(sleep_duration)
                continue # Tenta novamente após a pausa

            return response.json().get('items', [])

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403 and "rate limit exceeded" in str(e).lower():
                # Tratamento específico para 403 quando o rate limit é excedido
                remaining_requests = int(e.response.headers.get('X-RateLimit-Remaining', 0))
                reset_time = int(e.response.headers.get('X-RateLimit-Reset', 0))
                current_time = int(time.time())
                sleep_duration = max(reset_time - current_time + 1, 0) # Adiciona +1 segundo para segurança
                print(f"🚨 Rate limit atingido (HTTP 403). Dormindo por {sleep_duration} segundos até o reset.")
                time.sleep(sleep_duration)
                continue # Tenta novamente após a pausa
            elif e.response.status_code == 422: # Tratamento específico para 422 (Unprocessable Entity)
                print(f"🚫 Erro HTTP 422 (Entidade Não Processável) para a query '{query}'. Isso pode indicar que a organização não existe no GitHub ou o formato da query 'org:' não é aplicável. Não será retentado para este tipo de erro.")
                return [] # Não retenta para 422, apenas retorna vazio para que o fallback funcione
            elif e.response.status_code >= 500: # Erros de servidor (5xx), tentam novamente
                sleep_time = backoff_factor * (2 ** attempt)
                print(f"⚠️ Erro de servidor ({e.response.status_code}). Tentando novamente em {sleep_time:.1f} segundos...")
                time.sleep(sleep_time)
                continue
            else: # Outros erros HTTP, não tentam novamente
                print(f"Erro HTTP inesperado ({e.response.status_code}) em '{query}': {e}")
                return []
        except requests.exceptions.RequestException as e: # Erros gerais de requisição (conexão, DNS, etc.)
            sleep_time = backoff_factor * (2 ** attempt)
            print(f"⚠️ Erro de requisição em '{query}': {e}. Tentando novamente em {sleep_time:.1f} segundos...")
            time.sleep(sleep_time)
            continue
    print(f"❌ Falha ao buscar repositórios para '{query}' após {retries} tentativas.")
    return []

def filtrar_ruins(lista_repos, palavras_excluir=None):
    """
    Filtra repositórios com base em palavras-chave a serem excluídas e popularidade mínima.
    """
    # Expandindo a lista de palavras a excluir para melhorar a precisão
    ruins = ["test", "template", "hello", "starter", "bot", "demo", "example", "tutorial", 
             "boilerplate", "awesome", "curso", "aula", "my-repo", "repositorio-exemplo"]
    if palavras_excluir:
        ruins.extend(palavras_excluir)
    return [
        repo for repo in lista_repos
        if all(p not in (repo.get('name') or "").lower() for p in ruins) and
           all(p not in (repo.get('description') or "").lower() for p in ruins) and # Também filtra na descrição
           (repo.get('stargazers_count', 0) > 0 or repo.get('forks_count', 0) > 0 or repo.get('watchers_count', 0) > 0) # Adiciona critério de popularidade mínima
    ]

def buscar_repositorios_instituicao(sigla, nome_completo):
    """
    Busca repositórios para uma dada instituição usando múltiplas estratégias.
    """
    sigla_lower = sigla.lower()
    
    # 1. Tenta buscar via organização (mais preciso e recomendado)
    org_query = f"org:{sigla_lower}"
    repos = get_github_repos(org_query)
    if repos:
        print(f"  ✅ Encontrados repos via organização '{sigla}'.")
        return filtrar_ruins(repos)

    # 2. Busca por sigla e nome completo em nome/descrição com popularidade
    # Inclui o nome completo para cobrir mais casos
    alt_query = f'"{sigla_lower}" in:name,description stars:>=1 OR "{nome_completo.lower()}" in:name,description stars:>=1'
    repos = get_github_repos(alt_query)
    if repos:
        print(f"  ✅ Encontrados repos por sigla/nome em nome/descrição.")
        return filtrar_ruins(repos)

    # 3. Busca por nome ajustado (último recurso)
    # Melhorando o ajuste do nome para mais abrangência, removendo preposições comuns
    nome_alt = nome_completo.lower().replace("universidade", "uni").replace("instituto federal", "if")
    nome_alt = nome_alt.replace("de ", "").replace("da ", "").replace("do ", "").replace("das ", "").replace("dos ", "")
    # Remove espaços extras se houver
    nome_alt = ' '.join(nome_alt.split()) 
    nome_query = f'"{nome_alt}" in:description stars:>=1'
    repos = get_github_repos(nome_query)
    if repos:
        print(f"  ✅ Encontrados repos por nome ajustado na descrição.")
        return filtrar_ruins(repos)
    
    print(f"  ⚠️ Nenhum repositório relevante encontrado para {sigla} após todas as tentativas.")
    return []

def get_repo_details(repo):
    """
    Extrai detalhes relevantes de um objeto de repositório do GitHub.
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
    """
    Carrega os dados das instituições a partir de um arquivo CSV.
    """
    try:
        # Assumindo que o CSV é separado por vírgulas e codificado em UTF-8
        return pd.read_csv(file_path, encoding='utf-8')
    except FileNotFoundError:
        print(f"Erro: O arquivo '{file_path}' não foi encontrado. Certifique-se de que ele está no diretório correto.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao carregar '{file_path}': {e}")
        return pd.DataFrame()

def generate_institutions_repos_json(df):
    """
    Gera uma lista de dados de repositórios para cada instituição no DataFrame.
    """
    json_data = []
    for index, row in df.iterrows():
        sigla = row["Sigla"]
        nome = row["Nome Completo"]
        url = row["URL Oficial"]
        print(f"🔍 Buscando repositórios para {sigla} ({nome})")
        
        repos_raw = buscar_repositorios_instituicao(sigla, nome)

        repos_dict = {}
        for repo in repos_raw:
            detalhes = get_repo_details(repo)
            chave = (detalhes["Nome do Repositório"], detalhes["Link de Acesso"])
            repos_dict[chave] = detalhes

        if repos_dict: # Apenas adiciona se repositórios foram encontrados para a instituição
            json_data.append({
                "Sigla": sigla,
                "Nome Completo": nome,
                "URL Oficial": url,
                "Repositorios": list(repos_dict.values())
            })

    return json_data

# === 3. Execução principal ===

if __name__ == "__main__":
    # Certifique-se de que o arquivo 'institutos_federais.csv' esteja no mesmo diretório
    df_if = load_institutions_data("institutos_federais.csv")
    
    # O arquivo 'universidades_federais.csv' não foi fornecido, então está comentado.
    # Se você tiver esse arquivo, descomente e ajuste o caminho.
    # df_uf = load_institutions_data("dados/universidades_federais.csv") 

    todos_dados = []

    if not df_if.empty:
        print("\n--- Processando Institutos Federais ---")
        todos_dados.extend(generate_institutions_repos_json(df_if))

    # if not df_uf.empty:
    #     print("\n--- Processando Universidades Federais ---")
    #     todos_dados.extend(generate_institutions_repos_json(df_uf))

    # Desduplicação final global de repositórios
    seen = set()
    saida = {"institutions_data": []}
    for inst in todos_dados:
        novos_repos = []
        for r in inst["Repositorios"]:
            k = (r["Nome do Repositório"], r["Link de Acesso"])
            if k not in seen:
                novos_repos.append(r)
                seen.add(k)
        if novos_repos: # Apenas anexa a instituição se ela tiver repositórios únicos
            saida["institutions_data"].append({
                "Sigla": inst["Sigla"],
                "Nome Completo": inst["Nome Completo"],
                "URL Oficial": inst["URL Oficial"],
                "Repositorios": novos_repos
            })

    # Salva o resultado em um novo arquivo JSON
    try:
        with open("repositorios_federais_desduplicados_melhorado_v2.json", "w", encoding="utf-8") as f: # Novo nome de arquivo para V2
            json.dump(saida, f, ensure_ascii=False, indent=2)
        print("\n✅ Arquivo 'repositorios_federais_desduplicados_melhorado_v2.json' gerado com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro ao salvar o arquivo JSON: {e}")