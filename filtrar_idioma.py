import json
from langdetect import detect, DetectorFactory
from langdetect import LangDetectException
import re # Importar o módulo re para usar expressões regulares

# Garante resultados consistentes da detecção de idioma
DetectorFactory.seed = 0

# --- NOVAS STOPWORDS CUSTOMIZADAS PARA FILTRAGEM DO TÍTULO DO REPOSITÓRIO ---
# Estas são frases exatas (case-insensitive) que, se encontradas no "Nome do Repositório",
# farão com que o repositório seja descartado do JSON de saída.
custom_title_stopwords = [
    'toad_-3-blooket','ifrs 9','l10n_tw_standard_ifrss','.config','FBA port to iOS',
    'Best-Electronics-Appliances-for-Home-and-Kitchen---My-Home-Product-Guide', 'IFB-unix',
    'BlooketPanel', 'IFRExtractor-RS', 'xxx','CA378-AOIS_USB3-IFB','IFB-FAIR-data-training',
    'ifb-staff','Guide to excellent variety of Electronics Appliances','vapoursynth-colorbars-scripts',
    'wiki-is-mostly-fake-radom-words-word-,genrationr-','XPS9570-Firmware-IFR','UEFI-Variable-Editer',
    'IFRS 17','BlooketPanel','baidu','UEFI','ifrextractor-rs'
]

def filter_repos_by_description_language(input_file, output_file):
    """
    Remove repositórios que não atendam aos critérios de filtragem:
    - Descrição não está em inglês ou português.
    - Título contém stopwords personalizadas específicas.
    - Título contém a sigla da instituição de forma "grudada" (não seguida por espaço/hífen).

    Args:
        input_file (str): Caminho para o arquivo JSON de entrada.
        output_file (str): Caminho para o arquivo JSON de saída.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        return
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{input_file}' não é um JSON válido.")
        return

    filtered_data = []
    total_repos_processed = 0
    total_repos_kept = 0

    for institution in data:
        new_repos = []
        # Converte a sigla da instituição para minúsculas para comparação case-insensitive
        institution_sigla = institution.get('Sigla', '').lower() 

        for repo in institution['Repositorios']:
            total_repos_processed += 1
            # Converte o nome do repositório para minúsculas para comparação case-insensitive
            repo_name = repo.get('Nome do Repositório', '').lower()
            description = repo.get('Descricao')

            # --- 1. FILTRO: Custom Stopwords no Título ---
            # Verifica se o nome do repositório contém alguma das stopwords personalizadas
            found_title_stopword = False
            for stop_word in custom_title_stopwords:
                if stop_word.lower() in repo_name:
                    found_title_stopword = True
                    break
            if found_title_stopword:
                # print(f"DEBUG: Removido por stopword no título: {repo.get('Nome do Repositório')}") # Linha de depuração opcional
                continue # Pula para o próximo repositório

            # --- 2. FILTRO: Siglas da Instituição não seguidas por espaço/hífen no Título ---
            # Este filtro só é aplicado se a sigla da instituição não for vazia
            if institution_sigla:
                # Primeiro, verifica se a sigla está presente no nome do repositório
                if institution_sigla in repo_name:
                    # Padrão para uma "ocorrência limpa" da sigla:
                    # \b: borda de palavra (garante que a sigla não é prefixo de outra palavra, ex: 'unb' em 'unbound' não bateria nesta parte)
                    # re.escape(institution_sigla): escapa caracteres especiais na sigla
                    # (?:[ \-]|$): grupo não-capturante que verifica se a sigla é seguida por um espaço, hífen, OU pelo final da string.
                    clean_match_pattern = r'\b' + re.escape(institution_sigla) + r'(?:[ \-]|$)'
                    
                    # Se NÃO for encontrada uma "ocorrência limpa", significa que a sigla está "grudada" ou mal formatada.
                    if not re.search(clean_match_pattern, repo_name):
                        # print(f"DEBUG: Removido por sigla problemática: {repo.get('Nome do Repositório')} (Sigla detectada: {institution_sigla})") # Linha de depuração opcional
                        continue # Pula para o próximo repositório

            # --- 3. FILTRO: Idioma da Descrição (lógica existente) ---
            if description is None or description.strip() == '':
                # Se não houver descrição, mantemos o repositório por padrão
                new_repos.append(repo)
                total_repos_kept += 1
                continue

            try:
                # Tenta detectar o idioma. Se for pt ou en, mantém.
                lang = detect(description)
                if lang == 'pt': # or lang == 'en':
                    new_repos.append(repo)
                    total_repos_kept += 1
            except LangDetectException:
                # Se não for possível detectar o idioma, o repositório é descartado.
                # print(f"DEBUG: Não foi possível detectar o idioma da descrição: '{description[:50]}...'") # Linha de depuração opcional
                pass 

        # Adiciona a instituição apenas se ela tiver repositórios após a filtragem
        if new_repos:
            filtered_institution = institution.copy()
            filtered_institution['Repositorios'] = new_repos
            filtered_data.append(filtered_institution)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        print(f"Processamento concluído. {total_repos_kept} de {total_repos_processed} repositórios mantidos.")
        print(f"O novo arquivo JSON foi salvo como '{output_file}'")
    except IOError as e:
        print(f"Erro ao escrever o arquivo '{output_file}': {e}")

# Nome do arquivo de entrada e saída
input_json_file = 'repositorios_federais.json' # Certifique-se que este é o JSON original
output_json_file = 'repositorios_federais_filtrado_idioma.json'

# Chama a função para filtrar
filter_repos_by_description_language(input_json_file, output_json_file)