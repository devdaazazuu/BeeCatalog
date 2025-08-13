# api/import_views.py

import json
import logging
import os
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .spreadsheet_importer import spreadsheet_importer

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class SpreadsheetPreviewView(View):
    """
    View para fazer preview de uma planilha antes da importação.
    """
    
    def post(self, request):
        try:
            # Verificar se arquivo foi enviado
            if 'file' not in request.FILES:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Nenhum arquivo foi enviado'
                }, status=400)
            
            uploaded_file = request.FILES['file']
            sheet_name = request.POST.get('sheet_name')
            sample_size = int(request.POST.get('sample_size', 5))
            
            # Validar tipo de arquivo
            if not any(uploaded_file.name.lower().endswith(ext) for ext in spreadsheet_importer.supported_formats):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Formato não suportado. Use: {", ".join(spreadsheet_importer.supported_formats)}'
                }, status=400)
            
            # Salvar arquivo temporariamente
            temp_path = default_storage.save(
                f'temp_imports/{uploaded_file.name}',
                ContentFile(uploaded_file.read())
            )
            
            try:
                # Fazer preview
                preview_data = spreadsheet_importer.preview_import(
                    file_path=default_storage.path(temp_path),
                    sheet_name=sheet_name,
                    sample_size=sample_size
                )
                
                # Se for Excel, obter nomes das planilhas
                if uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
                    sheet_names = spreadsheet_importer.get_sheet_names(
                        default_storage.path(temp_path)
                    )
                    preview_data['available_sheets'] = sheet_names
                
                return JsonResponse({
                    'status': 'success',
                    'data': preview_data
                })
                
            finally:
                # Limpar arquivo temporário
                if default_storage.exists(temp_path):
                    default_storage.delete(temp_path)
            
        except Exception as e:
            logger.error(f"Erro no preview da planilha: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SpreadsheetImportView(View):
    """
    View para importar dados de uma planilha para a memória inteligente.
    """
    
    def post(self, request):
        try:
            # Verificar se arquivo foi enviado
            if 'file' not in request.FILES:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Nenhum arquivo foi enviado'
                }, status=400)
            
            uploaded_file = request.FILES['file']
            sheet_name = request.POST.get('sheet_name')
            force_update = request.POST.get('force_update', 'false').lower() == 'true'
            batch_size = int(request.POST.get('batch_size', 100))
            
            # Validar tipo de arquivo
            if not any(uploaded_file.name.lower().endswith(ext) for ext in spreadsheet_importer.supported_formats):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Formato não suportado. Use: {", ".join(spreadsheet_importer.supported_formats)}'
                }, status=400)
            
            # Salvar arquivo temporariamente
            temp_path = default_storage.save(
                f'temp_imports/{uploaded_file.name}',
                ContentFile(uploaded_file.read())
            )
            
            try:
                # Fazer importação
                import_stats = spreadsheet_importer.import_to_memory(
                    file_path=default_storage.path(temp_path),
                    sheet_name=sheet_name,
                    force_update=force_update,
                    batch_size=batch_size
                )
                
                return JsonResponse({
                    'status': 'success',
                    'data': import_stats,
                    'message': f'Importação concluída: {import_stats["imported"]} produtos importados, {import_stats["updated"]} atualizados'
                })
                
            finally:
                # Limpar arquivo temporário
                if default_storage.exists(temp_path):
                    default_storage.delete(temp_path)
            
        except Exception as e:
            logger.error(f"Erro na importação da planilha: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SpreadsheetColumnsView(View):
    """
    View para obter informações sobre as colunas de uma planilha.
    """
    
    def post(self, request):
        try:
            # Verificar se arquivo foi enviado
            if 'file' not in request.FILES:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Nenhum arquivo foi enviado'
                }, status=400)
            
            uploaded_file = request.FILES['file']
            sheet_name = request.POST.get('sheet_name')
            
            # Salvar arquivo temporariamente
            temp_path = default_storage.save(
                f'temp_imports/{uploaded_file.name}',
                ContentFile(uploaded_file.read())
            )
            
            try:
                # Ler apenas o cabeçalho
                df = spreadsheet_importer.read_spreadsheet(
                    default_storage.path(temp_path),
                    sheet_name
                )
                
                # Mapear colunas
                column_mapping = spreadsheet_importer.map_columns(df)
                
                # Obter informações das colunas
                column_info = []
                for col in df.columns:
                    # Verificar se a coluna está mapeada
                    mapped_to = None
                    for standard_field, original_col in column_mapping.items():
                        if original_col == col:
                            mapped_to = standard_field
                            break
                    
                    # Analisar alguns valores da coluna
                    sample_values = df[col].dropna().head(3).tolist()
                    
                    column_info.append({
                        'name': col,
                        'mapped_to': mapped_to,
                        'sample_values': sample_values,
                        'non_null_count': df[col].count(),
                        'data_type': str(df[col].dtype)
                    })
                
                # Se for Excel, obter nomes das planilhas
                sheet_names = []
                if uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
                    sheet_names = spreadsheet_importer.get_sheet_names(
                        default_storage.path(temp_path)
                    )
                
                return JsonResponse({
                    'status': 'success',
                    'data': {
                        'columns': column_info,
                        'total_rows': len(df),
                        'total_columns': len(df.columns),
                        'column_mapping': column_mapping,
                        'available_sheets': sheet_names,
                        'field_mappings': spreadsheet_importer.field_mappings
                    }
                })
                
            finally:
                # Limpar arquivo temporário
                if default_storage.exists(temp_path):
                    default_storage.delete(temp_path)
            
        except Exception as e:
            logger.error(f"Erro ao analisar colunas da planilha: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ImportHistoryView(View):
    """
    View para obter histórico de importações.
    """
    
    def get(self, request):
        try:
            # Por enquanto, retornar informações básicas
            # Em uma implementação completa, isso viria de um banco de dados
            from .memory_utils import get_memory_statistics
            
            stats = get_memory_statistics()
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'current_memory_stats': stats,
                    'supported_formats': spreadsheet_importer.supported_formats,
                    'field_mappings': spreadsheet_importer.field_mappings,
                    'import_guidelines': {
                        'required_fields': ['sku', 'title', 'name'],
                        'recommended_fields': ['description', 'price', 'brand', 'category'],
                        'optional_fields': ['keywords', 'bullet_points', 'specifications'],
                        'tips': [
                            'Use nomes de colunas em português ou inglês',
                            'Certifique-se de que pelo menos uma coluna de identificação (SKU, título) está presente',
                            'Dados em branco serão ignorados',
                            'Use force_update=true para sobrescrever dados existentes'
                        ]
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico de importações: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ImportTemplateView(View):
    """
    View para gerar template de planilha para importação.
    """
    
    def get(self, request):
        try:
            import pandas as pd
            from django.http import HttpResponse
            
            # Criar template com colunas padrão
            template_data = {
                'SKU': ['PROD001', 'PROD002', 'PROD003'],
                'Título': ['Produto Exemplo 1', 'Produto Exemplo 2', 'Produto Exemplo 3'],
                'Descrição': [
                    'Descrição detalhada do produto 1',
                    'Descrição detalhada do produto 2', 
                    'Descrição detalhada do produto 3'
                ],
                'Preço': [99.99, 149.99, 199.99],
                'Marca': ['Marca A', 'Marca B', 'Marca C'],
                'Categoria': ['Eletrônicos', 'Casa', 'Esportes'],
                'Palavras-chave': [
                    'eletrônico, moderno, qualidade',
                    'casa, conforto, design',
                    'esporte, resistente, performance'
                ],
                'Características': [
                    'Alta qualidade; Garantia 2 anos; Fácil instalação',
                    'Design moderno; Material durável; Fácil limpeza',
                    'Resistente à água; Leve; Ergonômico'
                ]
            }
            
            df = pd.DataFrame(template_data)
            
            # Criar resposta Excel
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="template_importacao_beecatalog.xlsx"'
            
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Produtos', index=False)
                
                # Adicionar planilha com instruções
                instructions = pd.DataFrame({
                    'Campo': list(spreadsheet_importer.field_mappings.keys()),
                    'Nomes Aceitos': [', '.join(names) for names in spreadsheet_importer.field_mappings.values()],
                    'Obrigatório': ['Sim' if field in ['sku', 'title'] else 'Não' for field in spreadsheet_importer.field_mappings.keys()]
                })
                instructions.to_excel(writer, sheet_name='Instruções', index=False)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao gerar template: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)