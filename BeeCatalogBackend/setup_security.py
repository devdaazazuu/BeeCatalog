#!/usr/bin/env python3
"""
Script Automatizado de Configuração de Segurança - BeeCatalog

Este script automatiza a implementação das configurações de segurança
identificadas na auditoria, seguindo o tutorial passo a passo.

Uso:
    python setup_security.py --step 1    # Executar etapa específica
    python setup_security.py --all       # Executar todas as etapas
    python setup_security.py --check     # Verificar configurações
    python setup_security.py --help      # Mostrar ajuda
"""

import os
import sys
import argparse
import subprocess
import secrets
import string
from pathlib import Path
from datetime import datetime

class SecuritySetup:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.env_file = self.base_dir / '.env.production'
        self.settings_file = self.base_dir / 'backbeecatalog' / 'settings_production.py'
        self.logs_dir = self.base_dir / 'logs'
        
    def print_step(self, step_num, description):
        """Imprime cabeçalho da etapa."""
        print(f"\n{'='*60}")
        print(f"🔧 ETAPA {step_num}: {description}")
        print(f"{'='*60}")
    
    def print_success(self, message):
        """Imprime mensagem de sucesso."""
        print(f"✅ {message}")
    
    def print_warning(self, message):
        """Imprime mensagem de aviso."""
        print(f"⚠️  {message}")
    
    def print_error(self, message):
        """Imprime mensagem de erro."""
        print(f"❌ {message}")
    
    def run_command(self, command, check=True):
        """Executa comando no shell."""
        try:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
    
    def generate_secret_key(self, length=50):
        """Gera SECRET_KEY segura."""
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def step_1_prepare_environment(self):
        """Etapa 1: Preparar ambiente."""
        self.print_step(1, "Preparar Ambiente")
        
        # Verificar se estamos no diretório correto
        if not (self.base_dir / 'manage.py').exists():
            self.print_error("manage.py não encontrado. Execute este script no diretório do projeto Django.")
            return False
        
        # Criar diretório de logs
        self.logs_dir.mkdir(exist_ok=True)
        self.print_success("Diretório de logs criado")
        
        # Verificar dependências essenciais
        required_packages = ['django', 'djangorestframework', 'django-cors-headers']
        for package in required_packages:
            success, _, _ = self.run_command(f"pip show {package}")
            if success:
                self.print_success(f"{package} instalado")
            else:
                self.print_warning(f"{package} não encontrado")
        
        return True
    
    def step_2_create_production_settings(self):
        """Etapa 2: Criar configurações de produção."""
        self.print_step(2, "Criar Configurações de Produção")
        
        settings_content = '''from .settings import *
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
            'sslmode': 'prefer',
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
EMAIL_HOST = get_env_variable('EMAIL_HOST', '')
EMAIL_PORT = int(get_env_variable('EMAIL_PORT', '587'))
EMAIL_HOST_USER = get_env_variable('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = get_env_variable('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'noreply@beecatalog.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Configurações de arquivo
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Admin URL customizada
ADMIN_URL = get_env_variable('ADMIN_URL', 'admin/')
'''
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                f.write(settings_content)
            self.print_success(f"Arquivo {self.settings_file} criado")
            return True
        except Exception as e:
            self.print_error(f"Erro ao criar settings_production.py: {e}")
            return False
    
    def step_3_create_env_file(self):
        """Etapa 3: Criar arquivo de ambiente."""
        self.print_step(3, "Criar Arquivo de Ambiente")
        
        secret_key = self.generate_secret_key()
        
        env_content = f'''# Configurações de Produção - BeeCatalog
# ATENÇÃO: Mantenha este arquivo seguro e não commite no repositório
# Criado em: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Django Core
DJANGO_SETTINGS_MODULE=backbeecatalog.settings_production
DJANGO_ENV=production
DEBUG=False
SECRET_KEY={secret_key}

# Database (CONFIGURE ESTAS VARIÁVEIS)
DB_NAME=beecatalog_prod
DB_USER=beecatalog_user
DB_PASSWORD=ALTERE_ESTA_SENHA_AGORA
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Hosts permitidos (SUBSTITUA PELOS SEUS DOMÍNIOS)
ALLOWED_HOSTS=localhost,127.0.0.1,SEU-DOMINIO.com

# CORS (SUBSTITUA PELA URL DO SEU FRONTEND)
CORS_ALLOWED_ORIGINS=https://SEU-FRONTEND.com

# Email (CONFIGURE CONFORME SEU PROVEDOR)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app

# Sentry (OPCIONAL)
SENTRY_DSN=

# Admin URL customizada (OPCIONAL)
ADMIN_URL=admin/
'''
        
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            self.print_success(f"Arquivo {self.env_file} criado")
            self.print_warning("IMPORTANTE: Edite o arquivo .env.production e configure:")
            self.print_warning("- DB_PASSWORD")
            self.print_warning("- ALLOWED_HOSTS")
            self.print_warning("- CORS_ALLOWED_ORIGINS")
            self.print_warning("- EMAIL_* (se necessário)")
            return True
        except Exception as e:
            self.print_error(f"Erro ao criar .env.production: {e}")
            return False
    
    def step_4_install_security_packages(self):
        """Etapa 4: Instalar pacotes de segurança."""
        self.print_step(4, "Instalar Pacotes de Segurança")
        
        packages = [
            'psycopg2-binary',  # PostgreSQL adapter
            'django-ratelimit',
            'django-csp',
            'sentry-sdk[django]',
            'gunicorn',
            'django-redis',  # Redis cache
        ]
        
        for package in packages:
            print(f"Instalando {package}...")
            success, stdout, stderr = self.run_command(f"pip install {package}")
            if success:
                self.print_success(f"{package} instalado")
            else:
                self.print_warning(f"Falha ao instalar {package}: {stderr}")
        
        # Atualizar requirements.txt
        success, _, _ = self.run_command("pip freeze > requirements_security.txt")
        if success:
            self.print_success("requirements_security.txt atualizado")
        
        return True
    
    def step_5_create_deploy_script(self):
        """Etapa 5: Criar script de deploy."""
        self.print_step(5, "Criar Script de Deploy")
        
        deploy_script = '''#!/bin/bash
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
'''
        
        deploy_file = self.base_dir / 'deploy.sh'
        try:
            with open(deploy_file, 'w', encoding='utf-8') as f:
                f.write(deploy_script)
            
            # Tornar executável (Linux/Mac)
            if os.name != 'nt':
                os.chmod(deploy_file, 0o755)
            
            self.print_success(f"Script de deploy criado: {deploy_file}")
            return True
        except Exception as e:
            self.print_error(f"Erro ao criar script de deploy: {e}")
            return False
    
    def step_6_create_nginx_config(self):
        """Etapa 6: Criar configuração Nginx."""
        self.print_step(6, "Criar Configuração Nginx")
        
        nginx_config = '''# Configuração Nginx para BeeCatalog
# Salve este arquivo como: /etc/nginx/sites-available/beecatalog
# Ative com: sudo ln -s /etc/nginx/sites-available/beecatalog /etc/nginx/sites-enabled/

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name SEU-DOMINIO.com www.SEU-DOMINIO.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name SEU-DOMINIO.com www.SEU-DOMINIO.com;

    # SSL Configuration (CONFIGURE OS CAMINHOS DOS CERTIFICADOS)
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
        alias /path/to/your/static/files/;  # CONFIGURE O CAMINHO
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Django media files
    location /media/ {
        alias /path/to/your/media/files/;  # CONFIGURE O CAMINHO
        expires 1y;
        add_header Cache-Control "public";
    }

    # Rate limiting para API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Rate limiting para login
    location /admin/login/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
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

    # Security: Block access to sensitive files
    location ~ /\\. {
        deny all;
    }
    
    location ~ \\.(env|ini|conf)$ {
        deny all;
    }
}
'''
        
        nginx_file = self.base_dir / 'nginx_beecatalog.conf'
        try:
            with open(nginx_file, 'w', encoding='utf-8') as f:
                f.write(nginx_config)
            self.print_success(f"Configuração Nginx criada: {nginx_file}")
            self.print_warning("CONFIGURE os seguintes itens no arquivo:")
            self.print_warning("- server_name (seus domínios)")
            self.print_warning("- ssl_certificate e ssl_certificate_key")
            self.print_warning("- Caminhos para static e media")
            return True
        except Exception as e:
            self.print_error(f"Erro ao criar configuração Nginx: {e}")
            return False
    
    def check_configuration(self):
        """Verificar configurações atuais."""
        self.print_step("CHECK", "Verificar Configurações")
        
        checks = [
            (self.env_file.exists(), f"Arquivo .env.production existe"),
            (self.settings_file.exists(), f"Arquivo settings_production.py existe"),
            (self.logs_dir.exists(), f"Diretório logs existe"),
            ((self.base_dir / 'deploy.sh').exists(), f"Script deploy.sh existe"),
            ((self.base_dir / 'nginx_beecatalog.conf').exists(), f"Configuração Nginx existe"),
        ]
        
        all_good = True
        for check, description in checks:
            if check:
                self.print_success(description)
            else:
                self.print_error(description)
                all_good = False
        
        # Verificar se .env.production tem configurações críticas
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            critical_configs = [
                ('SECRET_KEY=', 'SECRET_KEY configurada'),
                ('DB_PASSWORD=ALTERE_ESTA_SENHA_AGORA', 'DB_PASSWORD precisa ser alterada'),
                ('ALLOWED_HOSTS=localhost,127.0.0.1,SEU-DOMINIO.com', 'ALLOWED_HOSTS precisa ser configurado'),
                ('CORS_ALLOWED_ORIGINS=https://SEU-FRONTEND.com', 'CORS_ALLOWED_ORIGINS precisa ser configurado'),
            ]
            
            for config, description in critical_configs:
                if config in content:
                    if 'precisa ser' in description:
                        self.print_warning(description)
                        all_good = False
                    else:
                        self.print_success(description)
        
        # Verificar Django
        print("\n🔍 Verificando Django...")
        if self.env_file.exists():
            # Tentar carregar variáveis de ambiente
            try:
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
                
                # Verificar configurações Django
                success, stdout, stderr = self.run_command(
                    "python manage.py check --settings=backbeecatalog.settings_production"
                )
                
                if success:
                    self.print_success("Configurações Django válidas")
                else:
                    if "psycopg2" in stderr or "psycopg" in stderr:
                        self.print_warning("PostgreSQL adapter (psycopg2) não instalado - Execute: python setup_security.py --step 4")
                    else:
                        self.print_warning(f"Problemas nas configurações Django: {stderr[:200]}...")
                    all_good = False
                    
            except Exception as e:
                self.print_warning(f"Erro ao verificar Django: {e}")
                all_good = False
        
        print(f"\n{'='*60}")
        if all_good:
            self.print_success("✅ TODAS AS CONFIGURAÇÕES ESTÃO CORRETAS!")
            print("\n📋 Próximos passos:")
            print("1. Configure seu banco PostgreSQL")
            print("2. Configure certificado SSL")
            print("3. Execute: ./deploy.sh")
        else:
            self.print_warning("⚠️  ALGUMAS CONFIGURAÇÕES PRECISAM SER AJUSTADAS")
            print("\n📋 Execute as etapas faltantes:")
            print("python setup_security.py --all")
        
        return all_good
    
    def run_all_steps(self):
        """Executar todas as etapas."""
        print("🚀 CONFIGURAÇÃO COMPLETA DE SEGURANÇA - BEECATALOG")
        print("="*60)
        
        steps = [
            self.step_1_prepare_environment,
            self.step_2_create_production_settings,
            self.step_3_create_env_file,
            self.step_4_install_security_packages,
            self.step_5_create_deploy_script,
            self.step_6_create_nginx_config,
        ]
        
        for i, step in enumerate(steps, 1):
            try:
                if not step():
                    self.print_error(f"Falha na etapa {i}")
                    return False
            except Exception as e:
                self.print_error(f"Erro na etapa {i}: {e}")
                return False
        
        print(f"\n{'='*60}")
        self.print_success("🎉 CONFIGURAÇÃO COMPLETA!")
        print("\n📋 Próximos passos:")
        print("1. Edite .env.production com suas configurações")
        print("2. Configure PostgreSQL e Redis")
        print("3. Configure certificado SSL")
        print("4. Execute: python setup_security.py --check")
        print("5. Execute: ./deploy.sh")
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Configuração Automatizada de Segurança BeeCatalog',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python setup_security.py --all          # Executar todas as etapas
  python setup_security.py --step 1       # Executar etapa específica
  python setup_security.py --check        # Verificar configurações
  
Etapas disponíveis:
  1 - Preparar ambiente
  2 - Criar configurações de produção
  3 - Criar arquivo de ambiente
  4 - Instalar pacotes de segurança
  5 - Criar script de deploy
  6 - Criar configuração Nginx
"""
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Executar todas as etapas')
    parser.add_argument('--step', type=int, choices=range(1, 7),
                       help='Executar etapa específica (1-6)')
    parser.add_argument('--check', action='store_true',
                       help='Verificar configurações atuais')
    
    args = parser.parse_args()
    
    if not any([args.all, args.step, args.check]):
        parser.print_help()
        return
    
    setup = SecuritySetup()
    
    try:
        if args.all:
            setup.run_all_steps()
        elif args.step:
            steps = {
                1: setup.step_1_prepare_environment,
                2: setup.step_2_create_production_settings,
                3: setup.step_3_create_env_file,
                4: setup.step_4_install_security_packages,
                5: setup.step_5_create_deploy_script,
                6: setup.step_6_create_nginx_config,
            }
            steps[args.step]()
        elif args.check:
            setup.check_configuration()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()