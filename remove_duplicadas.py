import json

def remover_duplicatas_repositorios(caminho_arquivo_entrada, caminho_arquivo_saida):
    try:
        with open(caminho_arquivo_entrada, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        for instituicao_data in dados.get('institutions_data', []):
            repositorios = instituicao_data.get('Repositorios', [])
            repositorios_unicos = []
            vistos = set() # Usar um conjunto para armazenar tuplas (nome, link)

            for repo in repositorios:
                nome_repo = repo.get('Nome do Repositório')
                link_acesso = repo.get('Link de Acesso')

                # Criar uma chave única para identificar o repositório
                chave_repo = (nome_repo, link_acesso)

                if chave_repo not in vistos:
                    repositorios_unicos.append(repo)
                    vistos.add(chave_repo)
            
            instituicao_data['Repositorios'] = repositorios_unicos

        with open(caminho_arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False) # ensure_ascii=False para manter unicode
        
        print(f"Duplicatas removidas e arquivo salvo em: {caminho_arquivo_saida}")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo_entrada}' não foi encontrado.")
    except json.JSONDecodeError:
        print(f"Erro: Não foi possível decodificar o arquivo JSON '{caminho_arquivo_entrada}'. Verifique a formatação.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# Exemplo de uso:
# substitua 'repositorios_federais_com_clusters_visualizado.json' pelo nome do seu arquivo de entrada
# e 'repositorios_sem_duplicatas.json' pelo nome do arquivo de saída desejado.
remover_duplicatas_repositorios('repositorios_federais_com_clusters_visualizado.json', 'repositorios_sem_duplicatas.json')