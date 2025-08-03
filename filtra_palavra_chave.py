import json
from typing import Dict, List, Any

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
                # Usa a sigla como chave para buscar as palavras-chave associadas
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
    output_file: str
) -> None:
    """
    Filtra os repositórios de um arquivo JSON usando as palavras-chave
    dinamicamente carregadas de outro arquivo JSON.
    """
    # Carrega as palavras-chave
    keywords_by_institution = carregar_palavras_chave_instituicoes(keywords_file)
    if not keywords_by_institution:
        print("Palavras-chave não foram carregadas. Processo de filtragem abortado.")
        return

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

    print(f"\nIniciando filtragem de repositórios usando palavras-chave de '{keywords_file}'...")
    
    for institution in repos_data.get('institutions_data', []):
        sigla = institution.get('Sigla')
        
        # Pega a lista de palavras-chave para esta instituição
        institution_keywords = keywords_by_institution.get(sigla, [])
        if not institution_keywords:
            # Se não houver palavras-chave para a instituição, não filtramos seus repositórios
            # ou podemos optar por ignorá-la. Aqui, vamos ignorar.
            continue
            
        new_repos = []
        for repo in institution.get('Repositorios', []):
            total_repos_processed += 1
            repo_name = str(repo.get('Nome do Repositório', '')).lower()
            repo_desc = str(repo.get('Descricao', '')).lower()
            
            # Converte as palavras-chave para minúsculas
            keywords_lower = [k.lower() for k in institution_keywords]
            
            # Verifica se o nome ou a descrição do repositório contém alguma palavra-chave
            if any(keyword in repo_name or keyword in repo_desc for keyword in keywords_lower):
                new_repos.append(repo)
                total_repos_kept += 1
        
        if new_repos:
            filtered_institution = institution.copy()
            filtered_institution['Repositorios'] = new_repos
            filtered_institutions.append(filtered_institution)

    # Cria a nova estrutura JSON com os dados filtrados.
    output_json_structure = {
        "institutions_data": filtered_institutions,
        # Mantém as descrições dos clusters se existirem no arquivo original
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
    # Nomes dos arquivos de entrada e saída
    # O arquivo de repositórios a ser filtrado
    input_repos_file = 'repositorios_federais_com_clusters_visualizado.json'
    # O arquivo de palavras-chave gerado pelo script anterior
    input_keywords_file = 'palavras_chave_instituicoes_v2.json'
    # O arquivo onde o resultado será salvo
    output_filtered_file = 'repositorios_federais_filtrados_dinamico.json'

    filtrar_repositorios_por_palavras_chave(input_repos_file, input_keywords_file, output_filtered_file)
