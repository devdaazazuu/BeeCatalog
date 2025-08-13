# api/history_views.py

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q

from .product_memory import product_memory
from .memory_utils import get_memory_statistics

logger = logging.getLogger(__name__)

class CatalogHistoryView(View):
    """
    View para gerenciar o histórico de catalogação de produtos.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        """
        Lista o histórico de produtos catalogados com paginação e filtros.
        
        Query Parameters:
        - page: Número da página (padrão: 1)
        - limit: Itens por página (padrão: 20, máximo: 100)
        - search: Busca por nome do produto
        - status: Filtro por status (validated, pending, all)
        - date_from: Data inicial (YYYY-MM-DD)
        - date_to: Data final (YYYY-MM-DD)
        - origin: Filtro por origem (spreadsheet, manual, link_extraction)
        """
        try:
            # Parâmetros de paginação
            page = int(request.GET.get('page', 1))
            limit = min(int(request.GET.get('limit', 20)), 100)
            
            # Parâmetros de filtro
            search = request.GET.get('search', '').strip()
            status_filter = request.GET.get('status', 'all')
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            origin_filter = request.GET.get('origin', 'all')
            
            # Obter todos os produtos da memória
            all_products = self._get_enhanced_product_list()
            
            # Aplicar filtros
            filtered_products = self._apply_filters(
                all_products, search, status_filter, date_from, date_to, origin_filter
            )
            
            # Paginação
            total_items = len(filtered_products)
            start_index = (page - 1) * limit
            end_index = start_index + limit
            paginated_products = filtered_products[start_index:end_index]
            
            # Estatísticas
            stats = self._get_history_statistics(all_products)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'products': paginated_products,
                    'pagination': {
                        'current_page': page,
                        'total_pages': (total_items + limit - 1) // limit,
                        'total_items': total_items,
                        'items_per_page': limit,
                        'has_next': end_index < total_items,
                        'has_previous': page > 1
                    },
                    'statistics': stats,
                    'filters_applied': {
                        'search': search,
                        'status': status_filter,
                        'date_from': date_from,
                        'date_to': date_to,
                        'origin': origin_filter
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Erro ao listar histórico: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erro interno do servidor',
                'details': str(e)
            }, status=500)
    
    def _get_enhanced_product_list(self) -> List[Dict[str, Any]]:
        """
        Obtém lista completa de produtos com informações enriquecidas.
        """
        try:
            products = []
            
            # Obter produtos da memória
            memory_products = product_memory.list_products(limit=10000)  # Limite alto para pegar todos
            
            for product in memory_products:
                try:
                    # Obter dados completos do produto
                    full_data = product_memory.get_product_data(product.get('identifier', ''))
                    
                    if full_data:
                        enhanced_product = self._enhance_product_data(full_data)
                        products.append(enhanced_product)
                        
                except Exception as e:
                    logger.warning(f"Erro ao processar produto {product.get('identifier')}: {e}")
                    continue
            
            # Ordenar por data de criação (mais recente primeiro)
            products.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return products
            
        except Exception as e:
            logger.error(f"Erro ao obter lista de produtos: {e}")
            return []
    
    def _enhance_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece os dados do produto com informações adicionais para o histórico.
        """
        try:
            original_data = product_data.get('original_data', {})
            generated_content = product_data.get('generated_content', {})
            
            # Determinar origem
            origin = self._determine_origin(original_data)
            
            # Determinar status (por enquanto, todos são considerados validados)
            status = 'validated'  # Pode ser expandido futuramente
            
            # Extrair informações principais
            product_name = (
                generated_content.get('titulo') or 
                original_data.get('title') or 
                original_data.get('nome') or 
                product_data.get('product_identifier', 'Produto sem nome')
            )
            
            return {
                'id': product_data.get('product_identifier'),
                'name': product_name,
                'sku': original_data.get('sku') or original_data.get('SKU'),
                'created_at': product_data.get('created_at'),
                'updated_at': product_data.get('updated_at'),
                'origin': origin,
                'status': status,
                'has_title': bool(generated_content.get('titulo')),
                'has_description': bool(generated_content.get('descricao_produto')),
                'has_bullet_points': bool(generated_content.get('bullet_points')),
                'has_keywords': bool(generated_content.get('palavras_chave')),
                'original_data_keys': list(original_data.keys()) if original_data else [],
                'generated_content_keys': list(generated_content.keys()) if generated_content else [],
                'data_quality_score': self._calculate_data_quality(original_data, generated_content)
            }
            
        except Exception as e:
            logger.error(f"Erro ao enriquecer dados do produto: {e}")
            return {
                'id': product_data.get('product_identifier', 'unknown'),
                'name': 'Erro ao processar produto',
                'status': 'error',
                'created_at': product_data.get('created_at'),
                'origin': 'unknown'
            }
    
    def _determine_origin(self, original_data: Dict[str, Any]) -> str:
        """
        Determina a origem do produto baseado nos dados originais.
        """
        if not original_data:
            return 'unknown'
        
        # Se tem muitos campos estruturados, provavelmente veio de planilha
        structured_fields = ['sku', 'SKU', 'title', 'price', 'categoria', 'marca']
        if sum(1 for field in structured_fields if field in original_data) >= 3:
            return 'spreadsheet'
        
        # Se tem URL, provavelmente veio de extração de link
        if 'url' in original_data or 'link' in original_data:
            return 'link_extraction'
        
        # Caso contrário, assume entrada manual
        return 'manual'
    
    def _calculate_data_quality(self, original_data: Dict[str, Any], generated_content: Dict[str, Any]) -> float:
        """
        Calcula um score de qualidade dos dados (0-100).
        """
        try:
            score = 0
            
            # Pontos por dados originais
            if original_data:
                score += min(len(original_data) * 5, 30)  # Máximo 30 pontos
            
            # Pontos por conteúdo gerado
            if generated_content:
                if generated_content.get('titulo'):
                    score += 20
                if generated_content.get('descricao_produto'):
                    score += 25
                if generated_content.get('bullet_points'):
                    score += 15
                if generated_content.get('palavras_chave'):
                    score += 10
            
            return min(score, 100)
            
        except Exception:
            return 0
    
    def _apply_filters(self, products: List[Dict[str, Any]], search: str, status_filter: str, 
                      date_from: str, date_to: str, origin_filter: str) -> List[Dict[str, Any]]:
        """
        Aplica filtros à lista de produtos.
        """
        filtered = products
        
        # Filtro de busca por nome
        if search:
            search_lower = search.lower()
            filtered = [
                p for p in filtered 
                if search_lower in p.get('name', '').lower() or 
                   search_lower in str(p.get('sku', '')).lower()
            ]
        
        # Filtro por status
        if status_filter != 'all':
            filtered = [p for p in filtered if p.get('status') == status_filter]
        
        # Filtro por origem
        if origin_filter != 'all':
            filtered = [p for p in filtered if p.get('origin') == origin_filter]
        
        # Filtros de data
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from)
                filtered = [
                    p for p in filtered 
                    if p.get('created_at') and 
                       datetime.fromisoformat(p['created_at'].replace('Z', '+00:00').split('+')[0]) >= date_from_obj
                ]
            except Exception as e:
                logger.warning(f"Erro ao aplicar filtro date_from: {e}")
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to)
                filtered = [
                    p for p in filtered 
                    if p.get('created_at') and 
                       datetime.fromisoformat(p['created_at'].replace('Z', '+00:00').split('+')[0]) <= date_to_obj
                ]
            except Exception as e:
                logger.warning(f"Erro ao aplicar filtro date_to: {e}")
        
        return filtered
    
    def _get_history_statistics(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estatísticas do histórico.
        """
        try:
            total = len(products)
            
            if total == 0:
                return {
                    'total_products': 0,
                    'by_status': {},
                    'by_origin': {},
                    'average_quality_score': 0
                }
            
            # Estatísticas por status
            by_status = {}
            for product in products:
                status = product.get('status', 'unknown')
                by_status[status] = by_status.get(status, 0) + 1
            
            # Estatísticas por origem
            by_origin = {}
            for product in products:
                origin = product.get('origin', 'unknown')
                by_origin[origin] = by_origin.get(origin, 0) + 1
            
            # Score médio de qualidade
            quality_scores = [p.get('data_quality_score', 0) for p in products]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            return {
                'total_products': total,
                'by_status': by_status,
                'by_origin': by_origin,
                'average_quality_score': round(avg_quality, 1)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {
                'total_products': len(products),
                'by_status': {},
                'by_origin': {},
                'average_quality_score': 0
            }


class ValidateMemoryView(View):
    """
    View para validar memórias de produtos.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, product_id):
        """
        Valida uma memória de produto específica.
        
        Args:
            product_id: ID do produto a ser validado
        """
        try:
            # Verificar se o produto existe
            product_data = product_memory.get_product_data(product_id)
            
            if not product_data:
                return JsonResponse({
                    'success': False,
                    'error': 'Produto não encontrado na memória'
                }, status=404)
            
            # Marcar como validado (adicionar flag de validação)
            product_data['validated'] = True
            product_data['validated_at'] = datetime.now().isoformat()
            product_data['updated_at'] = datetime.now().isoformat()
            
            # Salvar de volta na memória
            success = product_memory.save_product_data(
                product_id,
                product_data.get('original_data', {}),
                product_data.get('generated_content', {}),
                force_update=True
            )
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Produto {product_id} validado com sucesso',
                    'data': {
                        'product_id': product_id,
                        'validated_at': product_data['validated_at']
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao salvar validação'
                }, status=500)
            
        except Exception as e:
            logger.error(f"Erro ao validar produto {product_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erro interno do servidor',
                'details': str(e)
            }, status=500)


class DeleteMemoryView(View):
    """
    View para excluir memórias de produtos.
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, product_id):
        """
        Exclui uma memória de produto específica.
        
        Args:
            product_id: ID do produto a ser excluído
        """
        try:
            # Verificar se o produto existe
            if not product_memory.has_product(product_id):
                return JsonResponse({
                    'success': False,
                    'error': 'Produto não encontrado na memória'
                }, status=404)
            
            # Excluir o produto
            success = product_memory.delete_product(product_id)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Produto {product_id} excluído com sucesso',
                    'data': {
                        'product_id': product_id,
                        'deleted_at': datetime.now().isoformat()
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao excluir produto'
                }, status=500)
            
        except Exception as e:
            logger.error(f"Erro ao excluir produto {product_id}: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erro interno do servidor',
                'details': str(e)
            }, status=500)


class MemoryStatsView(View):
    """
    View para obter estatísticas da memória.
    """
    
    def get(self, request):
        """
        Retorna estatísticas gerais da memória de produtos.
        """
        try:
            # Estatísticas básicas da memória
            memory_stats = get_memory_statistics()
            
            # Estatísticas específicas do histórico
            history_view = CatalogHistoryView()
            all_products = history_view._get_enhanced_product_list()
            history_stats = history_view._get_history_statistics(all_products)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'memory_stats': memory_stats,
                    'history_stats': history_stats,
                    'last_updated': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erro interno do servidor',
                'details': str(e)
            }, status=500)