#!/usr/bin/env python
# exemplo_uso_importacao.py

"""
Exemplo Prático: Como Usar o Sistema de Importação de Planilhas

Este script demonstra como usar o sistema de importação de planilhas
do BeeCatalog para acelerar o processo de catalogação de produtos.
"""

import os
import sys
import django
import pandas as pd
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backbeecatalog.settings')
django.setup()

def criar_planilha_exemplo():
    """Cria uma planilha de exemplo para demonstração."""
    print("📝 Criando planilha de exemplo...")
    
    # Dados de exemplo
    produtos_exemplo = {
        'SKU': [
            'SMART001', 'FONE002', 'CAM003', 'TABLET004', 'WATCH005'
        ],
        'Título': [
            'Smartphone Galaxy Pro 128GB',
            'Fone Bluetooth Premium',
            'Camiseta Esportiva Dry-Fit',
            'Tablet 10 polegadas 64GB',
            'Smartwatch Fitness Tracker'
        ],
        'Descrição': [
            'Smartphone com tela de 6.5 polegadas, 128GB de armazenamento, câmera tripla de 64MP',
            'Fone de ouvido sem fio com cancelamento de ruído ativo e bateria de 30 horas',
            'Camiseta esportiva com tecnologia dry-fit para corrida e academia',
            'Tablet com tela HD de 10 polegadas, 64GB de armazenamento e Android 12',
            'Relógio inteligente com monitor cardíaco, GPS e resistência à água'
        ],
        'Preço': [
            899.99, 299.99, 79.99, 599.99, 399.99
        ],
        'Marca': [
            'TechCorp', 'AudioMax', 'SportWear', 'TabletPro', 'FitTech'
        ],
        'Categoria': [
            'Eletrônicos', 'Áudio', 'Roupas', 'Eletrônicos', 'Wearables'
        ],
        'Palavras-chave': [
            'smartphone, celular, android, câmera',
            'fone, bluetooth, sem fio, música',
            'camiseta, esporte, corrida, academia',
            'tablet, android, tela grande, portátil',
            'smartwatch, fitness, saúde, GPS'
        ],
        'Características': [
            'Tela 6.5"; 128GB armazenamento; Câmera 64MP; Bateria 4000mAh',
            'Bluetooth 5.0; Cancelamento ruído; Bateria 30h; Resistente água',
            'Tecido dry-fit; Respirável; Proteção UV; Tamanhos P-GG',
            'Tela 10" HD; Android 12; 64GB; Wi-Fi; Câmera 8MP',
            'Monitor cardíaco; GPS; Resistente água; Bateria 7 dias'
        ]
    }
    
    # Criar DataFrame
    df = pd.DataFrame(produtos_exemplo)
    
    # Salvar como Excel
    arquivo_exemplo = 'produtos_exemplo.xlsx'
    df.to_excel(arquivo_exemplo, index=False, sheet_name='Produtos')
    
    print(f"✅ Planilha criada: {arquivo_exemplo}")
    print(f"   - {len(df)} produtos de exemplo")
    print(f"   - {len(df.columns)} colunas mapeadas")
    
    return arquivo_exemplo

def demonstrar_preview(arquivo):
    """Demonstra como fazer preview da planilha."""
    print("\n🔍 DEMONSTRAÇÃO: Preview da Planilha")
    print("=" * 50)
    
    from api.spreadsheet_importer import spreadsheet_importer
    
    try:
        # Fazer preview
        preview = spreadsheet_importer.preview_import(arquivo, sample_size=3)
        
        print(f"📊 Estatísticas:")
        print(f"   - Total de linhas: {preview['total_rows']}")
        print(f"   - Linhas válidas: {preview['valid_rows']}")
        print(f"   - Produtos identificados: {preview['identified_products']}")
        
        print(f"\n📋 Amostra de produtos:")
        for i, produto in enumerate(preview['sample_products'], 1):
            print(f"\n   Produto {i}:")
            for campo, valor in produto.items():
                if valor:
                    valor_display = str(valor)[:60] + '...' if len(str(valor)) > 60 else str(valor)
                    print(f"     {campo}: {valor_display}")
        
        if preview['errors']:
            print(f"\n⚠️  Erros encontrados: {len(preview['errors'])}")
            for erro in preview['errors'][:3]:
                print(f"     - {erro}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no preview: {e}")
        return False

def demonstrar_analise_colunas(arquivo):
    """Demonstra análise de colunas da planilha."""
    print("\n🔍 DEMONSTRAÇÃO: Análise de Colunas")
    print("=" * 50)
    
    from api.spreadsheet_importer import spreadsheet_importer
    
    try:
        # Ler planilha
        df = spreadsheet_importer.read_spreadsheet(arquivo)
        
        # Mapear colunas
        mapeamento = spreadsheet_importer.map_columns(df)
        
        print(f"📋 Informações da planilha:")
        print(f"   - Total de linhas: {len(df)}")
        print(f"   - Total de colunas: {len(df.columns)}")
        
        print(f"\n🗂️  Mapeamento de colunas:")
        for campo_padrao, coluna_original in mapeamento.items():
            if coluna_original:
                valores_nao_nulos = df[coluna_original].count()
                print(f"   {campo_padrao} ← {coluna_original} ({valores_nao_nulos} valores)")
        
        # Colunas não mapeadas
        colunas_nao_mapeadas = [col for col in df.columns if col not in mapeamento.values()]
        if colunas_nao_mapeadas:
            print(f"\n❓ Colunas não mapeadas:")
            for col in colunas_nao_mapeadas:
                print(f"   - {col}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        return False

def demonstrar_importacao(arquivo):
    """Demonstra importação para a memória."""
    print("\n📥 DEMONSTRAÇÃO: Importação para Memória")
    print("=" * 50)
    
    from api.spreadsheet_importer import spreadsheet_importer
    from api.memory_utils import get_memory_statistics
    
    try:
        # Estatísticas antes
        print("📊 Estatísticas ANTES da importação:")
        stats_antes = get_memory_statistics()
        print(f"   - Produtos na memória: {stats_antes.get('total_products_sample', 'N/A')}")
        
        # Importar
        print("\n🚀 Iniciando importação...")
        resultado = spreadsheet_importer.import_to_memory(
            arquivo, 
            force_update=True, 
            batch_size=10
        )
        
        print(f"\n✅ Importação concluída:")
        print(f"   - Produtos importados: {resultado['imported']}")
        print(f"   - Produtos atualizados: {resultado['updated']}")
        print(f"   - Produtos ignorados: {resultado['skipped']}")
        print(f"   - Erros: {resultado['errors']}")
        print(f"   - Total processado: {resultado['total_processed']}")
        
        if resultado['error_details']:
            print(f"\n⚠️  Detalhes dos erros:")
            for erro in resultado['error_details'][:3]:
                print(f"     - {erro}")
        
        # Estatísticas depois
        print("\n📊 Estatísticas DEPOIS da importação:")
        stats_depois = get_memory_statistics()
        print(f"   - Produtos na memória: {stats_depois.get('total_products_sample', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        print("   Nota: Isso é esperado se o Redis não estiver rodando.")
        print("   O sistema ainda funciona com backup local.")
        return False

def demonstrar_uso_memoria():
    """Demonstra como usar a memória após importação."""
    print("\n🧠 DEMONSTRAÇÃO: Uso da Memória Inteligente")
    print("=" * 50)
    
    from api.memory_utils import get_cached_content_or_generate
    from api.product_memory import ProductMemory
    
    try:
        memory = ProductMemory()
        
        # Listar alguns produtos na memória
        print("📋 Produtos na memória:")
        produtos = memory.list_products(limit=3)
        
        if produtos:
            for produto in produtos:
                print(f"   - {produto.get('identifier', 'N/A')}: {produto.get('title', 'Sem título')[:50]}...")
            
            # Demonstrar recuperação de conteúdo
            primeiro_produto = produtos[0]
            identifier = primeiro_produto.get('identifier')
            
            if identifier:
                print(f"\n🔄 Testando recuperação de conteúdo para: {identifier}")
                
                # Simular dados de produto
                product_data = {
                    'sku': identifier,
                    'title': primeiro_produto.get('title', 'Produto Teste'),
                    'description': 'Descrição de teste'
                }
                
                # Tentar recuperar conteúdo (isso usará a memória se disponível)
                print("   - Verificando se conteúdo já existe na memória...")
                conteudo_existente = memory.get_product_data(identifier)
                
                if conteudo_existente:
                    print("   ✅ Conteúdo encontrado na memória! (economia de tokens)")
                    print(f"   - Título: {conteudo_existente.get('title', 'N/A')[:50]}...")
                else:
                    print("   ℹ️  Conteúdo não encontrado na memória (seria gerado pela IA)")
        else:
            print("   ℹ️  Nenhum produto encontrado na memória")
            print("   Dica: Execute a importação primeiro")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao acessar memória: {e}")
        return False

def main():
    """Executa demonstração completa."""
    print("🎯 DEMONSTRAÇÃO COMPLETA: Sistema de Importação de Planilhas")
    print("=" * 70)
    print("\nEste exemplo mostra como usar o sistema para acelerar sua catalogação!")
    
    # Passo 1: Criar planilha de exemplo
    arquivo = criar_planilha_exemplo()
    
    try:
        # Passo 2: Preview
        if demonstrar_preview(arquivo):
            print("\n✅ Preview realizado com sucesso!")
        
        # Passo 3: Análise de colunas
        if demonstrar_analise_colunas(arquivo):
            print("\n✅ Análise de colunas realizada com sucesso!")
        
        # Passo 4: Importação
        if demonstrar_importacao(arquivo):
            print("\n✅ Importação realizada com sucesso!")
        
        # Passo 5: Uso da memória
        if demonstrar_uso_memoria():
            print("\n✅ Demonstração da memória realizada com sucesso!")
        
        # Instruções finais
        print("\n" + "=" * 70)
        print("🎉 DEMONSTRAÇÃO CONCLUÍDA!")
        print("\n📚 PRÓXIMOS PASSOS:")
        print("\n1. 📋 Use suas próprias planilhas:")
        print("   python manage.py import_spreadsheet sua_planilha.xlsx --preview")
        print("\n2. 🌐 Use a API REST:")
        print("   POST /api/spreadsheet/preview/ (com arquivo)")
        print("   POST /api/spreadsheet/import/ (com arquivo)")
        print("\n3. 📥 Baixe o template:")
        print("   GET /api/import/template/")
        print("\n4. 📖 Consulte a documentação:")
        print("   GUIA_IMPORTACAO_PLANILHAS.md")
        print("\n💡 BENEFÍCIOS:")
        print("   ✅ Economia massiva de tokens de IA")
        print("   ✅ Geração mais rápida de conteúdo")
        print("   ✅ Reutilização inteligente de dados")
        print("   ✅ Suporte a milhares de produtos")
        
    finally:
        # Limpar arquivo de exemplo
        if os.path.exists(arquivo):
            os.remove(arquivo)
            print(f"\n🧹 Arquivo de exemplo removido: {arquivo}")

if __name__ == '__main__':
    main()