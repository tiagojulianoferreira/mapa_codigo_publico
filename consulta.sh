#!/bin/bash

# Script de execução do pipeline completo
# Nome: executar_pipeline.sh

echo "========================================="
echo "🚀 PIPELINE COMPLETO DE REPOSITÓRIOS FEDERAIS"
echo "========================================="
echo ""

# Configuração do Python
PYTHON="python3"

# Verificar se python3 existe
if ! command -v $PYTHON &> /dev/null; then
    echo "⚠️  python3 não encontrado! Tentando python..."
    PYTHON="python"
    if ! command -v $PYTHON &> /dev/null; then
        echo "❌ ERRO: Nenhum Python encontrado no sistema!"
        exit 1
    fi
fi

echo "✅ Usando: $(which $PYTHON)"
echo "✅ Versão: $($PYTHON --version)"
echo ""

# Criar diretório de logs se não existir
mkdir -p logs

# Registrar início
echo "📝 Início: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a logs/pipeline.log
echo ""

# ========================================
# ETAPA 1: Busca com paginação
# ========================================
echo "📦 [1/4] Buscando repositórios no GitHub (com paginação)..."
echo "-----------------------------------------"
if $PYTHON github_busca_ampla.py 2>&1 | tee -a logs/etapa1.log; then
    echo "✅ Etapa 1 concluída com sucesso!"
    
    # Verificar se o arquivo foi gerado
    if [ -f "repositorios_federais_desduplicados.json" ]; then
        TOTAL_REPOS=$(grep -o '"Nome do Repositório"' repositorios_federais_desduplicados.json | wc -l)
        echo "   📊 Total de repositórios brutos: $TOTAL_REPOS"
    fi
else
    echo "❌ ERRO na Etapa 1!"
    exit 1
fi
echo "" && sleep 2

# ========================================
# ETAPA 2: Gerar palavras-chave automaticamente
# ========================================
echo "📦 [2/4] Gerando palavras-chave automaticamente..."
echo "-----------------------------------------"
if $PYTHON gerador_palavras_chave_auto.py 2>&1 | tee -a logs/etapa2.log; then
    echo "✅ Etapa 2 concluída com sucesso!"
    
    # Verificar se o arquivo foi gerado
    if [ -f "palavras_chave_auto_geradas.json" ]; then
        TOTAL_INST=$(grep -o '"Sigla"' palavras_chave_auto_geradas.json | wc -l)
        echo "   📊 Palavras-chave geradas para $TOTAL_INST instituições"
    fi
else
    echo "❌ ERRO na Etapa 2!"
    exit 1
fi
echo "" && sleep 2

# ========================================
# ETAPA 3: Filtrar por palavras-chave
# ========================================
echo "📦 [3/4] Filtrando repositórios por palavras-chave..."
echo "-----------------------------------------"

# Faz backup do arquivo original de keywords se existir
if [ -f "palavras_chave_instituicoes_v2.json" ] && [ ! -f "palavras_chave_instituicoes_v2.json.bak" ]; then
    cp palavras_chave_instituicoes_v2.json palavras_chave_instituicoes_v2.json.bak
    echo "   📦 Backup criado: palavras_chave_instituicoes_v2.json.bak"
fi

# Substitui pelo arquivo gerado automaticamente
cp palavras_chave_auto_geradas.json palavras_chave_instituicoes_v2.json

if $PYTHON filtra_palavra_chave.py 2>&1 | tee -a logs/etapa3.log; then
    echo "✅ Etapa 3 concluída com sucesso!"
    
    # Verificar se o arquivo foi gerado
    if [ -f "repositorios_filtrados.json" ]; then
        TOTAL_FILTRADOS=$(grep -o '"Nome do Repositório"' repositorios_filtrados.json | wc -l)
        echo "   📊 Repositórios após filtro de palavras: $TOTAL_FILTRADOS"
    fi
else
    echo "❌ ERRO na Etapa 3!"
    
    # Restaura o backup em caso de erro
    if [ -f "palavras_chave_instituicoes_v2.json.bak" ]; then
        cp palavras_chave_instituicoes_v2.json.bak palavras_chave_instituicoes_v2.json
        echo "   🔄 Backup restaurado"
    fi
    exit 1
fi
echo "" && sleep 2

# ========================================
# ETAPA 4: Filtrar por idioma (Português)
# ========================================
echo "📦 [4/4] Filtrando repositórios por idioma (Português)..."
echo "-----------------------------------------"
if $PYTHON filtrar_idioma.py 2>&1 | tee -a logs/etapa4.log; then
    echo "✅ Etapa 4 concluída com sucesso!"
    
    # Verificar se o arquivo final foi gerado
    if [ -f "repositorios_federais_filtrado_idioma.json" ]; then
        TOTAL_FINAL=$(grep -o '"Nome do Repositório"' repositorios_federais_filtrado_idioma.json | wc -l)
        echo "   📊 Repositórios finais (Português): $TOTAL_FINAL"
    fi
else
    echo "❌ ERRO na Etapa 4!"
    exit 1
fi
echo ""

# ========================================
# RESUMO FINAL
# ========================================
echo "========================================="
echo "✅ PIPELINE CONCLUÍDO COM SUCESSO!"
echo "========================================="
echo "📊 RESUMO:"
echo "-----------------------------------------"

# Estatísticas
if [ -f "repositorios_federais_desduplicados.json" ]; then
    REPOS_BRUTOS=$(grep -o '"Nome do Repositório"' repositorios_federais_desduplicados.json | wc -l)
    echo "   Etapa 1 - Repositórios brutos: $REPOS_BRUTOS"
fi

if [ -f "repositorios_filtrados.json" ]; then
    REPOS_KEYWORDS=$(grep -o '"Nome do Repositório"' repositorios_filtrados.json | wc -l)
    echo "   Etapa 3 - Após palavras-chave: $REPOS_KEYWORDS"
fi

if [ -f "repositorios_federais_filtrado_idioma.json" ]; then
    REPOS_FINAL=$(grep -o '"Nome do Repositório"' repositorios_federais_filtrado_idioma.json | wc -l)
    echo "   Etapa 4 - FINAL (Português): $REPOS_FINAL"
fi

echo "-----------------------------------------"
echo "📁 Arquivos gerados:"
ls -la *.json 2>/dev/null | awk '{print "   " $9 " (" $5 " bytes)"}'
echo "-----------------------------------------"
echo "📝 Logs salvos em: ./logs/"
echo "📅 Término: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a logs/pipeline.log
echo "========================================="

# Verifica se o arquivo do frontend foi gerado
if [ -f "repositorios_federais_filtrado_idioma.json" ]; then
    echo ""
    echo "🎯 ARQUIVO PRONTO PARA O FRONTEND!"
    echo "   repositorios_federais_filtrado_idioma.json"
    echo ""
    echo "👉 Copie para o diretório do frontend se necessário"
fi

echo ""