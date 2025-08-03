import json
from langdetect import detect, DetectorFactory, LangDetectException
import re
from typing import List, Dict, Any

# Garante que a detecção de idioma seja determinística para o mesmo texto.
DetectorFactory.seed = 0

def filter_repos_by_language(input_data: Dict[str, Any], accepted_languages: List[str]) -> Dict[str, Any]:
    """
    Filtra repositórios por idioma da descrição e do nome, mantendo apenas aqueles onde
    pelo menos um dos campos (descrição ou nome) está em um dos idiomas aceitos.

    Args:
        input_data (Dict[str, Any]): O JSON de entrada com a estrutura 'institutions_data'.
        accepted_languages (List[str]): Uma lista de códigos de idioma (ex: ['pt', 'en']) a serem aceitos.

    Returns:
        Dict[str, Any]: Um novo objeto JSON com os repositórios filtrados.
    """
    
    if 'institutions_data' not in input_data:
        print("Erro: A chave 'institutions_data' não foi encontrada no JSON de entrada.")
        return {}

    filtered_institutions = []
    total_repos_processed = 0
    total_repos_kept = 0
    
    # Itera sobre cada instituição no JSON
    for institution in input_data['institutions_data']:
        new_repos = []
        # Itera sobre cada repositório da instituição
        for repo in institution.get('Repositorios', []):
            total_repos_processed += 1
            
            # Pega a descrição e o nome do repositório
            description = repo.get('Descricao')
            repo_name = repo.get('Nome do Repositório')
            
            # Flag para verificar se o repositório deve ser mantido
            keep_repo = False
            
            # Tenta detectar o idioma da descrição primeiro
            if description and description != 'Sem descrição':
                try:
                    lang = detect(description)
                    if lang in accepted_languages:
                        keep_repo = True
                except LangDetectException:
                    pass # Se a detecção falhar na descrição, continua para o próximo campo

            # Se a descrição não foi aceita, tenta detectar o idioma do nome
            if not keep_repo and repo_name:
                try:
                    lang = detect(repo_name)
                    if lang in accepted_languages:
                        keep_repo = True
                except LangDetectException:
                    pass # Se a detecção falhar em ambos, o repositório será ignorado

            # Adiciona o repositório se pelo menos um dos campos foi validado
            if keep_repo:
                new_repos.append(repo)
                total_repos_kept += 1

        # Adiciona a instituição apenas se ela tiver repositórios após a filtragem
        if new_repos:
            filtered_institution = institution.copy()
            filtered_institution['Repositorios'] = new_repos
            filtered_institutions.append(filtered_institution)

    # Cria a nova estrutura JSON com a lista de instituições filtradas e as descrições dos clusters
    output_json_structure = {
        "institutions_data": filtered_institutions,
        "cluster_descriptions": input_data.get('cluster_descriptions', [])
    }
    
    print(f"Processamento concluído. {total_repos_kept} de {total_repos_processed} repositórios mantidos.")
    return output_json_structure

if __name__ == "__main__":
    # Nomes dos arquivos
    input_json_file = 'repositorios_filtrados.json'
    output_json_file = 'repositorios_federais_filtrado_idioma.json'
    
    # Lista de idiomas aceitos: 'pt' para Português, 'en' para Inglês.
    # Você pode personalizar esta lista conforme a necessidade.
    ACCEPTED_LANGUAGES = ['pt']

    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Chama a função para iniciar o processo de filtragem
        filtered_data = filter_repos_by_language(data, ACCEPTED_LANGUAGES)
        
        # Salva o resultado em um novo arquivo JSON
        if filtered_data:
            with open(output_json_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False)
            print(f"O novo arquivo JSON foi salvo como '{output_json_file}'")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_json_file}' não foi encontrado.")
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{input_json_file}' não é um JSON válido.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
