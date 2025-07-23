import pandas as pd
import json # Importa a biblioteca json para carregar o arquivo com mais controle

def remover_duplicatas_json_aninhado(caminho_entrada, caminho_saida, subset=None, keep='first'):
  """
  Remove linhas duplicadas de repositórios aninhados em um arquivo JSON
  e salva o resultado (repositórios únicos) em outro arquivo JSON.

  Args:
    caminho_entrada (str): Caminho do arquivo JSON de entrada com estrutura aninhada.
    caminho_saida (str): Caminho do arquivo JSON de saída para os repositórios únicos.
    subset (list, optional): Lista de nomes de colunas para considerar na
                             identificação de duplicatas de repositórios. Se None,
                             todas as colunas são usadas. Padrão para None.
    keep (str): Determina qual duplicata manter:
                - 'first': Mantém a primeira ocorrência (padrão).
                - 'last': Mantém a última ocorrência.
                - False: Remove todas as ocorrências de duplicatas.
  """
  try:
    # Carrega o JSON completo
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
      dados = json.load(f)

    # Verifica se a chave 'institutions_data' existe
    if 'institutions_data' not in dados:
      print(f"Erro: O arquivo JSON '{caminho_entrada}' não contém a chave 'institutions_data'.")
      return

    # Extrai todos os repositórios de todas as instituições para uma única lista
    todos_repositorios = []
    for institucionais_dados in dados['institutions_data']:
      if 'Repositorios' in institucionais_dados and isinstance(institucionais_dados['Repositorios'], list):
        todos_repositorios.extend(institucionais_dados['Repositorios'])

    # Cria um DataFrame a partir da lista combinada de repositórios
    df = pd.DataFrame(todos_repositorios)

    # Verifica se o DataFrame está vazio após extração
    if df.empty:
      print(f"Aviso: Não foram encontrados repositórios no arquivo '{caminho_entrada}' para processar.")
      # Pode-se optar por criar um arquivo de saída vazio ou não criar nada
      with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2) # Salva uma lista JSON vazia
      return

    # Remove linhas duplicadas com base nos parâmetros fornecidos
    df_sem_duplicatas = df.drop_duplicates(subset=subset, keep=keep)

    # Salva o DataFrame sem duplicatas em um novo arquivo JSON
    # Orient='records' é ideal para uma lista de objetos JSON (onde cada objeto é um repositório)
    df_sem_duplicatas.to_json(caminho_saida, orient='records', indent=2)

    print(f"Linhas duplicadas de repositórios removidas com sucesso. Resultado salvo em: {caminho_saida}")
    print(f"Total de repositórios originais encontrados: {len(df)}")
    print(f"Total de repositórios após remoção de duplicatas: {len(df_sem_duplicatas)}")

  except FileNotFoundError:
    print(f"Erro: Arquivo não encontrado no caminho: {caminho_entrada}")
  except json.JSONDecodeError:
    print(f"Erro: O arquivo '{caminho_entrada}' não é um JSON válido ou está malformado.")
  except Exception as e:
    print(f"Ocorreu um erro inesperado ao processar o arquivo: {e}")

# --- Exemplo de Uso com o seu JSON ---

# Nome do arquivo de entrada (o que você forneceu)
arquivo_entrada_real = 'repositorios_federais_com_clusters_visualizado1.json'
# Nome do arquivo de saída para os repositórios únicos
arquivo_saida_repositorios_unicos = 'repositorios_unicos.json'

print("--- Removendo duplicatas de repositórios (todas as colunas) ---")
remover_duplicatas_json_aninhado(
    caminho_entrada=arquivo_entrada_real,
    caminho_saida=arquivo_saida_repositorios_unicos
)

# Exemplo: Remover duplicatas considerando apenas 'Nome do Repositório' e 'Link de Acesso'
arquivo_saida_subset = 'repositorios_unicos_por_nome_link.json'
print("\n--- Removendo duplicatas de repositórios (por 'Nome do Repositório' e 'Link de Acesso') ---")
remover_duplicatas_json_aninhado(
    caminho_entrada=arquivo_entrada_real,
    caminho_saida=arquivo_saida_subset,
    subset=['Nome do Repositório', 'Link de Acesso']
)

# Exemplo: Remover todas as ocorrências de duplicatas exatas
arquivo_saida_estritamente_unicos = 'repositorios_estritamente_unicos.json'
print("\n--- Removendo TODAS as ocorrências de repositórios duplicados ---")
remover_duplicatas_json_aninhado(
    caminho_entrada=arquivo_entrada_real,
    caminho_saida=arquivo_saida_estritamente_unicos,
    keep=False
)