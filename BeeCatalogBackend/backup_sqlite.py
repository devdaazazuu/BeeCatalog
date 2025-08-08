#!/usr/bin/env python
"""
Script de backup dos dados SQLite antes da migração para PostgreSQL.
Este script cria um backup completo dos dados existentes.
"""

import os
import sys
import json
import django
from datetime import datetime
from django.core.management import execute_from_command_line
from django.core import serializers
from django.apps import apps

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backbeecatalog.settings')
django.setup()

def create_backup():
    """
    Cria backup completo dos dados SQLite.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'backup_{timestamp}'
    
    print(f"=== BACKUP DOS DADOS SQLITE ===")
    print(f"Criando backup em: {backup_dir}/")
    
    # Criar diretório de backup
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # 1. Backup completo usando dumpdata
        print("\n1. Criando backup completo...")
        backup_file = os.path.join(backup_dir, 'full_backup.json')
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            execute_from_command_line(['manage.py', 'dumpdata', '--output', backup_file, '--indent', '2'])
        
        print(f"✓ Backup completo salvo: {backup_file}")
        
        # 2. Backup por aplicação
        print("\n2. Criando backups por aplicação...")
        
        # Obter todas as aplicações instaladas
        installed_apps = [app.label for app in apps.get_app_configs() 
                         if not app.label.startswith('django') and 
                         not app.label.startswith('rest_framework') and
                         not app.label.startswith('corsheaders') and
                         not app.label.startswith('django_celery')]
        
        for app_label in installed_apps:
            try:
                app_backup_file = os.path.join(backup_dir, f'{app_label}_backup.json')
                execute_from_command_line(['manage.py', 'dumpdata', app_label, '--output', app_backup_file, '--indent', '2'])
                print(f"✓ Backup da aplicação {app_label}: {app_backup_file}")
            except Exception as e:
                print(f"⚠ Erro no backup da aplicação {app_label}: {e}")
        
        # 3. Backup das configurações
        print("\n3. Salvando informações do sistema...")
        
        system_info = {
            'backup_timestamp': timestamp,
            'django_version': django.get_version(),
            'python_version': sys.version,
            'installed_apps': installed_apps,
            'database_engine': 'sqlite3',
            'backup_method': 'dumpdata'
        }
        
        info_file = os.path.join(backup_dir, 'system_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(system_info, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Informações do sistema salvas: {info_file}")
        
        # 4. Copiar arquivo SQLite original
        print("\n4. Copiando arquivo SQLite original...")
        
        import shutil
        sqlite_file = 'db.sqlite3'
        if os.path.exists(sqlite_file):
            backup_sqlite = os.path.join(backup_dir, 'db_original.sqlite3')
            shutil.copy2(sqlite_file, backup_sqlite)
            print(f"✓ Arquivo SQLite copiado: {backup_sqlite}")
        else:
            print("⚠ Arquivo db.sqlite3 não encontrado")
        
        # 5. Criar script de restauração
        print("\n5. Criando script de restauração...")
        
        restore_script = f"""
#!/usr/bin/env python
# Script de restauração do backup {timestamp}

import os
import sys
import django
from django.core.management import execute_from_command_line

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backbeecatalog.settings')
django.setup()

def restore_backup():
    print("=== RESTAURAÇÃO DO BACKUP {timestamp} ===")
    
    try:
        # Executar migrações primeiro
        print("1. Executando migrações...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Carregar dados
        print("2. Carregando dados do backup...")
        execute_from_command_line(['manage.py', 'loaddata', 'full_backup.json'])
        
        print("✓ Backup restaurado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na restauração: {{e}}")
        sys.exit(1)

if __name__ == '__main__':
    restore_backup()
"""
        
        restore_file = os.path.join(backup_dir, 'restore_backup.py')
        with open(restore_file, 'w', encoding='utf-8') as f:
            f.write(restore_script)
        
        print(f"✓ Script de restauração criado: {restore_file}")
        
        # 6. Verificar integridade do backup
        print("\n6. Verificando integridade do backup...")
        
        backup_size = os.path.getsize(backup_file)
        print(f"✓ Tamanho do backup: {backup_size / 1024:.2f} KB")
        
        # Contar registros no backup
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
            record_count = len(backup_data)
        
        print(f"✓ Registros no backup: {record_count}")
        
        print("\n=== BACKUP CONCLUÍDO COM SUCESSO! ===")
        print(f"\nArquivos criados em: {backup_dir}/")
        print("- full_backup.json: Backup completo dos dados")
        print("- *_backup.json: Backups por aplicação")
        print("- system_info.json: Informações do sistema")
        print("- db_original.sqlite3: Cópia do arquivo SQLite original")
        print("- restore_backup.py: Script para restaurar o backup")
        
        print("\nPara restaurar o backup:")
        print(f"cd {backup_dir} && python restore_backup.py")
        
        return backup_dir
        
    except Exception as e:
        print(f"\n❌ ERRO no backup: {e}")
        sys.exit(1)

def verify_data_integrity():
    """
    Verifica a integridade dos dados antes do backup.
    """
    print("\n=== VERIFICAÇÃO DE INTEGRIDADE ===")
    
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Verificar tabelas principais
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"✓ Tabelas encontradas: {len(tables)}")
        
        # Contar registros por tabela
        total_records = 0
        for table in tables:
            if not table.startswith('django_') and not table.startswith('sqlite_'):
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    total_records += count
                    if count > 0:
                        print(f"  - {table}: {count} registros")
                except Exception as e:
                    print(f"  ⚠ Erro ao contar {table}: {e}")
        
        print(f"✓ Total de registros: {total_records}")
        
        return total_records > 0

if __name__ == '__main__':
    # Verificar integridade dos dados
    if verify_data_integrity():
        # Criar backup
        backup_dir = create_backup()
        print(f"\n🎉 Backup criado com sucesso em: {backup_dir}")
    else:
        print("⚠ Nenhum dado encontrado para backup")