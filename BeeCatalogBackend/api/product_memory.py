# api/product_memory.py

import os
import json
import hashlib
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
import redis

logger = logging.getLogger(__name__)

class ProductMemory:
    """
    Sistema de Memória Inteligente BeeCatalog
    
    Armazena e reutiliza dados de produtos já processados (títulos, descrições, tópicos)
    para evitar geração repetitiva e consumo desnecessário de tokens de IA.
    
    Funcionalidades:
    - Salva dados de produtos em estrutura organizada
    - Prioriza reutilização antes de gerar novo conteúdo
    - Permite forçar regeneração quando necessário
    - Compatível com planilhas para reutilização automática
    - Minimiza chamadas à IA para produtos repetidos
    """
    
    def __init__(self):
        self.memory_prefix = 'product_memory'
        self.default_timeout = 7776000  # 90 dias
        
        # Diretório local para backup dos dados
        self.memory_dir = os.path.join(settings.BASE_DIR, "memory", "produtos")
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir, exist_ok=True)
        
        # Conectar ao Redis para armazenamento principal apenas em produção
        self.redis_client = None
        if not settings.DEBUG:
            try:
                redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Não foi possível conectar ao Redis para memória de produtos: {e}")
                self.redis_client = None
    
    def _generate_product_key(self, product_identifier: str) -> str:
        """
        Gera uma chave única para o produto baseada no identificador.
        
        Args:
            product_identifier: SKU, título ou outro identificador único do produto
        
        Returns:
            Chave única para o produto
        """
        # Normalizar o identificador
        normalized_id = str(product_identifier).strip().lower()
        
        # Gerar hash para garantir unicidade e evitar caracteres especiais
        hash_key = hashlib.md5(normalized_id.encode('utf-8')).hexdigest()
        
        return f"{self.memory_prefix}:{hash_key}"
    
    def _get_product_file_path(self, product_identifier: str) -> str:
        """
        Retorna o caminho do arquivo local para backup do produto.
        """
        normalized_id = str(product_identifier).strip().lower()
        safe_filename = "".join(c for c in normalized_id if c.isalnum() or c in ('-', '_'))[:50]
        return os.path.join(self.memory_dir, f"{safe_filename}.json")
    
    def save_product_data(self, product_identifier: str, product_data: Dict[str, Any], 
                         generated_content: Dict[str, Any], force_update: bool = False, 
                         origin: str = 'manual', status: str = 'pending') -> bool:
        """
        Salva os dados do produto e conteúdo gerado na memória.
        
        Args:
            product_identifier: Identificador único do produto (SKU, título, etc.)
            product_data: Dados originais do produto
            generated_content: Conteúdo gerado pela IA (título, descrição, tópicos, etc.)
            force_update: Se True, sobrescreve dados existentes
        
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            memory_key = self._generate_product_key(product_identifier)
            
            # Verificar se já existe e não forçar atualização
            if not force_update and self.get_product_data(product_identifier):
                logger.info(f"Produto {product_identifier} já existe na memória. Use force_update=True para sobrescrever.")
                return False
            
            # Verificar se já existe dados
            existing_data = self.get_product_data(product_identifier) if not force_update else None
            current_time = datetime.now().isoformat()
            
            # Estrutura dos dados salvos
            memory_data = {
                'product_identifier': product_identifier,
                'product_data': product_data,
                'generated_content': generated_content,
                'created_at': existing_data.get('created_at', current_time) if existing_data else current_time,
                'updated_at': current_time,
                'origin': existing_data.get('origin', origin) if existing_data else origin,
                'status': existing_data.get('status', status) if existing_data else status,
                'validated_at': existing_data.get('validated_at') if existing_data else None,
                'data_quality_score': self._calculate_quality_score(product_data, generated_content),
                'version': '1.0'
            }
            
            # Salvar no Redis (principal)
            if self.redis_client:
                try:
                    serialized_data = json.dumps(memory_data, ensure_ascii=False, indent=2)
                    self.redis_client.setex(memory_key, self.default_timeout, serialized_data)
                    logger.info(f"Produto {product_identifier} salvo na memória Redis")
                except Exception as e:
                    logger.error(f"Erro ao salvar no Redis: {e}")
            
            # Salvar no cache Django (acesso rápido)
            cache.set(memory_key, memory_data, timeout=3600)  # 1 hora no cache Django
            
            # Backup local em arquivo
            try:
                file_path = self._get_product_file_path(product_identifier)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, ensure_ascii=False, indent=2)
                logger.debug(f"Backup local salvo: {file_path}")
            except Exception as e:
                logger.warning(f"Erro ao salvar backup local: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados do produto {product_identifier}: {e}")
            return False
    
    def get_product_data(self, product_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Recupera os dados do produto da memória.
        
        Args:
            product_identifier: Identificador único do produto
        
        Returns:
            Dados do produto se encontrado, None caso contrário
        """
        try:
            memory_key = self._generate_product_key(product_identifier)
            
            # Tentar primeiro o cache Django (mais rápido)
            cached_data = cache.get(memory_key)
            if cached_data:
                logger.debug(f"Produto {product_identifier} encontrado no cache Django")
                return cached_data
            
            # Tentar Redis
            if self.redis_client:
                try:
                    redis_data = self.redis_client.get(memory_key)
                    if redis_data:
                        result = json.loads(redis_data.decode('utf-8'))
                        # Replicar no cache Django para próximas consultas
                        cache.set(memory_key, result, timeout=3600)
                        logger.debug(f"Produto {product_identifier} encontrado no Redis")
                        return result
                except Exception as e:
                    logger.warning(f"Erro ao recuperar do Redis: {e}")
            
            # Tentar backup local
            try:
                file_path = self._get_product_file_path(product_identifier)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                    # Replicar nos caches
                    cache.set(memory_key, result, timeout=3600)
                    if self.redis_client:
                        serialized_data = json.dumps(result, ensure_ascii=False)
                        self.redis_client.setex(memory_key, self.default_timeout, serialized_data)
                    logger.debug(f"Produto {product_identifier} encontrado no backup local")
                    return result
            except Exception as e:
                logger.warning(f"Erro ao recuperar backup local: {e}")
            
            logger.debug(f"Produto {product_identifier} não encontrado na memória")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar dados do produto {product_identifier}: {e}")
            return None
    
    def has_product(self, product_identifier: str) -> bool:
        """
        Verifica se o produto existe na memória.
        
        Args:
            product_identifier: Identificador único do produto
        
        Returns:
            True se o produto existe, False caso contrário
        """
        return self.get_product_data(product_identifier) is not None
    
    def delete_product(self, product_identifier: str) -> bool:
        """
        Remove o produto da memória.
        
        Args:
            product_identifier: Identificador único do produto
        
        Returns:
            True se removeu com sucesso, False caso contrário
        """
        try:
            memory_key = self._generate_product_key(product_identifier)
            
            # Remover do cache Django
            cache.delete(memory_key)
            
            # Remover do Redis
            if self.redis_client:
                self.redis_client.delete(memory_key)
            
            # Remover backup local
            try:
                file_path = self._get_product_file_path(product_identifier)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Erro ao remover backup local: {e}")
            
            logger.info(f"Produto {product_identifier} removido da memória")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover produto {product_identifier}: {e}")
            return False
    
    def clear_all_memory(self) -> bool:
        """
        Limpa toda a memória de produtos.
        
        Returns:
            True se limpou com sucesso, False caso contrário
        """
        try:
            # Limpar Redis
            if self.redis_client:
                pattern = f"{self.memory_prefix}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            # Limpar cache Django
            # Note: Django cache não tem clear por padrão, então vamos limpar individualmente
            
            # Limpar backups locais
            try:
                if os.path.exists(self.memory_dir):
                    for filename in os.listdir(self.memory_dir):
                        if filename.endswith('.json'):
                            os.remove(os.path.join(self.memory_dir, filename))
            except Exception as e:
                logger.warning(f"Erro ao limpar backups locais: {e}")
            
            logger.info("Memória de produtos limpa com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar memória de produtos: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da memória de produtos.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            stats = {
                'redis_products': 0,
                'local_backups': 0,
                'memory_dir': self.memory_dir,
                'redis_connected': self.redis_client is not None
            }
            
            # Contar produtos no Redis
            if self.redis_client:
                try:
                    pattern = f"{self.memory_prefix}:*"
                    keys = self.redis_client.keys(pattern)
                    stats['redis_products'] = len(keys)
                except Exception as e:
                    logger.warning(f"Erro ao contar produtos no Redis: {e}")
            
            # Contar backups locais
            try:
                if os.path.exists(self.memory_dir):
                    json_files = [f for f in os.listdir(self.memory_dir) if f.endswith('.json')]
                    stats['local_backups'] = len(json_files)
            except Exception as e:
                logger.warning(f"Erro ao contar backups locais: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas da memória: {e}")
            return {}
    
    def _calculate_quality_score(self, product_data: Dict[str, Any], generated_content: Dict[str, Any]) -> int:
        """
        Calcula um score de qualidade dos dados do produto.
        
        Args:
            product_data: Dados originais do produto
            generated_content: Conteúdo gerado pela IA
        
        Returns:
            Score de qualidade de 0 a 100
        """
        try:
            score = 0
            
            # Verificar dados originais (30 pontos)
            if product_data.get('nome'):
                score += 10
            if product_data.get('preco'):
                score += 10
            if product_data.get('categoria'):
                score += 10
            
            # Verificar conteúdo gerado (70 pontos)
            if generated_content.get('titulo'):
                score += 20
            if generated_content.get('descricao_produto'):
                score += 25
            if generated_content.get('bullet_points'):
                score += 25
            
            return min(score, 100)
            
        except Exception as e:
            logger.warning(f"Erro ao calcular score de qualidade: {e}")
            return 0
    
    def validate_product(self, product_identifier: str) -> bool:
        """
        Valida um produto na memória.
        
        Args:
            product_identifier: Identificador único do produto
        
        Returns:
            True se validou com sucesso, False caso contrário
        """
        try:
            product_data = self.get_product_data(product_identifier)
            if not product_data:
                return False
            
            # Atualizar status para validado
            product_data['status'] = 'validated'
            product_data['validated_at'] = datetime.now().isoformat()
            product_data['updated_at'] = datetime.now().isoformat()
            
            # Salvar de volta
            memory_key = self._generate_product_key(product_identifier)
            data_json = json.dumps(product_data, ensure_ascii=False)
            
            # Salvar no Redis
            if self.redis_client:
                self.redis_client.setex(memory_key, self.redis_ttl, data_json)
            
            # Salvar no cache Django
            cache.set(memory_key, product_data, timeout=self.cache_timeout)
            
            # Salvar backup local
            try:
                file_path = self._get_product_file_path(product_identifier)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(product_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Erro ao salvar backup local: {e}")
            
            logger.info(f"Produto {product_identifier} validado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar produto {product_identifier}: {e}")
            return False
    
    def list_products_advanced(self, page: int = 1, limit: int = 20, 
                              search: str = '', status: str = 'all', 
                              origin: str = 'all', date_from: str = '', 
                              date_to: str = '') -> Dict[str, Any]:
        """
        Lista produtos na memória com filtros avançados e paginação.
        
        Args:
            page: Página atual (começa em 1)
            limit: Número de itens por página
            search: Termo de busca (nome ou SKU)
            status: Filtro por status ('all', 'validated', 'pending')
            origin: Filtro por origem ('all', 'spreadsheet', 'manual', 'link_extraction')
            date_from: Data inicial (formato ISO)
            date_to: Data final (formato ISO)
        
        Returns:
            Dicionário com produtos, paginação e estatísticas
        """
        try:
            all_products = []
            
            # Listar do Redis
            if self.redis_client:
                try:
                    pattern = f"{self.memory_prefix}:*"
                    keys = self.redis_client.keys(pattern)
                    
                    for key in keys:
                        try:
                            data = self.redis_client.get(key)
                            if data:
                                product_data = json.loads(data.decode('utf-8'))
                                
                                # Extrair informações do produto
                                product_info = {
                                    'id': product_data.get('product_identifier'),
                                    'name': product_data.get('product_data', {}).get('nome', 'Produto sem nome'),
                                    'sku': product_data.get('product_data', {}).get('sku', ''),
                                    'created_at': product_data.get('created_at'),
                                    'updated_at': product_data.get('updated_at'),
                                    'origin': product_data.get('origin', 'manual'),
                                    'status': product_data.get('status', 'pending'),
                                    'validated_at': product_data.get('validated_at'),
                                    'data_quality_score': product_data.get('data_quality_score', 0),
                                    'has_title': bool(product_data.get('generated_content', {}).get('titulo')),
                                    'has_description': bool(product_data.get('generated_content', {}).get('descricao_produto')),
                                    'has_bullet_points': bool(product_data.get('generated_content', {}).get('bullet_points'))
                                }
                                
                                all_products.append(product_info)
                                
                        except Exception as e:
                            logger.warning(f"Erro ao processar produto {key}: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Erro ao listar produtos do Redis: {e}")
            
            # Aplicar filtros
            filtered_products = self._apply_filters(all_products, search, status, origin, date_from, date_to)
            
            # Ordenar por data de criação (mais recentes primeiro)
            filtered_products.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Calcular paginação
            total_items = len(filtered_products)
            total_pages = (total_items + limit - 1) // limit
            start_index = (page - 1) * limit
            end_index = start_index + limit
            
            paginated_products = filtered_products[start_index:end_index]
            
            # Calcular estatísticas
            statistics = self._calculate_statistics(all_products)
            
            return {
                'products': paginated_products,
                'pagination': {
                    'currentPage': page,
                    'totalPages': total_pages,
                    'totalItems': total_items,
                    'itemsPerPage': limit,
                    'hasNext': page < total_pages,
                    'hasPrevious': page > 1
                },
                'statistics': statistics
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar produtos avançado: {e}")
            return {
                'products': [],
                'pagination': {
                    'currentPage': 1,
                    'totalPages': 0,
                    'totalItems': 0,
                    'itemsPerPage': limit,
                    'hasNext': False,
                    'hasPrevious': False
                },
                'statistics': {}
            }
    
    def _apply_filters(self, products: List[Dict[str, Any]], search: str, status: str, 
                      origin: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """
        Aplica filtros à lista de produtos.
        """
        filtered = products
        
        # Filtro de busca
        if search:
            search_lower = search.lower()
            filtered = [
                p for p in filtered 
                if search_lower in p.get('name', '').lower() or 
                   search_lower in p.get('sku', '').lower()
            ]
        
        # Filtro de status
        if status != 'all':
            filtered = [p for p in filtered if p.get('status') == status]
        
        # Filtro de origem
        if origin != 'all':
            filtered = [p for p in filtered if p.get('origin') == origin]
        
        # Filtro de data
        if date_from:
            filtered = [p for p in filtered if p.get('created_at', '') >= date_from]
        
        if date_to:
            filtered = [p for p in filtered if p.get('created_at', '') <= date_to]
        
        return filtered
    
    def _calculate_statistics(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estatísticas dos produtos.
        """
        if not products:
            return {}
        
        total_products = len(products)
        
        # Estatísticas por status
        by_status = {}
        for product in products:
            status = product.get('status', 'pending')
            by_status[status] = by_status.get(status, 0) + 1
        
        # Estatísticas por origem
        by_origin = {}
        for product in products:
            origin = product.get('origin', 'manual')
            by_origin[origin] = by_origin.get(origin, 0) + 1
        
        # Qualidade média
        quality_scores = [p.get('data_quality_score', 0) for p in products]
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'total_products': total_products,
            'by_status': by_status,
            'by_origin': by_origin,
            'average_quality_score': round(average_quality, 1)
        }
    
    def list_products(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lista produtos na memória (método legado).
        
        Args:
            limit: Número máximo de produtos a retornar
        
        Returns:
            Lista de produtos com informações básicas
        """
        try:
            result = self.list_products_advanced(page=1, limit=limit)
            return result.get('products', [])
            
        except Exception as e:
            logger.error(f"Erro ao listar produtos: {e}")
            return []

# Instância global da memória de produtos
product_memory = ProductMemory()