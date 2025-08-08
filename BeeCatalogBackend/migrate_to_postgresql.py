#!/usr/bin/env python
"""
Script de migração para PostgreSQL com otimizações.
Este script configura o banco PostgreSQL e cria índices otimizados.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.db import connection
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backbeecatalog.settings')
django.setup()

def create_optimized_indexes():
    """
    Cria índices otimizados para melhorar a performance.
    """
    print("Criando índices otimizados...")
    
    with connection.cursor() as cursor:
        # Índices para tabelas do Celery
        indexes = [
            # Índices para django_celery_results_taskresult
            "CREATE INDEX IF NOT EXISTS idx_taskresult_status ON django_celery_results_taskresult(status);",
            "CREATE INDEX IF NOT EXISTS idx_taskresult_date_created ON django_celery_results_taskresult(date_created);",
            "CREATE INDEX IF NOT EXISTS idx_taskresult_date_done ON django_celery_results_taskresult(date_done);",
            "CREATE INDEX IF NOT EXISTS idx_taskresult_task_name ON django_celery_results_taskresult(task_name);",
            
            # Índices compostos para consultas comuns
            "CREATE INDEX IF NOT EXISTS idx_taskresult_status_created ON django_celery_results_taskresult(status, date_created);",
            "CREATE INDEX IF NOT EXISTS idx_taskresult_name_status ON django_celery_results_taskresult(task_name, status);",
            
            # Índices para sessões Django (se usando banco para sessões)
            "CREATE INDEX IF NOT EXISTS idx_session_expire_date ON django_session(expire_date);",
            
            # Índices para logs (se houver tabela de logs)
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp) WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'logs');",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✓ Índice criado: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'índice'}")
            except Exception as e:
                print(f"⚠ Erro ao criar índice: {e}")
    
    print("Índices otimizados criados com sucesso!")

def optimize_postgresql_settings():
    """
    Aplica configurações otimizadas no PostgreSQL.
    """
    print("Aplicando configurações otimizadas do PostgreSQL...")
    
    with connection.cursor() as cursor:
        # Configurações de performance
        optimizations = [
            # Configurações de memória
            "ALTER SYSTEM SET shared_buffers = '256MB';",
            "ALTER SYSTEM SET effective_cache_size = '1GB';",
            "ALTER SYSTEM SET work_mem = '4MB';",
            "ALTER SYSTEM SET maintenance_work_mem = '64MB';",
            
            # Configurações de checkpoint
            "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
            "ALTER SYSTEM SET wal_buffers = '16MB';",
            
            # Configurações de conexão
            "ALTER SYSTEM SET max_connections = 100;",
            
            # Configurações de logging
            "ALTER SYSTEM SET log_min_duration_statement = 1000;",  # Log queries > 1s
            "ALTER SYSTEM SET log_checkpoints = on;",
            "ALTER SYSTEM SET log_connections = on;",
            "ALTER SYSTEM SET log_disconnections = on;",
        ]
        
        for setting in optimizations:
            try:
                cursor.execute(setting)
                print(f"✓ Configuração aplicada: {setting.split('SET ')[1].split(' =')[0]}")
            except Exception as e:
                print(f"⚠ Erro ao aplicar configuração: {e}")
        
        # Recarregar configurações
        try:
            cursor.execute("SELECT pg_reload_conf();")
            print("✓ Configurações recarregadas")
        except Exception as e:
            print(f"⚠ Erro ao recarregar configurações: {e}")
    
    print("Configurações otimizadas aplicadas!")

def create_monitoring_views():
    """
    Cria views para monitoramento do sistema.
    """
    print("Criando views de monitoramento...")
    
    with connection.cursor() as cursor:
        views = [
            # View para monitorar tasks do Celery
            """
            CREATE OR REPLACE VIEW v_celery_task_stats AS
            SELECT 
                task_name,
                status,
                COUNT(*) as count,
                AVG(EXTRACT(EPOCH FROM (date_done - date_created))) as avg_duration_seconds,
                MIN(date_created) as first_task,
                MAX(date_done) as last_completed
            FROM django_celery_results_taskresult 
            WHERE date_created >= NOW() - INTERVAL '24 hours'
            GROUP BY task_name, status
            ORDER BY task_name, status;
            """,
            
            # View para monitorar performance de tasks
            """
            CREATE OR REPLACE VIEW v_celery_performance AS
            SELECT 
                DATE_TRUNC('hour', date_created) as hour,
                task_name,
                COUNT(*) as tasks_count,
                COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as success_count,
                COUNT(CASE WHEN status = 'FAILURE' THEN 1 END) as failure_count,
                AVG(EXTRACT(EPOCH FROM (date_done - date_created))) as avg_duration
            FROM django_celery_results_taskresult 
            WHERE date_created >= NOW() - INTERVAL '7 days'
            GROUP BY DATE_TRUNC('hour', date_created), task_name
            ORDER BY hour DESC, task_name;
            """,
            
            # View para monitorar conexões ativas
            """
            CREATE OR REPLACE VIEW v_active_connections AS
            SELECT 
                datname as database,
                usename as username,
                application_name,
                client_addr,
                state,
                COUNT(*) as connection_count
            FROM pg_stat_activity 
            WHERE state IS NOT NULL
            GROUP BY datname, usename, application_name, client_addr, state
            ORDER BY connection_count DESC;
            """
        ]
        
        for view_sql in views:
            try:
                cursor.execute(view_sql)
                view_name = view_sql.split('VIEW ')[1].split(' AS')[0]
                print(f"✓ View criada: {view_name}")
            except Exception as e:
                print(f"⚠ Erro ao criar view: {e}")
    
    print("Views de monitoramento criadas!")

def run_migration():
    """
    Executa a migração completa para PostgreSQL.
    """
    print("=== MIGRAÇÃO PARA POSTGRESQL ===")
    print("Iniciando migração do BeeCatalog para PostgreSQL...")
    
    try:
        # 1. Executar migrações Django
        print("\n1. Executando migrações Django...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrações Django concluídas")
        
        # 2. Criar índices otimizados
        print("\n2. Criando índices otimizados...")
        create_optimized_indexes()
        
        # 3. Aplicar configurações otimizadas
        print("\n3. Aplicando configurações otimizadas...")
        optimize_postgresql_settings()
        
        # 4. Criar views de monitoramento
        print("\n4. Criando views de monitoramento...")
        create_monitoring_views()
        
        # 5. Verificar conexão e configurações
        print("\n5. Verificando configurações...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✓ PostgreSQL conectado: {version}")
            
            cursor.execute("SELECT current_database();")
            database = cursor.fetchone()[0]
            print(f"✓ Banco de dados ativo: {database}")
            
            cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            migrations_count = cursor.fetchone()[0]
            print(f"✓ Migrações aplicadas: {migrations_count}")
        
        print("\n=== MIGRAÇÃO CONCLUÍDA COM SUCESSO! ===")
        print("\nPróximos passos:")
        print("1. Carregue os dados do backup: python manage.py loaddata backup.json")
        print("2. Inicie o Redis: redis-server")
        print("3. Inicie os workers Celery:")
        print("   - celery -A backbeecatalog worker -Q spreadsheet --concurrency=4")
        print("   - celery -A backbeecatalog worker -Q scraping --concurrency=2")
        print("   - celery -A backbeecatalog worker -Q ai --concurrency=3")
        print("4. Inicie o servidor Django: python manage.py runserver")
        
    except Exception as e:
        print(f"\n❌ ERRO na migração: {e}")
        print("Verifique as configurações do banco de dados no settings.py")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()