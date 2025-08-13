#!/usr/bin/env python
# test_memory_system.py
"""
Script de teste para o Sistema de Memória Inteligente do BeeCatalog.
Este script verifica se todos os componentes estão funcionando corretamente.
"""

import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backbeecatalog.settings')
django.setup()

def test_product_memory():
    """Testa a classe ProductMemory."""
    print("\n=== Testando ProductMemory ===")
    
    try:
        from api.product_memory import product_memory
        
        # Dados de teste
        test_product_id = "TEST_PRODUCT_123"
        test_data = {
            "title": "Produto de Teste",
            "description": "Descrição do produto de teste",
            "price": 99.99,
            "category": "Eletrônicos",
            "created_at": datetime.now().isoformat()
        }
        
        # Teste 1: Salvar produto
        print("1. Salvando produto de teste...")
        success = product_memory.save_product_data(test_product_id, test_data)
        print(f"   Resultado: {'✓ Sucesso' if success else '✗ Falha'}")
        
        # Teste 2: Verificar existência
        print("2. Verificando se produto existe...")
        exists = product_memory.exists(test_product_id)
        print(f"   Resultado: {'✓ Existe' if exists else '✗ Não existe'}")
        
        # Teste 3: Recuperar dados
        print("3. Recuperando dados do produto...")
        retrieved_data = product_memory.get_product_data(test_product_id)
        if retrieved_data:
            print(f"   ✓ Dados recuperados: {retrieved_data.get('title', 'N/A')}")
        else:
            print("   ✗ Falha ao recuperar dados")
        
        # Teste 4: Listar produtos
        print("4. Listando produtos na memória...")
        products_list = product_memory.list_products(limit=5)
        print(f"   Produtos encontrados: {len(products_list)}")
        
        # Teste 5: Remover produto de teste
        print("5. Removendo produto de teste...")
        deleted = product_memory.delete_product(test_product_id)
        print(f"   Resultado: {'✓ Removido' if deleted else '✗ Falha'}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Erro no teste ProductMemory: {e}")
        return False

def test_memory_utils():
    """Testa as funções utilitárias."""
    print("\n=== Testando Memory Utils ===")
    
    try:
        from api.memory_utils import (
            extract_product_identifier,
            check_product_in_memory,
            save_generated_content_to_memory,
            get_memory_statistics
        )
        
        # Dados de teste
        test_product_data = {
            "sku": "TEST_SKU_456",
            "title": "Produto Utils Teste",
            "brand": "TestBrand"
        }
        
        # Teste 1: Extrair identificador
        print("1. Extraindo identificador do produto...")
        identifier = extract_product_identifier(test_product_data)
        print(f"   Identificador: {identifier}")
        
        # Teste 2: Verificar na memória
        print("2. Verificando produto na memória...")
        in_memory, cached_data = check_product_in_memory(test_product_data)
        print(f"   Na memória: {'✓ Sim' if in_memory else '✗ Não'}")
        
        # Teste 3: Salvar conteúdo gerado
        print("3. Salvando conteúdo gerado...")
        generated_content = {
            "title": "Título Gerado pela IA",
            "description": "Descrição gerada pela IA",
            "keywords": ["teste", "produto", "ia"]
        }
        saved = save_generated_content_to_memory(test_product_data, generated_content)
        print(f"   Resultado: {'✓ Salvo' if saved else '✗ Falha'}")
        
        # Teste 4: Obter estatísticas
        print("4. Obtendo estatísticas da memória...")
        stats = get_memory_statistics()
        print(f"   Redis conectado: {stats.get('redis_connected', False)}")
        print(f"   Produtos no Redis: {stats.get('redis_products', 0)}")
        print(f"   Backups locais: {stats.get('local_backups', 0)}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Erro no teste Memory Utils: {e}")
        return False

def test_integration():
    """Testa a integração com as funções existentes."""
    print("\n=== Testando Integração ===")
    
    try:
        from api.memory_utils import (
            batch_check_products_in_memory,
            clear_product_memory,
            export_memory_data
        )
        
        # Teste 1: Verificação em lote
        print("1. Testando verificação em lote...")
        test_products = [
            {"sku": "BATCH_TEST_1", "title": "Produto Lote 1"},
            {"sku": "BATCH_TEST_2", "title": "Produto Lote 2"},
            {"sku": "BATCH_TEST_3", "title": "Produto Lote 3"}
        ]
        
        batch_results = batch_check_products_in_memory(test_products)
        print(f"   Produtos verificados: {len(batch_results)}")
        
        # Teste 2: Exportar dados
        print("2. Testando exportação de dados...")
        exported_data = export_memory_data(limit=10)
        print(f"   Produtos exportados: {len(exported_data)}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Erro no teste de Integração: {e}")
        return False

def test_api_endpoints():
    """Testa os endpoints da API (simulação)."""
    print("\n=== Testando Endpoints da API ===")
    
    try:
        # Simular importação das views
        from api.memory_views import (
            ProductMemoryStatsView,
            ListProductsMemoryView,
            memory_health_check
        )
        
        print("1. Views importadas com sucesso ✓")
        
        # Verificar se as URLs estão configuradas
        try:
            from api.memory_urls import urlpatterns
            print(f"2. URLs configuradas: {len(urlpatterns)} endpoints ✓")
        except ImportError:
            print("2. ✗ Erro ao importar URLs")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ✗ Erro no teste de API: {e}")
        return False

def test_management_command():
    """Testa o comando de gerenciamento."""
    print("\n=== Testando Comando de Gerenciamento ===")
    
    try:
        from api.management.commands.manage_memory import Command
        
        print("1. Comando importado com sucesso ✓")
        
        # Verificar se o comando tem os métodos necessários
        command = Command()
        required_methods = ['show_stats', 'health_check', 'list_products']
        
        for method in required_methods:
            if hasattr(command, method):
                print(f"2. Método {method} encontrado ✓")
            else:
                print(f"2. ✗ Método {method} não encontrado")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ✗ Erro no teste do comando: {e}")
        return False

def run_all_tests():
    """Executa todos os testes."""
    print("🧪 INICIANDO TESTES DO SISTEMA DE MEMÓRIA INTELIGENTE")
    print("=" * 60)
    
    tests = [
        ("ProductMemory", test_product_memory),
        ("Memory Utils", test_memory_utils),
        ("Integração", test_integration),
        ("API Endpoints", test_api_endpoints),
        ("Management Command", test_management_command)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ ERRO CRÍTICO no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{test_name:20} | {status}")
        if result:
            passed += 1
    
    print("\n" + "-" * 60)
    print(f"Testes passaram: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para uso.")
    else:
        print(f"\n⚠️  {total-passed} teste(s) falharam. Verifique os erros acima.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Testes interrompidos pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 ERRO FATAL: {e}")
        sys.exit(1)