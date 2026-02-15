#!/bin/bash
# install.sh - Script de instalação completa

echo "========================================="
echo "🔧 INSTALANDO DEPENDÊNCIAS DO SISTEMA"
echo "========================================="
echo ""

# 1. Verificar Python
echo "📌 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    echo "   Instale com: sudo apt install python3 python3-pip (Ubuntu)"
    echo "   ou: brew install python (macOS)"
    exit 1
fi

PY_VERSION=$(python3 --version)
echo "✅ $PY_VERSION encontrado"
echo ""

# 2. Criar ambiente virtual (opcional mas recomendado)
echo "📌 Criando ambiente virtual..."
python3 -m venv .venv
source .venv/bin/activate
echo "✅ Ambiente virtual ativado"
echo ""

# 3. Atualizar pip
echo "📌 Atualizando pip..."
python3 -m pip install --upgrade pip
echo ""

# 4. Instalar dependências
echo "📌 Instalando dependências Python..."
python3 -m pip install -r requirements.txt
echo ""

# 5. Baixar recursos do NLTK
echo "📌 Baixando recursos do NLTK..."
python3 -c "
import nltk
print('   📥 Download punkt...')
nltk.download('punkt', quiet=True)
print('   📥 Download stopwords...')
nltk.download('stopwords', quiet=True)
print('✅ NLTK configurado!')
"
echo ""

# 6. Configurar arquivo .env
echo "📌 Configurando token do GitHub..."
if [ ! -f ".env" ]; then
    echo "# GitHub Token" > .env
    echo "GITHUB_TOKEN=seu_token_aqui" >> .env
    echo "✅ Arquivo .env criado"
    echo ""
    echo "⚠️  IMPORTANTE: Edite o arquivo .env e coloque seu token do GitHub!"
    echo "   nano .env"
else
    echo "✅ Arquivo .env já existe"
fi
echo ""

# 7. Verificar estrutura de diretórios
echo "📌 Verificando diretórios..."
mkdir -p dados
mkdir -p logs
echo "✅ Diretórios criados: dados/, logs/"
echo ""

echo "========================================="
echo "✅ INSTALAÇÃO CONCLUÍDA!"
echo "========================================="
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Coloque os arquivos CSV na pasta 'dados/':"
echo "   - institutos_federais.csv"
echo "   - universidades_federais.csv"
echo "   - cefet.csv (opcional)"
echo ""
echo "2. Edite o arquivo .env com seu token do GitHub:"
echo "   nano .env"
echo ""
echo "3. Execute o script principal:"
echo "   python3 github_busca_inteligente.py"
echo ""
echo "4. Para ativar o ambiente virtual nas próximas vezes:"
echo "   source .venv/bin/activate"
echo "========================================="