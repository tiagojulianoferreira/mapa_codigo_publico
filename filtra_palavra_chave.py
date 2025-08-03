import json
from typing import Dict, Any

def filter_repos_by_institution_keywords(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filtra repositórios de um objeto JSON, mantendo apenas aqueles que contêm
    a sigla ou o nome completo de uma instituição em seu nome, descrição ou organização.

    Args:
        input_data (Dict[str, Any]): O dicionário JSON de entrada com a estrutura 'institutions_data'.

    Returns:
        Dict[str, Any]: Um novo dicionário JSON com os repositórios filtrados.
    """
    if 'institutions_data' not in input_data:
        print("Erro: A chave 'institutions_data' não foi encontrada no JSON de entrada.")
        return {}

    # 1. Coletar todas as palavras-chave (siglas e nomes completos) das instituições.
    institution_keywords = set()
    for institution in input_data['institutions_data']:
        sigla = institution.get('Sigla')
        nome_completo = institution.get('Nome Completo')
        if sigla:
            institution_keywords.add(sigla.lower())
        if nome_completo:
            for word in nome_completo.lower().split():
                if len(word) > 2:
                    institution_keywords.add(word)

    print(f"Palavras-chave de filtragem geradas: {institution_keywords}")

    filtered_institutions = []
    total_repos_processed = 0
    total_repos_kept = 0
    
    for institution in input_data['institutions_data']:
        new_repos = []
        for repo in institution.get('Repositorios', []):
            total_repos_processed += 1
            
            # CORREÇÃO: Garante que os valores não são None antes de chamar .lower()
            repo_name = (repo.get('Nome do Repositório') or '').lower()
            description = (repo.get('Descricao') or '').lower()
            
            org_data = repo.get('Dados Organizacao', {})
            org_login = (org_data.get('login') or '').lower() if org_data else ''
            
            # 2. Verificar se alguma palavra-chave está presente nos metadados do repositório.
            is_valid_repo = False
            for keyword in institution_keywords:
                if keyword in repo_name or keyword in description or keyword in org_login:
                    is_valid_repo = True
                    break
            
            if is_valid_repo:
                new_repos.append(repo)
                total_repos_kept += 1

        if new_repos:
            filtered_institution = institution.copy()
            filtered_institution['Repositorios'] = new_repos
            filtered_institutions.append(filtered_institution)

    # 3. Cria a nova estrutura JSON com os dados filtrados.
    output_json_structure = {
        "institutions_data": filtered_institutions,
        "cluster_descriptions": input_data.get('cluster_descriptions', []) 
    }

    print(f"Processamento concluído. {total_repos_kept} de {total_repos_processed} repositórios mantidos.")
    return output_json_structure


# --- 4. Exemplo de Uso (demonstrando como carregar e usar a função) ---

if __name__ == "__main__":
    input_file = "repositorios_federais_desduplicados.json"
    output_file = "repositorios_federais_filtrados_por_sigla.json"

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        filtered_data = filter_repos_by_institution_keywords(data)

        if filtered_data:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False)
            print(f"O novo arquivo JSON foi salvo como '{output_file}'")
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON: O arquivo '{input_file}' pode estar corrompido.")
