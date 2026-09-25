#!/usr/bin/env python3
"""
Filtro de Stopwords para Repositórios
Remove repositórios que contenham stopwords no nome ou descrição
"""

import json
import re
from typing import List, Set, Dict
from pathlib import Path
import os
from datetime import datetime

class FiltroStopwords:
    def __init__(self, stopwords_file: str = "stopwords.txt"):
        """
        Inicializa o filtro carregando as stopwords do arquivo
        """
        self.stopwords_file = stopwords_file
        self.stopwords = self._carregar_stopwords()
        self.stopwords_pattern = self._criar_padrao_regex()
        
        print(f"✅ Carregadas {len(self.stopwords)} stopwords de '{stopwords_file}'")
        
    def _carregar_stopwords(self) -> Set[str]:
        """
        Carrega stopwords do arquivo, uma por linha
        """
        stopwords = set()
        
        if not os.path.exists(self.stopwords_file):
            print(f"⚠️ Arquivo '{self.stopwords_file}' não encontrado!")
            return stopwords
        
        try:
            with open(self.stopwords_file, 'r', encoding='utf-8') as f:
                for linha in f:
                    # Remove espaços em branco e linhas vazias
                    palavra = linha.strip()
                    if palavra and not palavra.startswith('#'):
                        stopwords.add(palavra.lower())
        except Exception as e:
            print(f"❌ Erro ao ler stopwords: {e}")
        
        return stopwords
    
    def _criar_padrao_regex(self) -> re.Pattern:
        """
        Cria um padrão regex para buscar stopwords no texto
        """
        if not self.stopwords:
            return re.compile(r'(?!x)x')  # Padrão que nunca match
        
        # Escapa caracteres especiais e junta com |
        palavras_escapadas = [re.escape(p) for p in self.stopwords]
        padrao = '|'.join(palavras_escapadas)
        
        # Busca por palavra inteira (usando boundaries)
        return re.compile(rf'\b({padrao})\b', re.IGNORECASE)
    
    def texto_contem_stopword(self, texto: str) -> bool:
        """
        Verifica se o texto contém alguma stopword
        """
        if not texto or texto == 'N/A' or not self.stopwords:
            return False
        
        # Usa regex para busca eficiente
        return bool(self.stopwords_pattern.search(texto))
    
    def filtrar_repositorios(
        self, 
        arquivo_entrada: str,
        arquivo_saida: str = None,
        criar_backup: bool = True
    ) -> Dict:
        """
        Filtra repositórios removendo os que contêm stopwords
        
        Args:
            arquivo_entrada: Arquivo JSON com repositórios
            arquivo_saida: Arquivo de saída (opcional)
            criar_backup: Se True, cria backup do arquivo original
        
        Returns:
            Dicionário com estatísticas do filtro
        """
        print("\n" + "="*70)
        print("🚫 FILTRO DE STOPWORDS")
        print("="*70)
        
        # Verifica arquivo de entrada
        if not os.path.exists(arquivo_entrada):
            print(f"❌ Arquivo '{arquivo_entrada}' não encontrado!")
            return None
        
        # Cria backup
        if criar_backup:
            backup_file = f"{arquivo_entrada}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(arquivo_entrada, backup_file)
            print(f"✅ Backup criado: {backup_file}")
        
        # Carrega dados
        print(f"\n📂 Carregando: {arquivo_entrada}")
        with open(arquivo_entrada, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Estatísticas iniciais
        stats = {
            'total_repos_antes': 0,
            'total_repos_depois': 0,
            'total_instituicoes_antes': len(dados.get('institutions_data', [])),
            'total_instituicoes_depois': 0,
            'repos_removidos': 0,
            'remocoes_por_stopword': {sw: 0 for sw in list(self.stopwords)[:20]},  # Top 20
            'stopwords_encontradas': set()
        }
        
        for inst in dados.get('institutions_data', []):
            stats['total_repos_antes'] += len(inst.get('Repositorios', []))
        
        print(f"\n📊 Antes do filtro:")
        print(f"   - Instituições: {stats['total_instituicoes_antes']}")
        print(f"   - Repositórios: {stats['total_repos_antes']}")
        
        # Processa cada instituição
        novas_instituicoes = []
        
        for inst in dados.get('institutions_data', []):
            sigla = inst.get('Sigla', 'N/A')
            repos_originais = inst.get('Repositorios', [])
            
            if not repos_originais:
                continue
            
            novos_repos = []
            
            for repo in repos_originais:
                # Verifica nome e descrição
                nome = repo.get('Nome do Repositório', '')
                descricao = repo.get('Descricao', '')
                
                # Combina os campos para verificação
                texto = f"{nome} {descricao}"
                
                # Verifica se contém stopword
                if self.texto_contem_stopword(texto):
                    stats['repos_removidos'] += 1
                    
                    # Identifica qual stopword causou a remoção
                    match = self.stopwords_pattern.search(texto)
                    if match:
                        stopword_encontrada = match.group(0).lower()
                        stats['stopwords_encontradas'].add(stopword_encontrada)
                        
                        # Atualiza contador (para as top 20)
                        if stopword_encontrada in stats['remocoes_por_stopword']:
                            stats['remocoes_por_stopword'][stopword_encontrada] += 1
                else:
                    novos_repos.append(repo)
            
            if novos_repos:
                inst['Repositorios'] = novos_repos
                novas_instituicoes.append(inst)
                stats['total_repos_depois'] += len(novos_repos)
        
        stats['total_instituicoes_depois'] = len(novas_instituicoes)
        
        # Cria nova estrutura
        dados_filtrados = {
            "institutions_data": novas_instituicoes
        }
        
        # Preserva cluster_descriptions se existir
        if 'cluster_descriptions' in dados:
            dados_filtrados['cluster_descriptions'] = dados['cluster_descriptions']
        
        # Gera nome de saída se não fornecido
        if arquivo_saida is None:
            base, ext = os.path.splitext(arquivo_entrada)
            arquivo_saida = f"{base}_sem_stopwords{ext}"
        
        # Salva arquivo
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(dados_filtrados, f, indent=2, ensure_ascii=False)
        
        # Estatísticas finais
        self._exibir_estatisticas(stats, arquivo_saida)
        
        return stats
    
    def _exibir_estatisticas(self, stats: Dict, arquivo_saida: str):
        """
        Exibe estatísticas detalhadas do filtro
        """
        taxa_remocao = (stats['repos_removidos'] / stats['total_repos_antes'] * 100) if stats['total_repos_antes'] > 0 else 0
        
        print("\n" + "="*70)
        print("📊 ESTATÍSTICAS DO FILTRO")
        print("="*70)
        print(f"\n📂 Arquivo de saída: {arquivo_saida}")
        print(f"\n📊 INSTITUIÇÕES:")
        print(f"   - Antes: {stats['total_instituicoes_antes']}")
        print(f"   - Depois: {stats['total_instituicoes_depois']}")
        
        print(f"\n📊 REPOSITÓRIOS:")
        print(f"   - Antes: {stats['total_repos_antes']}")
        print(f"   - Depois: {stats['total_repos_depois']}")
        print(f"   - Removidos: {stats['repos_removidos']}")
        print(f"   - Taxa de remoção: {taxa_remocao:.1f}%")
        
        # Top stopwords que mais removeram
        print(f"\n🔝 TOP STOPWORDS QUE MAIS REMOVERAM:")
        stopwords_ordenadas = sorted(
            [(sw, count) for sw, count in stats['remocoes_por_stopword'].items() if count > 0],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        if stopwords_ordenadas:
            for i, (sw, count) in enumerate(stopwords_ordenadas, 1):
                print(f"   {i:2d}. '{sw}': {count} remoções")
        else:
            print("   Nenhuma stopword encontrada")
        
        print(f"\n✅ Total de stopwords diferentes encontradas: {len(stats['stopwords_encontradas'])}")

def atualizar_stopwords(
    arquivo_stopwords: str = "stopwords.txt",
    novas_stopwords: List[str] = None
):
    """
    Adiciona novas stopwords ao arquivo
    """
    stopwords_existentes = set()
    
    # Carrega stopwords existentes
    if os.path.exists(arquivo_stopwords):
        with open(arquivo_stopwords, 'r', encoding='utf-8') as f:
            stopwords_existentes = set(linha.strip() for linha in f if linha.strip())
    
    # Adiciona novas
    if novas_stopwords:
        stopwords_existentes.update(novas_stopwords)
        
        # Salva arquivo ordenado
        with open(arquivo_stopwords, 'w', encoding='utf-8') as f:
            for palavra in sorted(stopwords_existentes):
                f.write(f"{palavra}\n")
        
        print(f"✅ Arquivo '{arquivo_stopwords}' atualizado com {len(stopwords_existentes)} stopwords")
    
    return stopwords_existentes

def extrair_stopwords_de_repositorios(
    arquivo_repos: str,
    arquivo_stopwords: str = "stopwords.txt",
    minimo_ocorrencias: int = 3
):
    """
    Extrai possíveis stopwords dos repositórios (nomes de projetos comuns)
    """
    from collections import Counter
    
    if not os.path.exists(arquivo_repos):
        print(f"❌ Arquivo '{arquivo_repos}' não encontrado!")
        return
    
    # Carrega dados
    with open(arquivo_repos, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    # Conta nomes de repositórios
    contador = Counter()
    
    for inst in dados.get('institutions_data', []):
        for repo in inst.get('Repositorios', []):
            nome = repo.get('Nome do Repositório', '')
            if nome and nome != 'N/A':
                # Extrai palavras individuais
                palavras = re.findall(r'[a-zA-Z][a-zA-Z0-9_-]{3,}', nome)
                contador.update([p.lower() for p in palavras])
    
    # Filtra palavras muito comuns (possíveis stopwords)
    possiveis_stopwords = [
        palavra for palavra, count in contador.most_common(100)
        if count >= minimo_ocorrencias and len(palavra) > 2
    ]
    
    print(f"\n📊 Palavras comuns encontradas (possíveis stopwords):")
    for i, palavra in enumerate(possiveis_stopwords[:20], 1):
        print(f"   {i:2d}. '{palavra}': {contador[palavra]} ocorrências")
    
    # Pergunta se quer adicionar
    print("\n" + "="*70)
    resposta = input("Deseja adicionar estas palavras ao arquivo de stopwords? (s/N): ").strip().lower()
    
    if resposta == 's':
        atualizar_stopwords(arquivo_stopwords, possiveis_stopwords)
        print("✅ Stopwords atualizadas!")

def main():
    """Função principal com menu interativo"""
    
    print("\n" + "="*70)
    print("🚫 FILTRO DE STOPWORDS PARA REPOSITÓRIOS")
    print("="*70)
    
    arquivo_stopwords = "stopwords.txt"
    
    # Menu
    print("\nOPÇÕES:")
    print("  1. Filtrar repositórios (remover stopwords)")
    print("  2. Ver stopwords atuais")
    print("  3. Adicionar novas stopwords")
    print("  4. Extrair stopwords de repositórios")
    print("  5. Sair")
    
    opcao = input("\nEscolha uma opção (1-5): ").strip()
    
    if opcao == '1':
        # Lista arquivos JSON
        json_files = [f for f in os.listdir('.') if f.endswith('.json')]
        
        if not json_files:
            print("❌ Nenhum arquivo JSON encontrado!")
            return
        
        print("\nArquivos disponíveis:")
        for i, file in enumerate(json_files, 1):
            tamanho = os.path.getsize(file) / 1024
            print(f"  {i:2d}. {file} ({tamanho:.1f} KB)")
        
        try:
            escolha = int(input("\nEscolha o arquivo (número): "))
            arquivo_entrada = json_files[escolha - 1]
            
            filtro = FiltroStopwords(arquivo_stopwords)
            
            if not filtro.stopwords:
                print("⚠️ Arquivo de stopwords vazio! Adicione stopwords primeiro.")
                return
            
            filtro.filtrar_repositorios(arquivo_entrada)
            
        except (ValueError, IndexError):
            print("❌ Opção inválida!")
    
    elif opcao == '2':
        if os.path.exists(arquivo_stopwords):
            with open(arquivo_stopwords, 'r', encoding='utf-8') as f:
                stopwords = [linha.strip() for linha in f if linha.strip()]
            
            print(f"\n📋 Stopwords no arquivo '{arquivo_stopwords}':")
            for i, sw in enumerate(sorted(stopwords), 1):
                print(f"   {i:3d}. {sw}")
            print(f"\nTotal: {len(stopwords)} stopwords")
        else:
            print(f"❌ Arquivo '{arquivo_stopwords}' não encontrado!")
    
    elif opcao == '3':
        print("\nDigite as novas stopwords (uma por linha, Enter vazio para terminar):")
        novas = []
        while True:
            palavra = input("> ").strip()
            if not palavra:
                break
            novas.append(palavra)
        
        if novas:
            atualizar_stopwords(arquivo_stopwords, novas)
    
    elif opcao == '4':
        json_files = [f for f in os.listdir('.') if f.endswith('.json')]
        
        if not json_files:
            print("❌ Nenhum arquivo JSON encontrado!")
            return
        
        print("\nArquivos disponíveis:")
        for i, file in enumerate(json_files, 1):
            print(f"  {i}. {file}")
        
        try:
            escolha = int(input("\nEscolha o arquivo (número): "))
            arquivo_repos = json_files[escolha - 1]
            extrair_stopwords_de_repositorios(arquivo_repos, arquivo_stopwords)
        except (ValueError, IndexError):
            print("❌ Opção inválida!")
    
    elif opcao == '5':
        print("👋 Até mais!")
        return
    
    else:
        print("❌ Opção inválida!")

if __name__ == "__main__":
    main()