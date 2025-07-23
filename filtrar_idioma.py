import json
from langdetect import detect, DetectorFactory
from langdetect import LangDetectException
import re

DetectorFactory.seed = 0

custom_title_stopwords = [
    'toad_-3-blooket','ifrs 9','l10n_tw_standard_ifrss','.config','FBA port to iOS',
    'Best-Electronics-Appliances-for-Home-and-Kitchen---My-Home-Product-Guide', 'IFB-unix',
    'BlooketPanel', 'IFRExtractor-RS', 'xxx','CA378-AOIS_USB3-IFB','IFB-FAIR-data-training',
    'ifb-staff','Guide to excellent variety of Electronics Appliances','vapoursynth-colorbars-scripts',
    'wiki-is-mostly-fake-radom-words-word-,genrationr-','XPS9570-Firmware-IFR','UEFI-Variable-Editer',
    'IFRS 17','BlooketPanel','baidu','UEFI','ifrextractor-rs'
]

def filter_repos_by_description_language(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f) # Renomeado para 'full_data' para clareza
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        return
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{input_file}' não é um JSON válido.")
        return

    # AQUI ESTÁ A MUDANÇA PRINCIPAL: Acesse a lista de instituições corretamente
    institutions_list = full_data.get('institutions_data', [])
    if not institutions_list:
        print(f"Aviso: Não foram encontradas informações de instituições na chave 'institutions_data' em '{input_file}'.")
        return

    filtered_data = [] # Esta será a lista de instituições filtradas que será salva
    total_repos_processed = 0
    total_repos_kept = 0

    # Itere sobre a lista de instituições
    for institution in institutions_list: # <-- AQUI MUDOU: itera sobre a lista de dicionários de instituições
        new_repos = []
        institution_sigla = institution.get('Sigla', '').lower()

        # O restante do seu código dentro deste loop permanece o mesmo
        for repo in institution.get('Repositorios', []): # Use .get() para repositórios também, caso esteja ausente
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
            if institution_sigla:
                if institution_sigla in repo_name:
                    clean_match_pattern = r'\b' + re.escape(institution_sigla) + r'(?:[ \-]|$)'
                    if not re.search(clean_match_pattern, repo_name):
                        continue

            # --- 3. FILTRO: Idioma da Descrição (lógica existente) ---
            if description is None or description.strip() == '':
                new_repos.append(repo)
                total_repos_kept += 1
                continue

            try:
                lang = detect(description)
                if lang == 'pt' or lang == 'en': # Mantendo ambos 'pt' e 'en' como no seu filtro original
                    new_repos.append(repo)
                    total_repos_kept += 1
            except LangDetectException:
                pass 

        # Adiciona a instituição apenas se ela tiver repositórios após a filtragem
        # ou se você quiser manter a instituição mesmo com lista vazia (ajuste aqui)
        if new_repos: # Ou 'if True:' se quiser manter todas as instituições, mesmo sem repos filtrados
            filtered_institution = institution.copy()
            filtered_institution['Repositorios'] = new_repos
            filtered_data.append(filtered_institution)

    try:
        # AQUI ESTÁ A MUDANÇA PARA SALVAR: Envolva a lista filtrada na chave 'institutions_data'
        output_json_structure = {"institutions_data": filtered_data}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_json_structure, f, indent=2, ensure_ascii=False)
        print(f"Processamento concluído. {total_repos_kept} de {total_repos_processed} repositórios mantidos.")
        print(f"O novo arquivo JSON foi salvo como '{output_file}'")
    except IOError as e:
        print(f"Erro ao escrever o arquivo '{output_file}': {e}")

# Nome do arquivo de entrada e saída
# Use 'repositorios_federais_desduplicados.json' se você usou o código anterior para gerar um arquivo com essa estrutura
input_json_file = 'repositorios_federais.json' # Verifique se este é o nome correto do seu arquivo
output_json_file = 'repositorios_federais_filtrado_idioma.json'

filter_repos_by_description_language(input_json_file, output_json_file)