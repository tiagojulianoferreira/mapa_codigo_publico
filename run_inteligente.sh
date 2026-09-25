#!/bin/bash
# run_inteligente.sh - Executa o pipeline inteligente

echo "========================================="
echo "🚀 INICIANDO BUSCA INTELIGENTE"
echo "========================================="
echo ""

# Ativar ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Ambiente virtual ativado"
fi

# Verificar token
if [ ! -f ".env" ] || ! grep -q "GITHUB_TOKEN" .env; then
    echo "❌ Token do GitHub não configurado!"
    echo "   Edite o arquivo .env com seu token"
    exit 1
fi

# Timestamp para logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/execucao_${TIMESTAMP}.log"

echo "📝 Log: $LOG_FILE"
echo ""

# Executar busca inteligente
echo "📦 Executando busca com feedback loop..."
python3 github_busca_inteligente.py 2>&1 | tee "$LOG_FILE"

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ EXECUÇÃO CONCLUÍDA COM SUCESSO!"
    echo ""
    echo "📊 ARQUIVOS GERADOS:"
    ls -la repositorios_federais_inteligente.json 2>/dev/null && \
        echo "   - repositorios_federais_inteligente.json (principal)"
    ls -la palavras_chave_inteligentes.json 2>/dev/null && \
        echo "   - palavras_chave_inteligentes.json (keywords)"
    
    # Estatísticas rápidas
    if [ -f "repositorios_federais_inteligente.json" ]; then
        TOTAL_REPOS=$(grep -o '"Nome do Repositório"' repositorios_federais_inteligente.json | wc -l)
        TOTAL_INST=$(grep -o '"Sigla"' repositorios_federais_inteligente.json | sort -u | wc -l)
        echo ""
        echo "📊 ESTATÍSTICAS:"
        echo "   Instituições: $TOTAL_INST"
        echo "   Repositórios: $TOTAL_REPOS"
    fi
else
    echo ""
    echo "❌ ERRO NA EXECUÇÃO!"
    echo "   Verifique o log: $LOG_FILE"
fi

echo ""
echo "========================================="