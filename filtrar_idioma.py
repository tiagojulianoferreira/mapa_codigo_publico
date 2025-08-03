import json
from langdetect import detect, DetectorFactory
from langdetect import LangDetectException
import re

# Garante que a detecção de idioma seja determinística para o mesmo texto.
DetectorFactory.seed = 0

# Lista de palavras-chave a serem ignoradas nos títulos dos repositórios.
# Esta lista pode ser expandida conforme a necessidade.
custom_title_stopwords = [
    'toad_-3-blooket', 'ifrs 9', 'l10n_tw_standard_ifrss', '.config', 'FBA port to iOS',
    'Best-Electronics-Appliances-for-Home-and-Kitchen---My-Home-Product-Guide', 'IFB-unix',
    'BlooketPanel', 'IFRExtractor-RS', 'xxx', 'CA378-AOIS_USB3-IFB', 'IFB-FAIR-data-training',
    'ifb-staff', 'Guide to excellent variety of Electronics Appliances', 'vapoursynth-colorbars-scripts',
    'wiki-is-mostly-fake-radom-words-word-,genrationr-', 'XPS9570-Firmware-IFR', 'UEFI-Variable-Editer',
    'IFRS 17', 'BlooketPanel', 'baidu', 'UEFI', 'ifrextractor-rs', 'wiki-is-mostly-fake-radom-words-word-genrationr-',
    'Bella'
]

def filter_repos_by_description_language(input_file, output_file):
    """
    Filtra repositórios de um arquivo JSON por idioma da descrição,
    mantendo apenas os que têm descrição em português ('pt') ou inglês ('en'),
    além de repositórios sem descrição.

    O código também filtra repositórios com base em palavras-chave no título
    e siglas de instituições.

    Args:
        input_file (str): O caminho para o arquivo JSON de entrada.
        output_file (str): O caminho para o arquivo JSON de saída.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        return
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{input_file}' não é um JSON válido.")
        return

    # Acessa a lista de instituições a partir da chave 'institutions_data'.
    institutions_list = full_data.get('institutions_data', [])
    if not institutions_list:
        print(f"Aviso: Não foram encontradas informações de instituições na chave 'institutions_data' em '{input_file}'.")
        return

    # Acessa as descrições de cluster a partir da chave 'cluster_descriptions'.
    cluster_descriptions = full_data.get('cluster_descriptions', [])
    
    filtered_institutions = [] # Esta será a lista de instituições filtradas que será salva.
    total_repos_processed = 0
    total_repos_kept = 0

    # Itera sobre a lista de instituições.
    for institution in institutions_list:
        new_repos = []
        institution_sigla = institution.get('Sigla', '').lower()

        for repo in institution.get('Repositorios', []):
            total_repos_processed += 1
            repo_name = repo.get('Nome do Repositório', '').lower()
            description = repo.get('Descricao')

            # --- 1. FILTRO: Custom Stopwords no Título ---
            found_title_stopword = False
            for stop_word in custom_title_stopwords:
                if stop_word.lower() in repo_name:
                    found_title_stopword = True
                    break
            if found_title_stopword:
                continue

            # --- 2. FILTRO: Siglas da Instituição não seguidas por espaço/hífen no Título ---
            if institution_sigla and institution_sigla in repo_name:
                clean_match_pattern = r'\b' + re.escape(institution_sigla) + r'(?:[ \-]|$)'
                if not re.search(clean_match_pattern, repo_name):
                    continue

            # --- 3. FILTRO: Idioma da Descrição ---
            if description is None or description.strip() == '':
                # Se não houver descrição, o repositório é mantido.
                new_repos.append(repo)
                total_repos_kept += 1
                continue

            try:
                lang = detect(description)
                if lang == 'pt' or lang == 'en':
                    new_repos.append(repo)
                    total_repos_kept += 1
            except LangDetectException:
                # Se o idioma não puder ser detectado, o repositório é ignorado.
                pass 

        # Adiciona a instituição apenas se ela tiver repositórios após a filtragem.
        if new_repos:
            filtered_institution = institution.copy()
            filtered_institution['Repositorios'] = new_repos
            filtered_institutions.append(filtered_institution)

    try:
        # Cria a nova estrutura JSON com a lista de instituições filtradas e os clusters.
        output_json_structure = {
            "institutions_data": filtered_institutions,
            "cluster_descriptions": cluster_descriptions
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_json_structure, f, indent=2, ensure_ascii=False)
        print(f"Processamento concluído. {total_repos_kept} de {total_repos_processed} repositórios mantidos.")
        print(f"O novo arquivo JSON foi salvo como '{output_file}'")
    except IOError as e:
        print(f"Erro ao escrever o arquivo '{output_file}': {e}")

# Nome do arquivo de entrada e saída
# Você deve usar 'repositorios_federais_com_clusters_visualizado.json' como entrada.
input_json_file = 'repositorios_federais_com_clusters_visualizado.json'
output_json_file = 'repositorios_federais_filtrado_idioma.json'

# Chama a função para iniciar o processo de filtragem
filter_repos_by_description_language(input_json_file, output_json_file)
