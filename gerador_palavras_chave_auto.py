import json
from collections import Counter
import re
from typing import List, Dict
import nltk
from nltk.corpus import stopwords
import unicodedata

# Download das stopwords em português (primeira execução)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class GeradorPalavrasChave:
    def __init__(self):
        # Stopwords em português e inglês
        self.stopwords = set(stopwords.words('portuguese') + stopwords.words('english'))
        # Adiciona stopwords customizadas
        self.stopwords.update(['github', 'git', 'projeto', 'projetos', 'código', 'codigo'])
        
    def normalizar_texto(self, texto: str) -> str:
        """Remove acentos e converte para minúsculo"""
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
        return texto.lower()
    
    def extrair_palavras_significativas(self, texto: str) -> List[str]:
        """Extrai palavras relevantes do texto"""
        if not texto or texto == 'N/A':
            return []
        
        texto_norm = self.normalizar_texto(texto)
        
        # Encontra todas as palavras com 4 ou mais caracteres
        palavras = re.findall(r'\b[a-z]{4,}\b', texto_norm)
        
        # Filtra stopwords
        palavras_filtradas = [
            p for p in palavras 
            if p not in self.stopwords and not p.isdigit()
        ]
        
        return palavras_filtradas
    
    def extrair_tecnologias(self, repo: Dict) -> List[str]:
        """Extrai tecnologias mencionadas no repositório"""
        tecnologias = []
        
        # Linguagem principal já é uma tecnologia
        if repo.get('Linguagem Principal') and repo['Linguagem Principal'] != 'N/A':
            tecnologias.append(repo['Linguagem Principal'].lower())
        
        # Topics são ótimas fontes de palavras-chave
        topics = repo.get('Topics', [])
        if topics:
            tecnologias.extend([t.lower() for t in topics])
        
        return tecnologias
    
    def gerar_palavras_chave_instituicao(self, repositorios: List[Dict]) -> List[str]:
        """
        Gera palavras-chave para uma instituição baseado em seus repositórios
        """
        contador = Counter()
        
        for repo in repositorios:
            # Coleta palavras do nome
            nome_palavras = self.extrair_palavras_significativas(repo.get('Nome do Repositório', ''))
            contador.update(nome_palavras)
            
            # Coleta palavras da descrição
            desc_palavras = self.extrair_palavras_significativas(repo.get('Descricao', ''))
            contador.update(desc_palavras)
            
            # Coleta tecnologias
            tecnologias = self.extrair_tecnologias(repo)
            contador.update(tecnologias)
        
        # Pega as 15 palavras mais comuns
        palavras_comuns = [palavra for palavra, _ in contador.most_common(15)]
        
        # Adiciona a sigla da instituição (importante!)
        # (A sigla será adicionada externamente)
        
        return palavras_comuns
    
    def processar_arquivo_repos(self, arquivo_repos: str, arquivo_saida: str):
        """
        Processa o arquivo de repositórios e gera palavras-chave para cada instituição
        """
        print("=" * 60)
        print("🚀 GERADOR AUTOMÁTICO DE PALAVRAS-CHAVE")
        print("=" * 60)
        
        # Carrega os repositórios
        with open(arquivo_repos, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        instituicoes_keywords = []
        
        for inst in dados.get('institutions_data', []):
            sigla = inst['Sigla']
            nome = inst['Nome Completo']
            repositorios = inst.get('Repositorios', [])
            
            print(f"\n📊 Processando {sigla} - {len(repositorios)} repositórios...")
            
            if not repositorios:
                print(f"  ⚠️ Sem repositórios para análise")
                continue
            
            # Gera palavras-chave automaticamente
            palavras_geradas = self.gerar_palavras_chave_instituicao(repositorios)
            
            # SEMPRE adiciona a sigla como palavra-chave
            palavras_finais = [sigla.lower()] + palavras_geradas
            
            # Remove duplicatas mantendo ordem
            palavras_unicas = []
            [palavras_unicas.append(p) for p in palavras_finais if p not in palavras_unicas]
            
            print(f"  ✅ Palavras-chave geradas: {', '.join(palavras_unicas[:10])}")
            if len(palavras_unicas) > 10:
                print(f"     ... e mais {len(palavras_unicas) - 10} palavras")
            
            instituicoes_keywords.append({
                "Sigla": sigla,
                "Nome Completo": nome,
                "Palavras_Chave": palavras_unicas
            })
        
        # Salva no formato esperado pelo filtra_palavra_chave.py
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump({"institutions_keywords": instituicoes_keywords}, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print("✅ PROCESSO CONCLUÍDO!")
        print("=" * 60)
        print(f"📁 Arquivo gerado: {arquivo_saida}")
        print(f"📊 Total de instituições processadas: {len(instituicoes_keywords)}")

# Script para instalar dependências (execute primeiro)
def instalar_dependencias():
    """Instala as dependências necessárias"""
    import subprocess
    import sys
    
    pacotes = ['nltk']
    for pacote in pacotes:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])

if __name__ == "__main__":
    # Descomente a linha abaixo na primeira execução
    # instalar_dependencias()
    
    gerador = GeradorPalavrasChave()
    gerador.processar_arquivo_repos(
        arquivo_repos="repositorios_federais_desduplicados.json",
        arquivo_saida="palavras_chave_auto_geradas.json"
    )