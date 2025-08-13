# api/memory_views.py

import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from .memory_utils import (
    get_memory_statistics,
    clear_product_memory,
    delete_product_from_memory,
    export_memory_data,
    extract_product_identifier
)
from .product_memory import product_memory

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class ProductMemoryStatsView(View):
    """
    View para obter estatísticas da memória de produtos.
    """
    
    def get(self, request):
        try:
            stats = get_memory_statistics()
            return JsonResponse({
                'status': 'success',
                'data': stats
            })
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas da memória: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ClearProductMemoryView(View):
    """
    View para limpar toda a memória de produtos.
    """
    
    def post(self, request):
        try:
            success = clear_product_memory()
            
            if success:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Memória de produtos limpa com sucesso'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Falha ao limpar memória de produtos'
                }, status=500)
                
        except Exception as e:
            logger.error(f"Erro ao limpar memória de produtos: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteProductMemoryView(View):
    """
    View para remover um produto específico da memória.
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_data = data.get('product_data')
            
            if not product_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'product_data é obrigatório'
                }, status=400)
            
            success = delete_product_from_memory(product_data)
            identifier = extract_product_identifier(product_data)
            
            if success:
                return JsonResponse({
                    'status': 'success',
                    'message': f'Produto {identifier} removido da memória com sucesso'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Falha ao remover produto {identifier} da memória'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao remover produto da memória: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ExportProductMemoryView(View):
    """
    View para exportar dados da memória de produtos.
    """
    
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 1000))
            exported_data = export_memory_data(limit=limit)
            
            return JsonResponse({
                'status': 'success',
                'data': exported_data,
                'count': len(exported_data)
            })
            
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Parâmetro limit deve ser um número'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao exportar dados da memória: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ListProductsMemoryView(View):
    """
    View para listar produtos na memória.
    """
    
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 100))
            products_list = product_memory.list_products(limit=limit)
            
            return JsonResponse({
                'status': 'success',
                'data': products_list,
                'count': len(products_list)
            })
            
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Parâmetro limit deve ser um número'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao listar produtos da memória: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class GetProductMemoryView(View):
    """
    View para obter dados de um produto específico da memória.
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_data = data.get('product_data')
            
            if not product_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'product_data é obrigatório'
                }, status=400)
            
            identifier = extract_product_identifier(product_data)
            saved_data = product_memory.get_product_data(identifier)
            
            if saved_data:
                return JsonResponse({
                    'status': 'success',
                    'data': saved_data,
                    'identifier': identifier
                })
            else:
                return JsonResponse({
                    'status': 'not_found',
                    'message': f'Produto {identifier} não encontrado na memória',
                    'identifier': identifier
                }, status=404)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao obter produto da memória: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ForceRegenerateProductView(View):
    """
    View para forçar regeneração de conteúdo de um produto.
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_data = data.get('product_data')
            
            if not product_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'product_data é obrigatório'
                }, status=400)
            
            identifier = extract_product_identifier(product_data)
            
            # Remover da memória para forçar regeneração
            success = delete_product_from_memory(product_data)
            
            return JsonResponse({
                'status': 'success',
                'message': f'Produto {identifier} marcado para regeneração. Será recriado na próxima execução.',
                'identifier': identifier,
                'removed_from_memory': success
            })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao forçar regeneração do produto: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

# Função auxiliar para verificar saúde da memória
@require_http_methods(["GET"])
def memory_health_check(request):
    """
    Endpoint para verificar a saúde do sistema de memória.
    """
    try:
        stats = get_memory_statistics()
        
        # Verificar se o sistema está funcionando
        health_status = {
            'memory_system': 'healthy',
            'redis_connected': stats.get('redis_connected', False),
            'products_in_redis': stats.get('redis_products', 0),
            'local_backups': stats.get('local_backups', 0),
            'memory_directory': stats.get('memory_dir', 'N/A')
        }
        
        # Determinar status geral
        if not stats.get('redis_connected', False) and stats.get('local_backups', 0) == 0:
            health_status['memory_system'] = 'degraded'
        
        return JsonResponse({
            'status': 'success',
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Erro no health check da memória: {e}")
        return JsonResponse({
            'status': 'error',
            'health': {
                'memory_system': 'unhealthy',
                'error': str(e)
            }
        }, status=500)