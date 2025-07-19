import json
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Garante resultados consistentes da detecção de idioma
DetectorFactory.seed = 0

def filter_repos_by_description_language(input_file, output_file):
    """
    Remove repositórios cuja descrição não está em inglês ou português.

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
        for repo in institution['Repositorios']:
            total_repos_processed += 1
            description = repo.get('Descricao')

            if description is None or description.strip() == '':
                # Se não houver descrição, mantemos o repositório por padrão,
                # pois não podemos determinar o idioma.
                new_repos.append(repo)
                total_repos_kept += 1
                continue

            try:
                # Tenta detectar o idioma. Se for pt ou en, mantém.
                lang = detect(description)
                if lang == 'pt' or lang == 'en':
                    new_repos.append(repo)
                    total_repos_kept += 1
            except LangDetectException:
                # Se não for possível detectar o idioma, considera como "desconhecido" e o remove.
                # print(f"Não foi possível detectar o idioma da descrição: '{description[:50]}...'")
                pass # Não adiciona o repositório

        # Adiciona a instituição apenas se ela tiver repositórios após a filtragem
        if new_repos:
            # Cria uma nova cópia da instituição com os repositórios filtrados
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
input_json_file = 'repositorios_federais.json'
output_json_file = 'repositorios_federais_filtrado_idioma.json'

# Chama a função para filtrar
filter_repos_by_description_language(input_json_file, output_json_file)