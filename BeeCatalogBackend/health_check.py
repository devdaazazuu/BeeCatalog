#!/usr/bin/env python
"""
Script de verificação de saúde do sistema BeeCatalog otimizado.
Verifica todos os componentes: PostgreSQL, Redis, Celery, Cache, etc.
"""

import os
import sys
import json
import time
import django
from datetime import datetime
from django.core.management import execute_from_command_line
from django.db import connection
from django.core.cache import cache
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backbeecatalog.settings')
django.setup()

def check_database():
    """
    Verifica a conexão e performance do PostgreSQL.
    """
    print("🔍 Verificando PostgreSQL...")
    
    try:
        with connection.cursor() as cursor:
            # Teste de conexão
            start_time = time.time()
            cursor.execute("SELECT 1;")
            response_time = (time.time() - start_time) * 1000
            
            # Informações do banco
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database();")
            database = cursor.fetchone()[0]
            
            # Estatísticas de conexão
            cursor.execute("""
                SELECT count(*) as active_connections,
                       max_conn.setting as max_connections
                FROM pg_stat_activity, 
                     (SELECT setting FROM pg_settings WHERE name = 'max_connections') max_conn
                WHERE state = 'active';
            """)
            conn_stats = cursor.fetchone()
            
            # Tamanho do banco
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
            """)
            db_size = cursor.fetchone()[0]
            
            print(f"  ✅ PostgreSQL conectado: {version.split(',')[0]}")
            print(f"  ✅ Banco de dados: {database}")
            print(f"  ✅ Tempo de resposta: {response_time:.2f}ms")
            print(f"  ✅ Conexões ativas: {conn_stats[0]}/{conn_stats[1]}")
            print(f"  ✅ Tamanho do banco: {db_size}")
            
            return True, {
                'status': 'healthy',
                'response_time_ms': response_time,
                'active_connections': conn_stats[0],
                'max_connections': conn_stats[1],
                'database_size': db_size
            }
            
    except Exception as e:
        print(f"  ❌ Erro PostgreSQL: {e}")
        return False, {'status': 'error', 'error': str(e)}

def check_redis():
    """
    Verifica a conexão e performance do Redis.
    """
    print("\n🔍 Verificando Redis...")
    
    # Pular verificação do Redis em modo DEBUG (usa cache local)
    if settings.DEBUG:
        print("✅ Redis: Pulando verificação (modo DEBUG - usando cache local)")
        return True
    
    try:
        import redis
        
        # Conectar ao Redis
        redis_client = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])
        
        # Teste de ping
        start_time = time.time()
        pong = redis_client.ping()
        response_time = (time.time() - start_time) * 1000
        
        # Informações do Redis
        info = redis_client.info()
        
        # Teste de cache Django
        test_key = f"health_check_{int(time.time())}"
        cache.set(test_key, "test_value", 30)
        cached_value = cache.get(test_key)
        cache.delete(test_key)
        
        print(f"  ✅ Redis conectado: v{info['redis_version']}")
        print(f"  ✅ Tempo de resposta: {response_time:.2f}ms")
        print(f"  ✅ Memória usada: {info['used_memory_human']}")
        print(f"  ✅ Conexões ativas: {info['connected_clients']}")
        print(f"  ✅ Cache Django: {'OK' if cached_value == 'test_value' else 'ERRO'}")
        
        return True, {
            'status': 'healthy',
            'response_time_ms': response_time,
            'memory_used': info['used_memory_human'],
            'connected_clients': info['connected_clients'],
            'cache_test': cached_value == 'test_value'
        }
        
    except Exception as e:
        print(f"  ❌ Erro Redis: {e}")
        return False, {'status': 'error', 'error': str(e)}

def check_celery():
    """
    Verifica o status dos workers Celery.
    """
    print("\n🔍 Verificando Celery...")
    
    try:
        from celery import Celery
        from backbeecatalog.celery import app
        
        # Verificar workers ativos
        inspect = app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        
        if not active_workers:
            print("  ⚠️  Nenhum worker Celery ativo")
            return False, {'status': 'no_workers', 'workers': {}}
        
        print(f"  ✅ Workers ativos: {len(active_workers)}")
        
        worker_info = {}
        for worker_name, worker_stats in (stats or {}).items():
            queue_info = worker_stats.get('pool', {})
            print(f"    - {worker_name}: {queue_info.get('processes', 'N/A')} processos")
            worker_info[worker_name] = {
                'processes': queue_info.get('processes', 0),
                'max_concurrency': queue_info.get('max-concurrency', 0)
            }
        
        # Verificar filas
        active_queues = inspect.active_queues()
        if active_queues:
            print("  ✅ Filas ativas:")
            for worker, queues in active_queues.items():
                for queue in queues:
                    print(f"    - {queue['name']}")
        
        return True, {
            'status': 'healthy',
            'active_workers': len(active_workers),
            'workers': worker_info,
            'queues': list(active_queues.keys()) if active_queues else []
        }
        
    except Exception as e:
        print(f"  ❌ Erro Celery: {e}")
        return False, {'status': 'error', 'error': str(e)}

def check_ai_cache():
    """
    Verifica o sistema de cache inteligente para IA.
    """
    print("\n🔍 Verificando Cache IA...")
    
    try:
        from api.cache_utils import get_cache_stats, get_or_cache_ai_response
        
        # Obter estatísticas do cache
        stats = get_cache_stats()
        
        # Teste do cache IA
        test_prompt = "test_health_check"
        test_context = {"test": "health_check"}
        
        def dummy_ai_function():
            return {"result": "test_response", "tokens": 10}
        
        # Primeira chamada (deve cachear)
        start_time = time.time()
        result1 = get_or_cache_ai_response(
            test_prompt, dummy_ai_function, test_context, cache_ttl=60
        )
        first_call_time = (time.time() - start_time) * 1000
        
        # Segunda chamada (deve usar cache)
        start_time = time.time()
        result2 = get_or_cache_ai_response(
            test_prompt, dummy_ai_function, test_context, cache_ttl=60
        )
        second_call_time = (time.time() - start_time) * 1000
        
        cache_hit = second_call_time < first_call_time / 2
        
        print(f"  ✅ Cache IA funcionando: {'SIM' if cache_hit else 'NÃO'}")
        print(f"  ✅ Primeira chamada: {first_call_time:.2f}ms")
        print(f"  ✅ Segunda chamada: {second_call_time:.2f}ms")
        print(f"  ✅ Estatísticas: {stats}")
        
        return True, {
            'status': 'healthy',
            'cache_hit': cache_hit,
            'first_call_ms': first_call_time,
            'second_call_ms': second_call_time,
            'stats': stats
        }
        
    except Exception as e:
        print(f"  ❌ Erro Cache IA: {e}")
        return False, {'status': 'error', 'error': str(e)}

def check_external_services():
    """
    Verifica serviços externos (Sentry, APIs, etc.).
    """
    print("\n🔍 Verificando Serviços Externos...")
    
    results = {}
    
    # Verificar Sentry
    try:
        import sentry_sdk
        sentry_sdk.capture_message("Health check test", level="info")
        print("  ✅ Sentry: Configurado")
        results['sentry'] = {'status': 'configured'}
    except Exception as e:
        print(f"  ⚠️  Sentry: {e}")
        results['sentry'] = {'status': 'error', 'error': str(e)}
    
    # Verificar Google AI (se configurado)
    try:
        google_api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if google_api_key:
            print("  ✅ Google AI: API Key configurada")
            results['google_ai'] = {'status': 'configured'}
        else:
            print("  ⚠️  Google AI: API Key não configurada")
            results['google_ai'] = {'status': 'not_configured'}
    except Exception as e:
        print(f"  ❌ Google AI: {e}")
        results['google_ai'] = {'status': 'error', 'error': str(e)}
    
    return True, results

def generate_health_report():
    """
    Gera relatório completo de saúde do sistema.
    """
    print("\n📊 Gerando Relatório de Saúde...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'system': 'BeeCatalog',
        'version': '2.0-optimized',
        'components': {}
    }
    
    # Verificar todos os componentes
    components = [
        ('database', check_database),
        ('redis', check_redis),
        ('celery', check_celery),
        ('ai_cache', check_ai_cache),
        ('external_services', check_external_services)
    ]
    
    overall_health = True
    
    for component_name, check_function in components:
        try:
            is_healthy, component_data = check_function()
            report['components'][component_name] = component_data
            if not is_healthy:
                overall_health = False
        except Exception as e:
            report['components'][component_name] = {
                'status': 'error',
                'error': str(e)
            }
            overall_health = False
    
    report['overall_status'] = 'healthy' if overall_health else 'degraded'
    
    # Salvar relatório
    report_file = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 Relatório salvo: {report_file}")
    
    return report, overall_health

def main():
    """
    Função principal do health check.
    """
    print("🏥 HEALTH CHECK - BeeCatalog Otimizado")
    print("=" * 50)
    
    try:
        report, is_healthy = generate_health_report()
        
        print("\n" + "=" * 50)
        if is_healthy:
            print("🎉 SISTEMA SAUDÁVEL - Todos os componentes funcionando!")
            print("\n✅ Componentes verificados:")
            for component, data in report['components'].items():
                status = data.get('status', 'unknown')
                emoji = "✅" if status == 'healthy' or status == 'configured' else "⚠️" if status == 'not_configured' else "❌"
                print(f"  {emoji} {component.replace('_', ' ').title()}: {status}")
        else:
            print("⚠️  SISTEMA COM PROBLEMAS - Verifique os componentes acima")
            print("\n❌ Componentes com problemas:")
            for component, data in report['components'].items():
                status = data.get('status', 'unknown')
                if status not in ['healthy', 'configured']:
                    print(f"  ❌ {component.replace('_', ' ').title()}: {status}")
                    if 'error' in data:
                        print(f"     Erro: {data['error']}")
        
        print("\n📊 Próximos passos:")
        print("  1. Acesse Grafana: http://localhost:3000")
        print("  2. Monitore Celery: http://localhost:5555")
        print("  3. Verifique métricas: http://localhost:9090")
        
        return 0 if is_healthy else 1
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO no health check: {e}")
        return 2

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)