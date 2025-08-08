# 🚀 Guia Rápido - Configuração de Segurança BeeCatalog

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **PostgreSQL** instalado e rodando
3. **Redis** instalado e rodando (opcional para desenvolvimento)
4. Estar no diretório do projeto Django

## ⚡ Uso Rápido

### 1. Configuração Automática Completa
```bash
# Execute todas as etapas de uma vez
python setup_security.py --all
```

### 2. Configuração Passo a Passo
```bash
# Etapa 1: Preparar ambiente
python setup_security.py --step 1

# Etapa 2: Criar configurações de produção
python setup_security.py --step 2

# Etapa 3: Criar arquivo de ambiente
python setup_security.py --step 3

# Etapa 4: Instalar pacotes de segurança
python setup_security.py --step 4

# Etapa 5: Criar script de deploy
python setup_security.py --step 5

# Etapa 6: Criar configuração Nginx
python setup_security.py --step 6
```

### 3. Verificar Configurações
```bash
# Verificar se tudo está configurado corretamente
python setup_security.py --check
```

## 🔧 Configuração Manual Necessária

Após executar o script, você DEVE editar o arquivo `.env.production`:

```bash
# Abrir arquivo para edição
notepad .env.production
```

**Configure obrigatoriamente:**
- `DB_PASSWORD=` - Senha do PostgreSQL
- `ALLOWED_HOSTS=` - Seus domínios (ex: meusite.com)
- `CORS_ALLOWED_ORIGINS=` - URL do frontend (ex: https://meuapp.com)

**Configure opcionalmente:**
- `EMAIL_*` - Configurações de email
- `SENTRY_DSN` - Monitoramento de erros

## 🗄️ Configurar PostgreSQL

### Windows (usando psql):
```sql
-- Conectar como superusuário
psql -U postgres

-- Criar banco e usuário
CREATE DATABASE beecatalog_prod;
CREATE USER beecatalog_user WITH PASSWORD 'SUA_SENHA_AQUI';
GRANT ALL PRIVILEGES ON DATABASE beecatalog_prod TO beecatalog_user;
ALTER USER beecatalog_user CREATEDB;
\q
```

### Testar conexão:
```bash
psql -h localhost -U beecatalog_user -d beecatalog_prod
```

## 🚀 Deploy

### 1. Verificar configurações:
```bash
python setup_security.py --check
```

### 2. Executar deploy:
```bash
# Linux/Mac
./deploy.sh

# Windows
bash deploy.sh
```

### 3. Iniciar servidor:
```bash
# Desenvolvimento (apenas para testes)
python manage.py runserver --settings=backbeecatalog.settings_production

# Produção com Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 3 backbeecatalog.wsgi:application
```

## 🔍 Verificações de Segurança

### Verificar configurações Django:
```bash
python manage.py check --deploy --settings=backbeecatalog.settings_production
```

### Testar HTTPS (após configurar SSL):
```bash
curl -I https://seudominio.com
```

### Verificar headers de segurança:
```bash
curl -I https://seudominio.com | grep -E "(Strict-Transport|X-Content|X-Frame)"
```

## 📁 Arquivos Criados

O script cria os seguintes arquivos:

- `.env.production` - Variáveis de ambiente
- `backbeecatalog/settings_production.py` - Configurações Django
- `deploy.sh` - Script de deploy
- `nginx_beecatalog.conf` - Configuração Nginx
- `logs/` - Diretório para logs
- `requirements_security.txt` - Dependências atualizadas

## 🆘 Solução de Problemas

### Erro: "manage.py não encontrado"
```bash
# Certifique-se de estar no diretório correto
cd c:\BeeCatalog\BeeCatalog\BeeCatalogBackend
python setup_security.py --all
```

### Erro: "ImproperlyConfigured"
```bash
# Verifique se .env.production está configurado
python setup_security.py --check
```

### Erro de conexão PostgreSQL:
```bash
# Verifique se PostgreSQL está rodando
psql -U postgres -c "SELECT version();"

# Verifique configurações em .env.production
cat .env.production | grep DB_
```

### Erro de permissão (Linux/Mac):
```bash
# Dar permissão ao script
chmod +x deploy.sh
```

## 📞 Próximos Passos

1. **Configure SSL/HTTPS:**
   - Obtenha certificado SSL (Let's Encrypt recomendado)
   - Configure Nginx com o arquivo `nginx_beecatalog.conf`

2. **Configure monitoramento:**
   - Crie conta no Sentry.io
   - Configure `SENTRY_DSN` no `.env.production`

3. **Backup:**
   - Configure backup automático do PostgreSQL
   - Configure backup dos arquivos de mídia

4. **Monitoramento:**
   - Configure alertas para logs de segurança
   - Configure monitoramento de performance

## 📚 Recursos Adicionais

- [Documentação Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Mozilla SSL Configuration](https://ssl-config.mozilla.org/)
- [Let's Encrypt](https://letsencrypt.org/)

---

**⚠️ IMPORTANTE:** Sempre teste as configurações em um ambiente de desenvolvimento antes de aplicar em produção!