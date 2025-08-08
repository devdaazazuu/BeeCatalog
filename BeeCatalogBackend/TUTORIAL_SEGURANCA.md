# 🚀 Tutorial Completo - Implementação de Segurança BeeCatalog

## 📋 Pré-requisitos

- Python 3.8+
- Django 4.0+
- PostgreSQL 12+
- Redis 6+
- Servidor web (Nginx/Apache)
- Certificado SSL

## 🎯 Objetivo

Este tutorial irá guiá-lo através da implementação completa das configurações de segurança identificadas na auditoria, transformando o BeeCatalog em uma aplicação segura para produção.

---

## 📚 Parte 1: Configuração Inicial

### 1.1 Preparar Ambiente

```bash
# 1. Navegar para o diretório do projeto
cd c:\BeeCatalog\BeeCatalog\BeeCatalogBackend

# 2. Ativar ambiente virtual (se não estiver ativo)
.\venv\Scripts\Activate.ps1

# 3. Verificar dependências atuais
pip list
```

### 1.2 Gerar Configurações de Segurança

```bash
# Executar o script de configuração
python security_config.py --environment production
```

Este comando criará:
- `.env.production` - Variáveis de ambiente para produção
- `security_settings.py` - Configurações de segurança Django

---

## 🔧 Parte 2: Configuração do Django

### 2.1 Atualizar settings.py

Abra o arquivo `backbeecatalog/settings.py` e adicione no final:

```python
# Importar configurações de segurança
if os.getenv('DJANGO_ENV') == 'production':
    from .security_settings import *
```

### 2.2 Criar settings específicos para produção

Crie o arquivo `backbeecatalog/settings_production.py`:

```python
from .settings import *
import os
from django.core.exceptions import ImproperlyConfigured

def get_env_variable(var_name, default=None):
    """Obtém variável de ambiente ou levanta exceção."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

# Configurações críticas de segurança
DEBUG = False
SECRET_KEY = get_env_variable('SECRET_KEY')
ALLOWED_HOSTS = get_env_variable('ALLOWED_HOSTS', 'localhost').split(',')

# Segurança HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Cookies seguros
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 1800  # 30 minutos
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CORS para produção
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = get_env_variable('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# Database para produção
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_variable('DB_NAME'),
        'USER': get_env_variable('DB_USER'),
        'PASSWORD': get_env_variable('DB_PASSWORD'),
        'HOST': get_env_variable('DB_HOST', 'localhost'),
        'PORT': get_env_variable('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 600,
    }
}

# Cache Redis para produção
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': get_env_variable('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'ssl_cert_reqs': None,
            },
        },
        'KEY_PREFIX': 'beecatalog_prod',
        'TIMEOUT': 300,
    }
}

# Logging de segurança
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['security_file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Email seguro
EMAIL_USE_TLS = True
EMAIL_HOST = get_env_variable('EMAIL_HOST')
EMAIL_PORT = int(get_env_variable('EMAIL_PORT', '587'))
EMAIL_HOST_USER = get_env_variable('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_env_variable('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER

# Configurações de arquivo
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644
```

---

## 🔐 Parte 3: Configuração de Variáveis de Ambiente

### 3.1 Editar arquivo .env.production

Abra o arquivo `.env.production` gerado e configure:

```bash
# Django Core
DJANGO_SETTINGS_MODULE=backbeecatalog.settings_production
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=sua-chave-super-secreta-de-50-caracteres-ou-mais-aqui

# Database
DB_NAME=beecatalog_prod
DB_USER=beecatalog_user
DB_PASSWORD=SuaSenhaSeguraAqui123!
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Hosts permitidos (substitua pelos seus domínios)
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# CORS (substitua pela URL do seu frontend)
CORS_ALLOWED_ORIGINS=https://seu-frontend.com,https://www.seu-frontend.com

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app

# Sentry (opcional)
SENTRY_DSN=https://sua-chave@sentry.io/projeto
```

### 3.2 Gerar SECRET_KEY segura

```bash
# Gerar nova SECRET_KEY
python security_config.py --generate-secret

# Copie a chave gerada e cole no arquivo .env.production
```

---

## 🗄️ Parte 4: Configuração do Banco de Dados

### 4.1 Criar usuário e banco PostgreSQL

```sql
-- Conectar como superusuário postgres
psql -U postgres

-- Criar usuário
CREATE USER beecatalog_user WITH PASSWORD 'SuaSenhaSeguraAqui123!';

-- Criar banco
CREATE DATABASE beecatalog_prod OWNER beecatalog_user;

-- Conceder privilégios
GRANT ALL PRIVILEGES ON DATABASE beecatalog_prod TO beecatalog_user;

-- Sair
\q
```

### 4.2 Configurar SSL no PostgreSQL

Edite `postgresql.conf`:

```ini
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
```

### 4.3 Executar migrações

```bash
# Carregar variáveis de ambiente
Get-Content .env.production | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

# Executar migrações
python manage.py migrate --settings=backbeecatalog.settings_production
```

---

## 🔒 Parte 5: Configuração HTTPS

### 5.1 Obter certificado SSL

**Opção 1: Let's Encrypt (Gratuito)**
```bash
# Instalar Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

**Opção 2: Certificado comercial**
- Compre de uma CA confiável
- Siga instruções do provedor

### 5.2 Configurar Nginx

Crie `/etc/nginx/sites-available/beecatalog`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self';" always;

    # Django static files
    location /static/ {
        alias /path/to/your/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Django media files
    location /media/ {
        alias /path/to/your/media/files/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Proxy to Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        # ... outros headers proxy ...
    }
}
```

### 5.3 Ativar configuração Nginx

```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/beecatalog /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

---

## 🛡️ Parte 6: Implementar Rate Limiting

### 6.1 Instalar django-ratelimit

```bash
pip install django-ratelimit
```

### 6.2 Adicionar ao requirements.txt

```txt
django-ratelimit==4.1.0
```

### 6.3 Aplicar rate limiting nas views

Edite suas views críticas:

```python
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.views import LoginView

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

# Para views baseadas em função
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def api_endpoint(request):
    # sua lógica aqui
    pass
```

---

## 📊 Parte 7: Configurar Monitoramento

### 7.1 Configurar Sentry

```bash
# Instalar Sentry SDK
pip install sentry-sdk[django]
```

Adicione ao settings_production.py:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=get_env_variable('SENTRY_DSN', ''),
    integrations=[
        DjangoIntegration(auto_enabling_integrations=False),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    send_default_pii=False,
    environment='production',
)
```

### 7.2 Configurar logs de segurança

Crie o diretório de logs:

```bash
mkdir logs
touch logs/security.log
chmod 640 logs/security.log
```

---

## 🔄 Parte 8: Deploy e Verificação

### 8.1 Script de deploy

Crie `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Iniciando deploy de produção..."

# Carregar variáveis de ambiente
source .env.production

# Verificar configurações de segurança
echo "🔍 Verificando configurações..."
python manage.py check --deploy --settings=backbeecatalog.settings_production

# Executar migrações
echo "📊 Executando migrações..."
python manage.py migrate --settings=backbeecatalog.settings_production

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=backbeecatalog.settings_production

# Reiniciar serviços
echo "🔄 Reiniciando serviços..."
sudo systemctl restart gunicorn
sudo systemctl reload nginx

echo "✅ Deploy concluído com sucesso!"
```

### 8.2 Configurar Gunicorn

Crie `gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
user = "www-data"
group = "www-data"
tmp_upload_dir = None
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
```

### 8.3 Criar serviço systemd

Crie `/etc/systemd/system/beecatalog.service`:

```ini
[Unit]
Description=BeeCatalog Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/BeeCatalog/BeeCatalogBackend
EnvironmentFile=/path/to/BeeCatalog/BeeCatalogBackend/.env.production
ExecStart=/path/to/venv/bin/gunicorn --config gunicorn.conf.py backbeecatalog.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 8.4 Executar deploy

```bash
# Tornar script executável
chmod +x deploy.sh

# Executar deploy
./deploy.sh

# Habilitar e iniciar serviço
sudo systemctl enable beecatalog
sudo systemctl start beecatalog
```

---

## ✅ Parte 9: Verificação Final

### 9.1 Testes de segurança

```bash
# Verificar configurações Django
python security_config.py --check-config

# Verificar deploy
python manage.py check --deploy --settings=backbeecatalog.settings_production

# Análise de código
bandit -r . --skip B101,B601 -ll
```

### 9.2 Testes externos

1. **SSL Labs Test**: https://www.ssllabs.com/ssltest/
2. **Security Headers**: https://securityheaders.com/
3. **Mozilla Observatory**: https://observatory.mozilla.org/

### 9.3 Checklist final

- [ ] ✅ DEBUG = False
- [ ] ✅ SECRET_KEY segura configurada
- [ ] ✅ HTTPS funcionando
- [ ] ✅ Headers de segurança configurados
- [ ] ✅ Rate limiting ativo
- [ ] ✅ Logs de segurança funcionando
- [ ] ✅ Backup configurado
- [ ] ✅ Monitoramento ativo

---

## 🆘 Parte 10: Troubleshooting

### 10.1 Problemas comuns

**Erro: "ALLOWED_HOSTS"**
```python
# Adicione seu domínio ao ALLOWED_HOSTS
ALLOWED_HOSTS = ['seu-dominio.com', 'www.seu-dominio.com']
```

**Erro: "CSRF verification failed"**
```python
# Verifique CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [
    "https://seu-frontend.com",
]
```

**Erro: "SSL required"**
```bash
# Verifique certificado SSL
sudo certbot certificates
```

### 10.2 Logs importantes

```bash
# Logs do Django
tail -f logs/security.log

# Logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Logs do sistema
sudo journalctl -u beecatalog -f
```

### 10.3 Comandos úteis

```bash
# Verificar status dos serviços
sudo systemctl status beecatalog
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# Reiniciar serviços
sudo systemctl restart beecatalog
sudo systemctl reload nginx

# Verificar portas
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :8000
```

---

## 📚 Recursos Adicionais

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

## 🎉 Conclusão

Parabéns! Você implementou com sucesso todas as configurações de segurança necessárias para o BeeCatalog. Seu sistema agora está protegido contra as principais vulnerabilidades e pronto para produção.

### Próximos passos:
1. Monitore logs de segurança regularmente
2. Mantenha dependências atualizadas
3. Execute auditorias de segurança mensais
4. Implemente testes de penetração trimestrais

**Lembre-se**: A segurança é um processo contínuo, não um destino final!

---

**Criado em:** $(Get-Date -Format "yyyy-MM-dd")
**Versão:** 1.0
**Autor:** Sistema de Auditoria BeeCatalog