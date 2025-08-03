import pandas as pd
import json
from typing import Dict, List, Any

def gerar_palavras_chave_instituicoes(
    input_files: List[str],
    output_file: str
) -> None:
    """
    Lê uma lista de arquivos CSV, combina-os e gera um arquivo JSON de
    palavras-chave mais abrangente.

    As palavras-chave são a sigla, o nome completo e termos chave extraídos
    do nome (ex: "Universidade Federal", "Campus").
    """
    all_institutions_data = []

    print("Lendo arquivos CSV de instituições...")
    for file in input_files:
        try:
            df = pd.read_csv(file)
            all_institutions_data.append(df)
            print(f"Arquivo '{file}' lido com sucesso.")
        except FileNotFoundError:
            print(f"Erro: O arquivo '{file}' não foi encontrado. Ignorando.")
        except pd.errors.ParserError as e:
            print(f"Erro ao ler o arquivo CSV '{file}': {e}. Ignorando.")

    if not all_institutions_data:
        print("Nenhum arquivo CSV válido foi encontrado. Processo abortado.")
        return

    combined_df = pd.concat(all_institutions_data, ignore_index=True)
    combined_df.drop_duplicates(subset=['Sigla'], inplace=True)
    
    institutions_keywords: List[Dict[str, Any]] = []

    print("Gerando lista de palavras-chave com termos mais amplos...")
    for index, row in combined_df.iterrows():
        sigla = row.get('Sigla')
        nome_completo = row.get('Nome Completo')
        tipo = row.get('Tipo')
        
        keywords_list = []
        
        # Adiciona a sigla e o nome completo como palavras-chave
        if pd.notna(sigla):
            keywords_list.append(str(sigla))
        if pd.notna(nome_completo):
            keywords_list.append(str(nome_completo))
            
            # Divide o nome completo em palavras para extrair termos chave
            words = str(nome_completo).split()
            
            # Adiciona termos genéricos de tipo de instituição
            if 'Universidade' in words and 'Federal' in words:
                keywords_list.append('Universidade Federal')
            if 'Instituto' in words and 'Federal' in words:
                keywords_list.append('Instituto Federal')
            if 'Campus' in words:
                keywords_list.append('Campus')
                
            # Extrai o nome da cidade ou localização
            # Ex: "Universidade Federal de Minas Gerais" -> "Minas Gerais"
            # Ex: "Instituto Federal da Bahia" -> "Bahia"
            # Esta lógica agora é mais robusta e menos propensa a erros
            if len(words) > 2:
                # Procura por preposições como 'de', 'do', 'da'
                prep_indices = [i for i, word in enumerate(words) if word.lower() in ['de', 'do', 'da', 'e']]
                if prep_indices:
                    # Pega a parte do nome após a última preposição
                    location_name = ' '.join(words[prep_indices[-1] + 1:])
                    # Garante que não está adicionando apenas palavras genéricas como "Brasil"
                    if location_name.lower() not in ['brasil', 'amazonia', 'sul']:
                         keywords_list.append(location_name)
                # Caso não haja preposição, pega as últimas palavras que não sejam genéricas
                else:
                    last_word = words[-1]
                    if last_word.lower() not in ['federal', 'instituto', 'escola', 'faculdade', 'universidade', 'campus']:
                        keywords_list.append(last_word)


        if keywords_list:
            institutions_keywords.append({
                "Sigla": sigla,
                "Nome Completo": nome_completo,
                "Palavras_Chave": sorted(list(set(keywords_list))) # Remove duplicatas e ordena
            })

    try:
        output_data = {"institutions_keywords": institutions_keywords}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\nLista de palavras-chave gerada com sucesso e salva em '{output_file}'.")
        print(f"Total de {len(institutions_keywords)} instituições processadas.")
    except IOError as e:
        print(f"Erro ao escrever o arquivo '{output_file}': {e}")


if __name__ == '__main__':
    csv_files = ['dados/institutos_federais.csv', 'dados/universidades_federais.csv']
    output_json_file = 'palavras_chave_instituicoes_v2.json' # Novo nome para o arquivo de saída
    gerar_palavras_chave_instituicoes(csv_files, output_json_file)
