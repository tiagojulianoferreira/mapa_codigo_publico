import json
from langdetect import detect, DetectorFactory, LangDetectException
import re
from typing import List, Dict, Any

# Garante que a detecção de idioma seja determinística para o mesmo texto.
DetectorFactory.seed = 0

def filter_repos_by_description_language(input_data: Dict[str, Any], accepted_languages: List[str]) -> Dict[str, Any]:
    """
    Filtra repositórios por idioma da descrição, mantendo apenas aqueles com
    descrições em um dos idiomas aceitos.

    Args:
        input_data (Dict[str, Any]): O JSON de entrada com a estrutura 'institutions_data' e 'cluster_descriptions'.
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
    
    for institution in input_data['institutions_data']:
        new_repos = []
        for repo in institution.get('Repositorios', []):
            total_repos_processed += 1
            description = repo.get('Descricao')
            
            # Pular se não houver descrição para detectar
            if not description or description == 'Sem descrição':
                continue

            # Limpar a descrição para uma detecção mais precisa
            cleaned_description = re.sub(r'https?://\S+|www\.\S+', '', description, flags=re.MULTILINE)
            cleaned_description = re.sub(r'[@#]\w+', '', cleaned_description)
            
            try:
                detected_lang = detect(cleaned_description)
                if detected_lang in accepted_languages:
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

    # Cria a nova estrutura JSON com a lista de instituições filtradas e os clusters.
    output_json_structure = {
        "institutions_data": filtered_institutions,
        "cluster_descriptions": input_data.get('cluster_descriptions', []) # Mantém as descrições dos clusters
    }

    print(f"Processamento concluído. {total_repos_kept} de {total_repos_processed} repositórios mantidos.")
    return output_json_structure

if __name__ == "__main__":
    # Nomes dos arquivos
    input_json_file = 'repositorios_federais_desduplicados.json'
    output_json_file = 'repositorios_federais_filtrado_idioma.json'
    
    # Lista de idiomas aceitos: 'pt' para Português, 'en' para Inglês.
    # Você pode personalizar esta lista conforme a necessidade.
    ACCEPTED_LANGUAGES = ['pt','en']

    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Chama a função para iniciar o processo de filtragem
        filtered_data = filter_repos_by_description_language(data, ACCEPTED_LANGUAGES)
        
        # Salva o resultado em um novo arquivo JSON
        if filtered_data:
            with open(output_json_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False)
            print(f"O novo arquivo JSON foi salvo como '{output_json_file}'")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_json_file}' não foi encontrado.")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON: O arquivo '{input_json_file}' pode estar corrompido.")

