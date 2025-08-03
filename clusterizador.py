import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import re
import nltk
from nltk.corpus import stopwords
import os

# --- Configuração de Stopwords (o mesmo código anterior) ---
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
    'durante','FBA port to iOS', 'linux'
]
portuguese_stopwords = set(stopwords.words('portuguese'))
english_stopwords = set(stopwords.words('english'))
all_stopwords = portuguese_stopwords.union(english_stopwords).union(set(custom_stopwords))

def preprocess_text(text):
    """Função para pré-processar o texto de nome e descrição."""
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text) # Remove URLs
    text = re.sub(r'<.*?>', '', text) # Remove tags HTML
    text = re.sub(r'[^a-z0-9\s]', '', text) # Remove caracteres especiais
    text = ' '.join([word for word in text.split() if word not in all_stopwords and len(word) > 2])
    return text

def clusterizar_repositorios(input_file, output_file, n_clusters=15):
    """
    Carrega, pré-processa, clusteriza e salva os dados dos repositórios
    em um novo arquivo JSON, incluindo as descrições dos clusters.
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

    all_repos = []
    for institution in full_data.get('institutions_data', []):
        for repo in institution.get('Repositorios', []):
            all_repos.append(repo)

    if not all_repos:
        print("Não há repositórios para clusterizar. Verifique o arquivo de entrada.")
        return

    # Preparar dados para o DataFrame (incluindo nome da instituição para referência)
    repos_df_data = []
    for institution in full_data.get('institutions_data', []):
        sigla = institution.get('Sigla')
        for repo in institution.get('Repositorios', []):
            # Pré-processa o texto para clustering
            combined_text = f"{repo.get('Nome do Repositório', '')} {repo.get('Descricao', '')}"
            processed_text = preprocess_text(combined_text)
            repos_df_data.append({
                'text': processed_text,
                'repo_obj': repo,  # Armazena o objeto original do repositório
                'sigla': sigla
            })
    
    # Se não houver texto processado, encerra
    if not any(item['text'] for item in repos_df_data):
        print("Nenhum texto válido encontrado para clusterização após o pré-processamento.")
        return

    repos_df = pd.DataFrame(repos_df_data)

    # --- TF-IDF e KMeans (o mesmo código anterior) ---
    tfidf_vectorizer = TfidfVectorizer(max_features=1000)
    tfidf_matrix = tfidf_vectorizer.fit_transform(repos_df['text'])
    
    kmeans_model = KMeans(n_clusters=n_clusters, init='k-means++', max_iter=300, n_init=10, random_state=42)
    kmeans_model.fit(tfidf_matrix)

    # Adiciona o ID do cluster ao DataFrame
    repos_df['Cluster_ID'] = kmeans_model.labels_ + 1 # +1 para começar do 1
    
    # Adiciona o ID do cluster de volta ao objeto do repositório original
    for index, row in repos_df.iterrows():
        repo_obj = row['repo_obj']
        repo_obj['Cluster_ID'] = row['Cluster_ID']
    
    # Reorganiza o JSON completo com os novos Cluster_IDs
    # O loop acima já atualizou os objetos 'repo_obj' que estavam no 'full_data',
    # então 'full_data' já contém os 'Cluster_ID's.

    # Gerar descrições dos clusters
    generated_cluster_descriptions = []
    print("\n--- Descrições dos Clusters Geradas ---")
    order_centroids = kmeans_model.cluster_centers_.argsort()[:, ::-1]
    terms = tfidf_vectorizer.get_feature_names_out()
    
    for i in range(n_clusters):
        top_terms = [terms[ind] for ind in order_centroids[i, :5]]
        description_text = f"Cluster {i+1}: {', '.join(top_terms)}"
        print(description_text)
        generated_cluster_descriptions.append({"id": i + 1, "description": description_text})

    # --- FINAL: Salvar os dados atualizados em um novo arquivo JSON ---
    final_output_data = {
        "institutions_data": full_data.get('institutions_data', []),
        "cluster_descriptions": generated_cluster_descriptions
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output_data, f, indent=2, ensure_ascii=False)
        print(f"\nProcessamento concluído. Repositórios com Cluster_ID e descrições de clusters salvos em '{output_file}'.")
    except IOError as e:
        print(f"Erro ao escrever o arquivo '{output_file}': {e}")


# --- Configurações para rodar ---
# O arquivo de entrada deve ser o JSON que contém a estrutura completa,
# incluindo os dados de organização. 'repositorios_federais_desduplicados.json' é um bom exemplo.
input_json_file = 'repositorios_filtrados.json' 
output_json_file = 'repositorios_federais_com_clusters_visualizado.json'
N_CLUSTERS = 15 # Ajuste conforme sua análise

# Chama a função para iniciar o processo
if __name__ == "__main__":
    clusterizar_repositorios(input_json_file, output_json_file, N_CLUSTERS)
