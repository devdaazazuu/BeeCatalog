#!/bin/bash
set -e

echo "🚀 Iniciando deploy de produção..."

# Verificar se arquivo .env.production existe
if [ ! -f ".env.production" ]; then
    echo "❌ Arquivo .env.production não encontrado!"
    echo "Execute: python setup_security.py --step 3"
    exit 1
fi

# Carregar variáveis de ambiente (Linux/Mac)
if [ "$OS" != "Windows_NT" ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Verificar configurações de segurança
echo "🔍 Verificando configurações..."
python manage.py check --deploy --settings=backbeecatalog.settings_production

if [ $? -ne 0 ]; then
    echo "❌ Verificação de segurança falhou!"
    exit 1
fi

# Executar migrações
echo "📊 Executando migrações..."
python manage.py migrate --settings=backbeecatalog.settings_production

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=backbeecatalog.settings_production

echo "✅ Deploy concluído com sucesso!"
echo "📋 Próximos passos:"
echo "1. Configure seu servidor web (Nginx/Apache)"
echo "2. Configure certificado SSL"
echo "3. Reinicie os serviços"
