import json
from typing import Dict, Any

# Lista de palavras-chave a serem ignoradas nos títulos e descrições dos repositórios.
# Esta lista pode ser expandida conforme a necessidade.
CUSTOM_STOPWORDS = [
    'toad_-3-blooket', 'ifrs 9', 'l10n_tw_standard_ifrss', '.config', 'FBA port to iOS',
    'Best-Electronics-Appliances-for-Home-and-Kitchen---My-Home-Product-Guide', 'IFB-unix',
    'BlooketPanel', 'IFRExtractor-RS', 'xxx', 'CA378-AOIS_USB3-IFB', 'IFB-FAIR-data-training',
    'ifb-staff', 'Guide to excellent variety of Electronics Appliances', 'vapoursynth-colorbars-scripts',
    'wiki-is-mostly-fake-radom-words-word-,genrationr-', 'XPS9570-Firmware-IFR', 'UEFI-Variable-Editer',
    'IFRS 17', 'BlooketPanel', 'baidu', 'UEFI', 'ifrextractor-rs', 'wiki-is-mostly-fake-radom-words-word-genrationr-',
    'Bella'
]

def filter_repos_with_multiple_criteria(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filtra repositórios de um objeto JSON, aplicando múltiplos critérios de filtragem:
    1. A descrição deve ter no máximo 500 caracteres.
    2. O nome e a descrição não devem conter palavras-chave da lista de stopwords.
    3. O nome, descrição ou organização devem conter a sigla ou nome da instituição.

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
            
            # Garante que os valores não são None antes de chamar .lower()
            repo_name = (repo.get('Nome do Repositório') or '').lower()
            description = (repo.get('Descricao') or '')
            
            org_data = repo.get('Dados Organizacao', {})
            org_login = (org_data.get('login') or '').lower() if org_data else ''

            # CRITÉRIO 1: A descrição deve ter no máximo 500 caracteres.
            if len(description) > 500:
                continue

            description_lower = description.lower()
            
            # CRITÉRIO 2: O nome ou a descrição não podem conter stopwords.
            has_stopword = False
            for word in CUSTOM_STOPWORDS:
                if word in repo_name or word in description_lower:
                    has_stopword = True
                    break
            if has_stopword:
                continue

            # CRITÉRIO 3: O repositório deve conter a palavra-chave da instituição.
            is_valid_repo = False
            for keyword in institution_keywords:
                if keyword in repo_name or keyword in description_lower or keyword in org_login:
                    is_valid_repo = True
                    break
            
            if is_valid_repo:
                new_repos.append(repo)
                total_repos_kept += 1

        if new_repos:
            filtered_institution = institution.copy()
            filtered_institution['Repositorios'] = new_repos
            filtered_institutions.append(filtered_institution)

    # Cria a nova estrutura JSON com os dados filtrados.
    output_json_structure = {
        "institutions_data": filtered_institutions,
        "cluster_descriptions": input_data.get('cluster_descriptions', []) 
    }

    print(f"Processamento concluído. {total_repos_kept} de {total_repos_processed} repositórios mantidos.")
    return output_json_structure


# --- Exemplo de Uso ---

if __name__ == "__main__":
    # O arquivo de entrada é o 'repositorios_federais_com_clusters_visualizado.json'
    input_file = "repositorios_federais_desduplicados.json"
    output_file = "repositorios_federais_filtrados_multiplos_criterios.json"

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        filtered_data = filter_repos_with_multiple_criteria(data)

        if filtered_data:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False)
            print(f"O novo arquivo JSON foi salvo como '{output_file}'")
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON: O arquivo '{input_file}' pode estar corrompido.")
