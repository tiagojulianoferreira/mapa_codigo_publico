import json
from typing import Dict, List, Any
import os

def criar_arquivo_stopwords_se_nao_existir(file_path: str):
    """
    Cria um arquivo de stopwords padrão se ele não existir,
    com uma lista de palavras para começar.
    """
    if not os.path.exists(file_path):
        default_stopwords = [
            'toad_-3-blooket', 'ifrs 9', 'l10n_tw_standard_ifrss', '.config',
            'Best-Electronics-Appliances-for-Home-and-Kitchen---My-Home-Product-Guide',
            'BlooketPanel', 'xxx', 'IFRS 17', 'baidu', 'UEFI', 'linux', 'windows', 'mac'
        ]
        with open(file_path, 'w', encoding='utf-8') as f:
            for word in default_stopwords:
                f.write(f"{word}\n")
        print(f"Arquivo de stopwords '{file_path}' criado com sucesso.")

def carregar_stopwords(file_path: str) -> List[str]:
    """
    Carrega as palavras-chave de um arquivo de texto, uma por linha.
    """
    criar_arquivo_stopwords_se_nao_existir(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Lê cada linha, remove espaços em branco no início e fim e filtra linhas vazias
            stopwords = [line.strip() for line in f if line.strip()]
        return stopwords
    except FileNotFoundError:
        print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
        return []
    except IOError as e:
        print(f"Erro ao ler o arquivo '{file_path}': {e}")
        return []

def carregar_palavras_chave_instituicoes(file_path: str) -> Dict[str, List[str]]:
    """
    Carrega as palavras-chave das instituições de um arquivo JSON
    e as organiza em um dicionário para busca rápida.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        keywords_map = {}
        for institution in data.get('institutions_keywords', []):
            sigla = institution.get('Sigla')
            keywords = institution.get('Palavras_Chave', [])
            if sigla and keywords:
                keywords_map[sigla] = keywords
        return keywords_map
    except FileNotFoundError:
        print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
        return {}
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{file_path}' não é um JSON válido.")
        return {}

def filtrar_repositorios_por_palavras_chave(
    repos_data_file: str,
    keywords_file: str,
    stopwords_file: str,
    output_file: str
) -> None:
    """
    Filtra os repositórios de um arquivo JSON usando as palavras-chave
    dinamicamente carregadas de outro arquivo JSON e removendo stopwords
    de um arquivo de texto.
    """
    # Carrega as palavras-chave das instituições
    keywords_by_institution = carregar_palavras_chave_instituicoes(keywords_file)
    if not keywords_by_institution:
        print("Palavras-chave não foram carregadas. Processo de filtragem abortado.")
        return

    # Carrega a lista de stopwords do arquivo de texto
    custom_stopwords = carregar_stopwords(stopwords_file)
    if not custom_stopwords:
        print(f"Aviso: Não foi possível carregar as stopwords do arquivo '{stopwords_file}'. A filtragem por stopwords não será aplicada.")
        
    # Carrega os dados dos repositórios
    try:
        with open(repos_data_file, 'r', encoding='utf-8') as f:
            repos_data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O arquivo de repositórios '{repos_data_file}' não foi encontrado.")
        return
    except json.JSONDecodeError:
        print(f"Erro: O arquivo de repositórios '{repos_data_file}' não é um JSON válido.")
        return

    filtered_institutions = []
    total_repos_kept = 0
    total_repos_processed = 0
    stopwords_lower = [sw.lower() for sw in custom_stopwords]

    print(f"\nIniciando filtragem de repositórios usando palavras-chave de '{keywords_file}' e removendo stopwords de '{stopwords_file}'...")
    
    for institution in repos_data.get('institutions_data', []):
        sigla = institution.get('Sigla')
        
        institution_keywords = keywords_by_institution.get(sigla, [])
        if not institution_keywords:
            continue
            
        new_repos = []
        for repo in institution.get('Repositorios', []):
            total_repos_processed += 1
            repo_name = str(repo.get('Nome do Repositório', '')).lower()
            repo_desc = str(repo.get('Descricao', '')).lower()
            
            keywords_lower = [k.lower() for k in institution_keywords]
            
            contains_keyword = any(keyword in repo_name or keyword in repo_desc for keyword in keywords_lower)
            
            contains_stopwords = any(sw in repo_name or sw in repo_desc for sw in stopwords_lower)
            
            if contains_keyword and not contains_stopwords:
                new_repos.append(repo)
                total_repos_kept += 1
        
        if new_repos:
            filtered_institution = institution.copy()
            filtered_institution['Repositorios'] = new_repos
            filtered_institutions.append(filtered_institution)

    output_json_structure = {
        "institutions_data": filtered_institutions,
        "cluster_descriptions": repos_data.get('cluster_descriptions', [])
    }
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_json_structure, f, indent=2, ensure_ascii=False)
        print(f"\nProcessamento concluído. {total_repos_kept} de {total_repos_processed} repositórios mantidos.")
        print(f"O novo arquivo JSON foi salvo como '{output_file}'.")
    except IOError as e:
        print(f"Erro ao escrever o arquivo '{output_file}': {e}")


if __name__ == "__main__":
    input_repos_file = 'repositorios_federais_desduplicados.json'
    input_keywords_file = 'palavras_chave_instituicoes_v2.json'
    input_stopwords_file = 'stopwords.txt'
    output_filtered_file = 'repositorios_filtrados.json'

    filtrar_repositorios_por_palavras_chave(input_repos_file, input_keywords_file, input_stopwords_file, output_filtered_file)
