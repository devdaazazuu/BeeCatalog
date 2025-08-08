#!/usr/bin/env python3
"""
Script de Configuração de Segurança para BeeCatalog

Este script ajuda a implementar as configurações de segurança recomendadas
para o ambiente de produção do BeeCatalog.

Uso:
    python security_config.py --environment production
    python security_config.py --check-config
    python security_config.py --generate-secret
"""

import os
import secrets
import string
import argparse
from pathlib import Path


def generate_secret_key(length=50):
    """Gera uma SECRET_KEY segura para Django."""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_production_env():
    """Cria arquivo .env com configurações de produção seguras."""
    env_content = f"""# Configurações de Produção - BeeCatalog
# ATENÇÃO: Mantenha este arquivo seguro e não commite no repositório

# Django Core
DJANGO_SETTINGS_MODULE=backbeecatalog.settings
DEBUG=False
SECRET_KEY={generate_secret_key()}

# Segurança HTTPS
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY

# Cookies
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Strict
CSRF_COOKIE_SAMESITE=Strict

# Database
DB_NAME=beecatalog_prod
DB_USER=beecatalog_user
DB_PASSWORD=CHANGE_THIS_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email (configure conforme seu provedor)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Sentry (opcional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Allowed Hosts (adicione seus domínios)
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# CORS (configure conforme necessário)
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
"""
    
    env_file = Path('.env.production')
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Arquivo {env_file} criado com configurações de produção.")
    print("⚠️  IMPORTANTE: Revise e ajuste as configurações antes de usar em produção.")
    print("⚠️  Especialmente: DB_PASSWORD, EMAIL_*, SENTRY_DSN, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS")


def create_security_settings():
    """Cria arquivo com configurações de segurança para Django."""
    security_content = """
# Configurações de Segurança para Produção
# Adicione estas configurações ao seu settings.py

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

# Segurança HTTPS
SECURE_SSL_REDIRECT = get_env_variable('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if SECURE_SSL_REDIRECT else None
SESSION_COOKIE_SECURE = get_env_variable('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = get_env_variable('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = int(get_env_variable('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_env_variable('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = get_env_variable('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = get_env_variable('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = get_env_variable('SECURE_BROWSER_XSS_FILTER', 'True').lower() == 'true'
X_FRAME_OPTIONS = get_env_variable('X_FRAME_OPTIONS', 'DENY')

# Cookies
SESSION_COOKIE_HTTPONLY = get_env_variable('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
CSRF_COOKIE_HTTPONLY = get_env_variable('CSRF_COOKIE_HTTPONLY', 'True').lower() == 'true'
SESSION_COOKIE_SAMESITE = get_env_variable('SESSION_COOKIE_SAMESITE', 'Strict')
CSRF_COOKIE_SAMESITE = get_env_variable('CSRF_COOKIE_SAMESITE', 'Strict')

# Timeout de sessão (30 minutos)
SESSION_COOKIE_AGE = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Logging de Segurança
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
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
            'formatter': 'simple',
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

# Rate Limiting (se usando django-ratelimit)
RATELIMIT_ENABLE = True

# Content Security Policy (se usando django-csp)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# Configurações de Email Seguras
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = get_env_variable('EMAIL_HOST_USER', 'noreply@beecatalog.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Configurações de Arquivo
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Configurações de Admin
ADMIN_URL = get_env_variable('ADMIN_URL', 'admin/')
"""
    
    security_file = Path('security_settings.py')
    with open(security_file, 'w') as f:
        f.write(security_content)
    
    print(f"✅ Arquivo {security_file} criado com configurações de segurança.")
    print("📝 Integre estas configurações ao seu settings.py")


def check_security_config():
    """Verifica configurações de segurança atuais."""
    print("🔍 Verificando configurações de segurança...\n")
    
    # Verificar se DEBUG está desabilitado
    debug = os.getenv('DEBUG', 'True')
    if debug.lower() == 'true':
        print("❌ DEBUG=True (deve ser False em produção)")
    else:
        print("✅ DEBUG=False")
    
    # Verificar SECRET_KEY
    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 50:
        print("❌ SECRET_KEY muito curta (deve ter pelo menos 50 caracteres)")
    elif secret_key.startswith('django-insecure-'):
        print("❌ SECRET_KEY insegura (gerada automaticamente pelo Django)")
    else:
        print("✅ SECRET_KEY adequada")
    
    # Verificar HTTPS
    ssl_redirect = os.getenv('SECURE_SSL_REDIRECT', 'False')
    if ssl_redirect.lower() != 'true':
        print("❌ SECURE_SSL_REDIRECT não habilitado")
    else:
        print("✅ SECURE_SSL_REDIRECT habilitado")
    
    # Verificar cookies seguros
    session_secure = os.getenv('SESSION_COOKIE_SECURE', 'False')
    csrf_secure = os.getenv('CSRF_COOKIE_SECURE', 'False')
    
    if session_secure.lower() != 'true':
        print("❌ SESSION_COOKIE_SECURE não habilitado")
    else:
        print("✅ SESSION_COOKIE_SECURE habilitado")
    
    if csrf_secure.lower() != 'true':
        print("❌ CSRF_COOKIE_SECURE não habilitado")
    else:
        print("✅ CSRF_COOKIE_SECURE habilitado")
    
    # Verificar HSTS
    hsts_seconds = os.getenv('SECURE_HSTS_SECONDS', '0')
    if int(hsts_seconds) == 0:
        print("❌ SECURE_HSTS_SECONDS não configurado")
    else:
        print(f"✅ SECURE_HSTS_SECONDS configurado ({hsts_seconds} segundos)")
    
    print("\n📋 Resumo: Execute 'python security_config.py --environment production' para gerar configurações seguras.")


def main():
    parser = argparse.ArgumentParser(description='Configuração de Segurança BeeCatalog')
    parser.add_argument('--environment', choices=['production'], 
                       help='Gerar configurações para ambiente específico')
    parser.add_argument('--check-config', action='store_true',
                       help='Verificar configurações de segurança atuais')
    parser.add_argument('--generate-secret', action='store_true',
                       help='Gerar nova SECRET_KEY')
    
    args = parser.parse_args()
    
    if args.environment == 'production':
        print("🔧 Gerando configurações de produção...")
        create_production_env()
        create_security_settings()
        print("\n✅ Configurações geradas com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Revise o arquivo .env.production")
        print("2. Integre security_settings.py ao seu settings.py")
        print("3. Configure seu servidor web (nginx/apache) para HTTPS")
        print("4. Execute 'python manage.py check --deploy' para verificar")
    
    elif args.check_config:
        check_security_config()
    
    elif args.generate_secret:
        secret = generate_secret_key()
        print(f"🔑 Nova SECRET_KEY gerada:")
        print(f"SECRET_KEY={secret}")
        print("\n⚠️  Mantenha esta chave segura e não a compartilhe!")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()