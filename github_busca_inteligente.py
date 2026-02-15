import pandas as pd
import requests
import json
import time
from dotenv import load_dotenv
import os
import re
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
import logging
from collections import Counter, defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords

# === Configuração ===
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BuscaInteligenteGitHub:
    def __init__(self):
        self.token = GITHUB_TOKEN
        self.headers = HEADERS
        self.cache_queries = {}  # Cache para evitar buscas repetidas
        self.metricas_queries = defaultdict(lambda: {"sucessos": 0, "falhas": 0, "total_repos": 0})
        self.timestamp_consulta = datetime.now().isoformat()
        
        # Download NLTK resources
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        self.stopwords_pt = set(stopwords.words('portuguese'))
        self.stopwords_en = set(stopwords.words('english'))
    
    # ==================================================
    # 1. ANÁLISE DE RELEVÂNCIA DAS PALAVRAS-CHAVE
    # ==================================================
    
    def calcular_relevancia_palavras(self, repositorios: List[Dict]) -> Dict[str, float]:
        """
        Calcula a relevância de cada palavra-chave usando TF-IDF
        VERSÃO CORRIGIDA - Trata campos None
        """
        # Prepara os textos para análise
        textos = []
        for repo in repositorios:
            # Tratamento seguro para campos None
            nome = repo.get('Nome do Repositório', '')
            nome_str = str(nome) if nome is not None else ""
            
            desc = repo.get('Descricao', '')
            desc_str = str(desc) if desc is not None else ""
            
            texto = f"{nome_str} {desc_str}"
            textos.append(texto.lower())
        
        if not textos:
            return {}
        
        # Calcula TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words=list(self.stopwords_pt.union(self.stopwords_en)),
            ngram_range=(1, 2)  # Inclui bigramas
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(textos)
            feature_names = vectorizer.get_feature_names_out()
            scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
            
            # Cria dicionário de palavras com seus scores
            relevancia = dict(zip(feature_names, scores))
            
            # Ordena por relevância
            relevancia = dict(sorted(relevancia.items(), key=lambda x: x[1], reverse=True))
            
            return relevancia
            
        except Exception as e:
            logger.error(f"Erro no cálculo TF-IDF: {e}")
            return {}
    
    def extrair_palavras_chave_inteligentes(self, repositorios: List[Dict], top_n: int = 20) -> List[str]:
        """
        Extrai palavras-chave inteligentes usando múltiplas estratégias
        VERSÃO CORRIGIDA - Trata campos None
        """
        # Estratégia 1: TF-IDF
        relevancia_tfidf = self.calcular_relevancia_palavras(repositorios)
        
        # Estratégia 2: Frequência simples
        contador = Counter()
        for repo in repositorios:
            # Tratamento seguro para nome
            nome = repo.get('Nome do Repositório')
            nome_str = str(nome).lower() if nome is not None else ""
            
            # Tratamento seguro para descrição
            desc = repo.get('Descricao')
            desc_str = str(desc).lower() if desc is not None else ""
            
            # Extrai palavras significativas
            palavras = re.findall(r'\b[a-z]{4,}\b', f"{nome_str} {desc_str}")
            contador.update(palavras)
        
        # Estratégia 3: Tecnologias (Topics)
        tecnologias = Counter()
        for repo in repositorios:
            topics = repo.get('Topics', [])
            if topics and isinstance(topics, list):
                for topic in topics:
                    if topic and isinstance(topic, str):
                        tecnologias[topic.lower()] += 1
        
        # Combina as estratégias com pesos
        palavras_com_peso = defaultdict(float)
        
        # Peso 0.5 para TF-IDF
        for palavra, score in list(relevancia_tfidf.items())[:30]:
            palavras_com_peso[palavra] += score * 0.5
        
        # Peso 0.3 para frequência
        for palavra, freq in contador.most_common(30):
            if len(repositorios) > 0:
                palavras_com_peso[palavra] += (freq / len(repositorios)) * 0.3
        
        # Peso 0.2 para tecnologias
        for palavra, freq in tecnologias.most_common(20):
            if len(repositorios) > 0:
                palavras_com_peso[palavra] += (freq / len(repositorios)) * 0.2
        
        # Ordena por peso e retorna as top N
        palavras_ordenadas = sorted(palavras_com_peso.items(), key=lambda x: x[1], reverse=True)
        
        return [p for p, _ in palavras_ordenadas[:top_n]]
    
    # ==================================================
    # 2. OTIMIZAÇÃO DE QUERIES BASEADA EM MÉTRICAS
    # ==================================================
    
    def calcular_eficiencia_query(self, query: str, resultados: List[Dict]) -> float:
        """
        Calcula a eficiência de uma query baseado nos resultados
        VERSÃO CORRIGIDA - Trata campos None
        """
        if not resultados:
            return 0.0
        
        total_resultados = len(resultados)
        relevantes = 0
        
        for repo in resultados[:10]:
            # Tratamento seguro para description (pode ser None)
            desc = repo.get('description')
            if desc is None:
                desc_lower = ""
            else:
                desc_lower = str(desc).lower()
            
            # Tratamento seguro para name (pode ser None)
            name = repo.get('name')
            if name is None:
                name_lower = ""
            else:
                name_lower = str(name).lower()
            
            # Verifica se o repositório menciona termos da query
            termos_query = query.lower().split()
            if any(termo in desc_lower or termo in name_lower for termo in termos_query):
                relevantes += 1
        
        taxa_relevancia = relevantes / min(10, len(resultados)) if resultados else 0
        pontuacao = (min(total_resultados, 100) / 100) * 0.3 + taxa_relevancia * 0.7
        
        return pontuacao
    
    def otimizar_queries_com_base_em_metricas(self, queries_anteriores: List[str], 
                                               resultados_anteriores: Dict[str, List]) -> List[str]:
        """
        Otimiza as queries baseado no desempenho histórico
        """
        # Calcula eficiência de cada query anterior
        eficiencia_queries = {}
        for query in queries_anteriores:
            resultados = resultados_anteriores.get(query, [])
            eficiencia = self.calcular_eficiencia_query(query, resultados)
            eficiencia_queries[query] = eficiencia
            self.metricas_queries[query]["total_repos"] += len(resultados)
            
            if eficiencia > 0.5:
                self.metricas_queries[query]["sucessos"] += 1
            else:
                self.metricas_queries[query]["falhas"] += 1
        
        # Identifica padrões em queries bem-sucedidas
        queries_sucesso = [q for q, e in eficiencia_queries.items() if e > 0.5]
        
        # Extrai padrões comuns
        padroes = Counter()
        for query in queries_sucesso:
            termos = query.split()
            for termo in termos:
                if len(termo) > 3:
                    padroes[termo] += 1
        
        # Gera novas queries baseadas nos padrões
        novas_queries = []
        termos_promissores = [t for t, _ in padroes.most_common(5)]
        
        # Combina termos promissores
        from itertools import combinations
        for termo1, termo2 in combinations(termos_promissores, 2):
            nova_query = f'"{termo1} {termo2}"'
            if nova_query not in queries_anteriores:
                novas_queries.append(nova_query)
        
        return novas_queries[:5]  # Retorna até 5 novas queries
    
    # ==================================================
    # 3. BUSCA INTELIGENTE COM FEEDBACK LOOP
    # ==================================================
    
    def buscar_com_feedback_loop(self, sigla: str, nome: str, campus: str = None, 
                                  iteracoes: int = 3) -> List[Dict]:
        """
        Busca repositórios com feedback loop para otimizar as consultas
        """
        todos_repos = []
        queries_utilizadas = []
        resultados_por_query = {}
        
        # Gera queries iniciais
        queries_iniciais = self.gerar_queries_iniciais(sigla, nome, campus)
        
        for iteracao in range(iteracoes):
            logger.info(f"\n🔄 Iteração {iteracao + 1}/{iteracoes} para {sigla}")
            
            # Define queries desta iteração
            if iteracao == 0:
                queries_atual = queries_iniciais
            else:
                queries_atual = self.otimizar_queries_com_base_em_metricas(
                    queries_utilizadas, resultados_por_query
                )
            
            if not queries_atual:
                logger.info("  ⚠️ Sem novas queries para testar")
                break
            
            for query in queries_atual:
                if query in queries_utilizadas:
                    continue
                    
                logger.info(f"  🔎 Testando: {query}")
                
                # Executa busca
                resultados = self.executar_busca_com_paginacao(query)
                
                # Armazena métricas
                queries_utilizadas.append(query)
                resultados_por_query[query] = resultados
                
                # Adiciona aos resultados totais
                todos_repos.extend(resultados)
                
                # Mostra estatísticas
                eficiencia = self.calcular_eficiencia_query(query, resultados)
                logger.info(f"     ✅ {len(resultados)} resultados (eficiência: {eficiencia:.2f})")
                
                time.sleep(1)
            
            # Pausa entre iterações
            if iteracao < iteracoes - 1:
                time.sleep(2)
        
        # Remove duplicatas
        repos_unicos = {repo['id']: repo for repo in todos_repos}.values()
        
        # Log de métricas finais
        logger.info(f"\n📊 Métricas finais para {sigla}:")
        logger.info(f"   Total de queries testadas: {len(queries_utilizadas)}")
        
        queries_sucesso = [q for q in queries_utilizadas 
                          if self.metricas_queries[q]["sucessos"] > 0]
        logger.info(f"   Queries com sucesso: {len(queries_sucesso)}")
        
        return list(repos_unicos)
    
    def executar_busca_com_paginacao(self, query: str, max_paginas: int = 5) -> List[Dict]:
        """
        Executa busca com paginação
        """
        todos_repos = []
        page = 1
        per_page = 100
        
        while page <= max_paginas:
            url = "https://api.github.com/search/repositories"
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': per_page,
                'page': page
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 403 and 'rate limit' in response.text.lower():
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    wait_time = max(reset_time - time.time(), 0) + 5
                    logger.warning(f"      ⏳ Rate limit. Aguardando {wait_time:.0f}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                if not items:
                    break
                
                todos_repos.extend(items)
                
                if len(items) < per_page:
                    break
                
                page += 1
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"      ❌ Erro: {e}")
                break
        
        return todos_repos
    
    def gerar_queries_iniciais(self, sigla: str, nome: str, campus: str = None) -> List[str]:
        """
        Gera queries iniciais baseadas em padrões comuns
        """
        queries = []
        sigla_lower = sigla.lower()
        
        # Queries básicas
        queries.append(f'"{sigla_lower}"')
        
        if campus:
            campus_clean = re.sub(r"[^a-z0-9]", "", campus.lower())
            queries.extend([
                f'"{sigla_lower} {campus_clean}"',
                f'"{sigla_lower}-{campus_clean}"',
                f'"{sigla_lower}/{campus_clean}"'
            ])
        
        # Queries com nome completo
        nome_parts = nome.lower().split()
        if len(nome_parts) > 2:
            queries.append(f'"{nome_parts[0]} {nome_parts[1]}"')
        
        return list(set(queries))  # Remove duplicatas
    
    # ==================================================
    # 4. PROCESSAMENTO PRINCIPAL
    # ==================================================
    
    def processar_instituicoes_com_inteligencia(self, df: pd.DataFrame) -> Dict:
        """
        Processa todas as instituições usando busca inteligente
        """
        resultado_final = {"institutions_data": []}
        todas_keywords = {}
        
        for idx, row in df.iterrows():
            sigla = row["Sigla"]
            nome = row["Nome Completo"]
            url = row["URL Oficial"]
            campus = row.get("Campus", None)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🏛️  Processando {sigla} - {nome}")
            logger.info(f"{'='*60}")
            
            # PASSO 1: Busca inicial com feedback loop
            repos_encontrados = self.buscar_com_feedback_loop(sigla, nome, campus)
            
            if not repos_encontrados:
                logger.warning(f"⚠️ Nenhum repositório encontrado para {sigla}")
                continue
            
            # PASSO 2: Extrai detalhes dos repositórios
            repos_detalhados = []
            for repo in repos_encontrados:
                detalhes = self.extrair_detalhes_repo(repo)
                repos_detalhados.append(detalhes)
            
            # PASSO 3: Gera palavras-chave inteligentes
            palavras_relevantes = self.extrair_palavras_chave_inteligentes(repos_detalhados)
            
            # Adiciona sigla e termos básicos
            palavras_finais = list(set([sigla.lower()] + palavras_relevantes[:15]))
            todas_keywords[sigla] = palavras_finais
            
            logger.info(f"✅ {sigla}: {len(repos_detalhados)} repositórios")
            logger.info(f"   Palavras-chave: {', '.join(palavras_finais[:10])}")
            
            resultado_final["institutions_data"].append({
                "Sigla": sigla,
                "Nome Completo": nome,
                "URL Oficial": url,
                "Repositorios": repos_detalhados
            })
            
            # Pausa entre instituições
            if idx < len(df) - 1:
                time.sleep(3)
        
        # Salva palavras-chave geradas com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f"palavras_chave_inteligentes_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump({
                "timestamp_consulta": self.timestamp_consulta,
                "institutions_keywords": [
                    {"Sigla": k, "Palavras_Chave": v} for k, v in todas_keywords.items()
                ]
            }, f, indent=2, ensure_ascii=False)
        
        return resultado_final
    
    def extrair_detalhes_repo(self, repo: Dict) -> Dict:
        """
        Extrai detalhes do repositório no formato esperado
        VERSÃO CORRIGIDA - Trata campos None
        """
        owner = repo.get('owner', {})
        is_org = owner.get('type') == 'Organization' if owner else False
        
        # Tratamento seguro para licença
        license_info = repo.get('license')
        if license_info and isinstance(license_info, dict):
            license_name = license_info.get('spdx_id', 'N/A')
        else:
            license_name = 'N/A'
        
        # Tratamento seguro para description
        description = repo.get('description')
        if description is None:
            description = 'N/A'
        
        # Tratamento seguro para name
        name = repo.get('name')
        if name is None:
            name = 'N/A'
        
        # Tratamento seguro para language
        language = repo.get('language')
        if language is None:
            language = 'N/A'
        
        # Tratamento seguro para updated_at
        updated_at = repo.get('updated_at')
        if updated_at is None:
            updated_at = 'N/A'
        
        # Tratamento seguro para html_url
        html_url = repo.get('html_url')
        if html_url is None:
            html_url = 'N/A'
        
        # Tratamento seguro para created_at
        created_at = repo.get('created_at')
        if created_at is None:
            created_at = 'N/A'
        
        # Tratamento seguro para topics
        topics = repo.get('topics', [])
        if not isinstance(topics, list):
            topics = []
        
        return {
            'Nome do Repositório': name,
            'Descricao': description,
            'Linguagem Principal': language,
            'Estrelas': repo.get('stargazers_count', 0),
            'Licenca': license_name,
            'Ultima Atualizacao': updated_at,
            'Link de Acesso': html_url,
            'Organizacao': is_org,
            'Forks': repo.get('forks_count', 0),
            'Topics': topics,
            'Data_Criacao': created_at
        }

# ==================================================
# EXECUÇÃO PRINCIPAL
# ==================================================

def main():
    logger.info("=" * 70)
    logger.info("🚀 INICIANDO BUSCA INTELIGENTE COM FEEDBACK LOOP")
    logger.info("=" * 70)
    
    timestamp_geral = datetime.now()
    timestamp_str = timestamp_geral.strftime("%Y%m%d_%H%M%S")
    
    # Carrega dados
    try:
        df_if = pd.read_csv("dados/institutos_federais.csv")
        df_uf = pd.read_csv("dados/universidades_federais.csv")
        
        # Tenta carregar CEFET se existir
        try:
            df_cefet = pd.read_csv("dados/cefet.csv")
        except:
            df_cefet = pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return
    
    # Inicializa o buscador inteligente
    buscador = BuscaInteligenteGitHub()
    
    # Processa instituições
    todos_dados = []
    
    if not df_if.empty:
        logger.info("\n📚 Processando Institutos Federais...")
        resultado_if = buscador.processar_instituicoes_com_inteligencia(df_if)
        todos_dados.extend(resultado_if["institutions_data"])
    
    if not df_uf.empty:
        logger.info("\n📚 Processando Universidades Federais...")
        resultado_uf = buscador.processar_instituicoes_com_inteligencia(df_uf)
        todos_dados.extend(resultado_uf["institutions_data"])
    
    if not df_cefet.empty:
        logger.info("\n📚 Processando CEFETs...")
        resultado_cefet = buscador.processar_instituicoes_com_inteligencia(df_cefet)
        todos_dados.extend(resultado_cefet["institutions_data"])
    
    # Desduplicação global
    logger.info("\n🔄 Realizando desduplicação global...")
    seen = set()
    for inst in todos_dados:
        novos_repos = []
        for repo in inst["Repositorios"]:
            chave = (repo["Nome do Repositório"], repo["Link de Acesso"])
            if chave not in seen:
                novos_repos.append(repo)
                seen.add(chave)
        inst["Repositorios"] = novos_repos
    
    # Cria estrutura final com timestamp e metadados
    saida = {
        "metadata": {
            "timestamp_consulta": timestamp_geral.isoformat(),
            "data_consulta": timestamp_geral.strftime("%Y-%m-%d"),
            "hora_consulta": timestamp_geral.strftime("%H:%M:%S"),
            "versao_script": "2.0.0",
            "total_instituicoes": len(todos_dados),
            "total_repositorios": sum(len(inst["Repositorios"]) for inst in todos_dados)
        },
        "institutions_data": todos_dados
    }
    
    # Salva arquivo principal para o frontend (SEM METADADOS - compatível)
    with open("repositorios_federais_filtrado_idioma.json", "w", encoding="utf-8") as f:
        json.dump({"institutions_data": todos_dados}, f, indent=2, ensure_ascii=False)
    
    # Salva arquivo com timestamp para série histórica (COM METADADOS)
    arquivo_historico = f"repositorios_federais_{timestamp_str}.json"
    with open(arquivo_historico, "w", encoding="utf-8") as f:
        json.dump(saida, f, indent=2, ensure_ascii=False)
    
    # Estatísticas finais
    total_repos = sum(len(inst["Repositorios"]) for inst in todos_dados)
    total_inst = len(todos_dados)
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ PROCESSO CONCLUÍDO!")
    logger.info("=" * 70)
    logger.info(f"📁 Arquivo para frontend: repositorios_federais_filtrado_idioma.json")
    logger.info(f"📁 Arquivo para série histórica: {arquivo_historico}")
    logger.info(f"📊 Total de instituições: {total_inst}")
    logger.info(f"📊 Total de repositórios únicos: {total_repos}")
    logger.info(f"📊 Palavras-chave: palavras_chave_inteligentes_{timestamp_str}.json")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()