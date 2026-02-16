import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import re
import nltk
from nltk.corpus import stopwords
import os
from datetime import datetime

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

def clusterizar_repositorios(input_file, output_file, n_clusters=15, top_repos_por_cluster=50):
    """
    Carrega, pré-processa, clusteriza e salva os dados dos repositórios
    em um novo arquivo JSON no formato especificado.
    
    Args:
        input_file: Arquivo JSON de entrada com os dados dos repositórios
        output_file: Arquivo JSON de saída
        n_clusters: Número de clusters para o KMeans
        top_repos_por_cluster: Número de repositórios mais populares por cluster
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

    # Preparar dados para o DataFrame
    repos_df_data = []
    for institution in full_data.get('institutions_data', []):
        sigla = institution.get('Sigla')
        for repo in institution.get('Repositorios', []):
            # Pré-processa o texto para clustering
            combined_text = f"{repo.get('Nome do Repositório', '')} {repo.get('Descricao', '')}"
            processed_text = preprocess_text(combined_text)
            
            # Garantir que o campo Estrelas seja numérico
            estrelas = repo.get('Estrelas', 0)
            if estrelas is None:
                estrelas = 0
            
            repos_df_data.append({
                'text': processed_text,
                'repo_obj': repo.copy(),  # Cria uma cópia para não modificar o original
                'sigla': sigla,
                'estrelas': int(estrelas) if estrelas else 0
            })
    
    # Se não houver texto processado, encerra
    if not any(item['text'] for item in repos_df_data):
        print("Nenhum texto válido encontrado para clusterização após o pré-processamento.")
        return

    repos_df = pd.DataFrame(repos_df_data)

    # --- TF-IDF e KMeans ---
    tfidf_vectorizer = TfidfVectorizer(max_features=1000)
    tfidf_matrix = tfidf_vectorizer.fit_transform(repos_df['text'])
    
    kmeans_model = KMeans(n_clusters=n_clusters, init='k-means++', max_iter=300, n_init=10, random_state=42)
    kmeans_model.fit(tfidf_matrix)

    # Adiciona o ID do cluster ao DataFrame
    repos_df['Cluster_ID'] = kmeans_model.labels_ + 1  # +1 para começar do 1

    # Gerar descrições dos clusters
    generated_cluster_descriptions = []
    print("\n--- Descrições dos Clusters Geradas ---")
    order_centroids = kmeans_model.cluster_centers_.argsort()[:, ::-1]
    terms = tfidf_vectorizer.get_feature_names_out()
    
    cluster_desc_map = {}
    for i in range(n_clusters):
        cluster_id = i + 1
        top_terms = [terms[ind] for ind in order_centroids[i, :5]]
        description_text = f"Cluster {cluster_id}: {', '.join(top_terms)}"
        print(description_text)
        cluster_desc_map[cluster_id] = description_text
        generated_cluster_descriptions.append({"id": cluster_id, "description": description_text})

    # --- Preparar a saída no formato especificado ---
    
    # Obter a data e hora atual para data_analise
    data_analise = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Inicializar o dicionário de saída
    output_data = {
        "data_analise": data_analise
    }
    
    # Para cada cluster, selecionar os top repositórios por estrelas
    for cluster_id in range(1, n_clusters + 1):
        # Filtrar repositórios do cluster atual
        cluster_repos = repos_df[repos_df['Cluster_ID'] == cluster_id]
        
        # Ordenar por estrelas (decrescente) e pegar os top N
        top_repos = cluster_repos.nlargest(top_repos_por_cluster, 'estrelas')
        
        # Formatar os repositórios para o formato de saída
        repos_formatados = []
        for _, row in top_repos.iterrows():
            repo = row['repo_obj']
            repos_formatados.append({
                "Nome do Repositório": repo.get('Nome do Repositório', ''),
                "Descricao": repo.get('Descricao', ''),
                "Estrelas": repo.get('Estrelas', 0),
                "Linguagem Principal": repo.get('Linguagem Principal'),
                "Organizacao": repo.get('Organizacao', False),
                "Link de Acesso": repo.get('Link de Acesso', '')
            })
        
        # Adicionar ao dicionário de saída
        output_data[f"repositorios_destaque_cluster_{cluster_id}"] = repos_formatados
        
        # Imprimir estatísticas
        print(f"\nCluster {cluster_id}: {len(cluster_repos)} repositórios no total, {len(repos_formatados)} destacados")

    # Opcional: Incluir descrições dos clusters no arquivo de saída
    output_data["cluster_descriptions"] = generated_cluster_descriptions

    # --- Salvar o arquivo de saída ---
    try:
        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nProcessamento concluído. Dados salvos em '{output_file}'.")
        print(f"Total de clusters: {n_clusters}")
        print(f"Total de repositórios processados: {len(repos_df)}")
        print(f"Top {top_repos_por_cluster} repositórios por cluster incluídos")
        
    except IOError as e:
        print(f"Erro ao escrever o arquivo '{output_file}': {e}")


# --- Configurações para rodar ---
input_json_file = 'repositorios_federais_filtrado_idioma_sem_stopwords.json'
output_json_file = './dados/repositorios_federais_por_cluster.json'
N_CLUSTERS = 15  # Número de clusters
TOP_REPOS_POR_CLUSTER = 50  # Número de repositórios mais populares por cluster

# Chama a função para iniciar o processo
if __name__ == "__main__":
    clusterizar_repositorios(input_json_file, output_json_file, N_CLUSTERS, TOP_REPOS_POR_CLUSTER)