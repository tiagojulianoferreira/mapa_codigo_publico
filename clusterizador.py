import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import re
import nltk
from nltk.corpus import stopwords
import os

# --- O código de preprocess_text e stopwords PERSONALIZADAS é o mesmo que antes ---
try:
    stopwords.words('portuguese')
    stopwords.words('english')
except LookupError:
    print("Baixando NLTK stopwords...")
    nltk.download('stopwords')
    nltk.download('punkt')

custom_stopwords = [
    'projeto', 'disciplina', 'desenvolvimento', 'sistema', 'sistemas',
    'computação', 'ciência', 'federal', 'universidade', 'trabalho',
    'dados', 'estrutura', 'web', 'aplicação', 'implementação', 'gestão',
    'curso', 'repositório', 'ufam', 'tcc', 'site', 'código', 'api', 'app',
    'base', 'uso', 'para', 'com', 'um', 'uma', 'este', 'esta', 'disponibiliza',
    'Toad_-3-Blooket', 'IFRS 9','l10n_tw_standard_ifrss', 'unbound', '.config',
    'durante','FBA port to iOS'
]
portuguese_stopwords = set(stopwords.words('portuguese'))
english_stopwords = set(stopwords.words('english'))
all_stopwords = portuguese_stopwords.union(english_stopwords).union(set(custom_stopwords))

def preprocess_text(text):
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    words = text.split()
    filtered_words = [word for word in words if word not in all_stopwords]
    return ' '.join(filtered_words)

# --- Fim do código de preprocess_text ---


def cluster_and_visualize_repositories(input_file, output_file, num_clusters=15):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f) # Carrega o dicionário completo
    except FileNotFoundError:
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        return
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{input_file}' não é um JSON válido.")
        return

    # AQUI ESTÁ A CORREÇÃO: Acesse a lista de instituições corretamente
    institutions_data_list = full_data.get('institutions_data', [])
    if not institutions_data_list:
        print(f"Aviso: Não foram encontradas informações de instituições na chave 'institutions_data' em '{input_file}'.")
        return

    all_repos_list = []
    
    # Itere sobre a lista de dicionários de instituições
    for institution in institutions_data_list: # <-- LINHA CORRIGIDA
        # Use .get() para acessar 'Repositorios' com segurança
        for repo in institution.get('Repositorios', []):
            combined_text = f"{repo.get('Nome do Repositório', '')} {repo.get('Descricao', '')}"
            processed_text = preprocess_text(combined_text)
            
            all_repos_list.append({
                'Nome do Repositório': repo.get('Nome do Repositório', 'N/A'),
                'Descricao': repo.get('Descricao', 'N/A'),
                'Linguagem Principal': repo.get('Linguagem Principal', 'N/A'),
                'Estrelas': repo.get('Estrelas', 0),
                'Link de Acesso': repo.get('Link de Acesso', '#'),
                'Instituicao': institution.get('Sigla', 'N/A'), # Use .get() para 'Sigla' também
                'processed_text': processed_text,
                'original_repo_obj': repo # Manter referência para atualizar depois
            })

    if not all_repos_list:
        print("Nenhum repositório encontrado para clusterizar.")
        return

    df = pd.DataFrame(all_repos_list)
    texts = df['processed_text'].tolist()

    vectorizer = TfidfVectorizer(min_df=2, max_df=0.85, ngram_range=(1,3))
    X = vectorizer.fit_transform(texts)

    # Verifica se há clusters suficientes para o número de repositórios
    if X.shape[0] < num_clusters:
        print(f"Aviso: O número de repositórios ({X.shape[0]}) é menor que o número de clusters desejado ({num_clusters}). Ajustando num_clusters para {X.shape[0]}.")
        num_clusters = X.shape[0]
        if num_clusters == 0:
            print("Nenhum repositório para clusterizar após o pré-processamento.")
            return

    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
    cluster_labels = kmeans.fit_predict(X)
    df['Cluster_ID'] = cluster_labels

    # Atualiza o 'original_repo_obj' com o Cluster_ID
    # Isso modifica diretamente a estrutura 'data' (que é a lista de instituições original)
    for i, row in df.iterrows():
        row['original_repo_obj']['Cluster_ID'] = int(row['Cluster_ID'])

    print("\nTermos Mais Representativos por Cluster:")
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()
    
    # --- NOVO: Coletar as descrições dos clusters para o JSON ---
    generated_cluster_descriptions = []
    for i in range(num_clusters):
        cluster_terms = [terms[ind] for ind in order_centroids[i, :5]]
        description_text = f"Cluster {i}: {', '.join(cluster_terms)}"
        print(description_text) # Ainda imprime para saída no console
        generated_cluster_descriptions.append({"id": i, "description": description_text})
    
    # --- FINAL: Salvar os dados atualizados em um novo arquivo JSON (NOVO FORMATO) ---
    final_output_data = {
        "institutions_data": full_data.get('institutions_data', []), # 'full_data' já foi atualizada com os Cluster_IDs nos repositórios
        "cluster_descriptions": generated_cluster_descriptions # A nova lista de descrições
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output_data, f, indent=2, ensure_ascii=False)
        print(f"\nProcessamento concluído. Repositórios e descrições de clusters salvos em '{output_file}' no novo formato.")
    except IOError as e:
        print(f"Erro ao escrever o arquivo '{output_file}': {e}")


# --- Configurações para rodar ---
# O arquivo de entrada deve ser o JSON original que você tinha,
# ANTES de adicionar Cluster_ID (ou seja, o repositorios_federais.json)
input_json_file = 'repositorios_federais_filtrado_idioma.json' # <-- VERIFIQUE ESTE NOME DE ARQUIVO
output_json_file = 'repositorios_federais_com_clusters_visualizado.json'
N_CLUSTERS = 15 # Ajuste conforme sua análise

# Chama a função para clusterizar e visualizar
cluster_and_visualize_repositories(input_json_file, output_json_file, 
                                   num_clusters=N_CLUSTERS)
