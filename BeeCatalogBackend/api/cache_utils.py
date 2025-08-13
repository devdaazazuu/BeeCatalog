# api/cache_utils.py

import json
import hashlib
import logging
from typing import Any, Dict, Optional, Union
from django.core.cache import cache
from django.conf import settings
import redis

logger = logging.getLogger(__name__)

class AICache:
    """
    Sistema de cache inteligente para respostas da IA.
    Usa SHA256 hash do prompt + contexto como chave.
    """
    
    def __init__(self):
        self.cache_prefix = 'ai_response'
        self.default_timeout = 2592000  # 30 dias
        
        # Conectar diretamente ao Redis para operações avançadas apenas em produção
        self.redis_client = None
        if not settings.DEBUG:
            try:
                redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Não foi possível conectar ao Redis: {e}")
                self.redis_client = None
    
    def _generate_cache_key(self, prompt: str, context: Union[str, Dict, list]) -> str:
        """
        Gera uma chave de cache baseada no hash SHA256 do prompt + contexto.
        """
        # Normalizar o contexto para string JSON
        if isinstance(context, (dict, list)):
            context_str = json.dumps(context, sort_keys=True, ensure_ascii=False)
        else:
            context_str = str(context)
        
        # Criar hash único
        combined = f"{prompt}|{context_str}"
        hash_key = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
        return f"{self.cache_prefix}:{hash_key}"
    
    def get(self, prompt: str, context: Union[str, Dict, list]) -> Optional[Any]:
        """
        Recupera resposta do cache se existir.
        """
        try:
            cache_key = self._generate_cache_key(prompt, context)
            
            # Tentar primeiro o cache Django
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit (Django): {cache_key[:16]}...")
                return cached_data
            
            # Se não encontrar, tentar Redis diretamente
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    try:
                        result = json.loads(cached_data.decode('utf-8'))
                        logger.info(f"Cache hit (Redis): {cache_key[:16]}...")
                        # Replicar no cache Django para próximas consultas
                        cache.set(cache_key, result, timeout=300)  # 5 min no Django cache
                        return result
                    except json.JSONDecodeError:
                        logger.warning(f"Erro ao decodificar cache Redis: {cache_key[:16]}...")
            
            logger.debug(f"Cache miss: {cache_key[:16]}...")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar do cache: {e}")
            return None
    
    def set(self, prompt: str, context: Union[str, Dict, list], response: Any, timeout: Optional[int] = None) -> bool:
        """
        Armazena resposta no cache.
        """
        try:
            cache_key = self._generate_cache_key(prompt, context)
            timeout = timeout or self.default_timeout
            
            # Armazenar no cache Django (mais rápido para consultas frequentes)
            cache.set(cache_key, response, timeout=min(timeout, 3600))  # Max 1h no Django
            
            # Armazenar no Redis (persistência longa)
            if self.redis_client:
                try:
                    serialized_response = json.dumps(response, ensure_ascii=False)
                    self.redis_client.setex(cache_key, timeout, serialized_response)
                    logger.info(f"Cache stored: {cache_key[:16]}... (timeout: {timeout}s)")
                except (TypeError, ValueError) as e:
                    logger.warning(f"Erro ao serializar resposta para cache: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar no cache: {e}")
            return False
    
    def delete(self, prompt: str, context: Union[str, Dict, list]) -> bool:
        """
        Remove entrada específica do cache.
        """
        try:
            cache_key = self._generate_cache_key(prompt, context)
            
            # Remover do cache Django
            cache.delete(cache_key)
            
            # Remover do Redis
            if self.redis_client:
                self.redis_client.delete(cache_key)
            
            logger.info(f"Cache deleted: {cache_key[:16]}...")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar do cache: {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Limpa todo o cache de IA.
        """
        try:
            # Limpar cache Django com padrão
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern(f"{self.cache_prefix}:*")
            
            # Limpar Redis com padrão
            if self.redis_client:
                pattern = f"{self.cache_prefix}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} AI cache entries from Redis")
            
            logger.info("AI cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        """
        stats = {
            'redis_connected': self.redis_client is not None,
            'cache_prefix': self.cache_prefix,
            'default_timeout': self.default_timeout,
        }
        
        if self.redis_client:
            try:
                pattern = f"{self.cache_prefix}:*"
                keys = self.redis_client.keys(pattern)
                stats['redis_keys_count'] = len(keys)
                
                # Informações do Redis
                info = self.redis_client.info()
                stats['redis_memory_used'] = info.get('used_memory_human', 'N/A')
                stats['redis_connected_clients'] = info.get('connected_clients', 'N/A')
                
            except Exception as e:
                stats['redis_error'] = str(e)
        
        return stats

# Instância global do cache
ai_cache = AICache()

def get_or_cache_ai_response(prompt: str, context: Union[str, Dict, list], ai_function, *args, **kwargs) -> Any:
    """
    Função utilitária para buscar no cache ou executar função de IA.
    
    Args:
        prompt: O prompt enviado para a IA
        context: Contexto/dados enviados junto com o prompt
        ai_function: Função que chama a IA
        *args, **kwargs: Argumentos para a função de IA
    
    Returns:
        Resposta da IA (do cache ou nova)
    """
    # Tentar recuperar do cache
    cached_response = ai_cache.get(prompt, context)
    if cached_response is not None:
        return cached_response
    
    # Se não estiver no cache, executar função de IA
    try:
        logger.info("Executing AI function (cache miss)")
        response = ai_function(*args, **kwargs)
        
        # Armazenar no cache
        ai_cache.set(prompt, context, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao executar função de IA: {e}")
        raise

def batch_ai_requests(requests: list, ai_function, batch_size: int = 5) -> list:
    """
    Processa múltiplas requisições de IA em lotes para otimizar performance.
    
    Args:
        requests: Lista de dicionários com 'prompt' e 'context'
        ai_function: Função que processa um lote de requisições
        batch_size: Tamanho do lote
    
    Returns:
        Lista de respostas na mesma ordem das requisições
    """
    results = []
    
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i + batch_size]
        
        # Verificar cache para cada item do lote
        batch_results = []
        uncached_items = []
        uncached_indices = []
        
        for idx, request in enumerate(batch):
            cached = ai_cache.get(request['prompt'], request['context'])
            if cached is not None:
                batch_results.append(cached)
            else:
                batch_results.append(None)  # Placeholder
                uncached_items.append(request)
                uncached_indices.append(idx)
        
        # Processar itens não cacheados em lote
        if uncached_items:
            try:
                logger.info(f"Processing batch of {len(uncached_items)} uncached AI requests")
                uncached_responses = ai_function(uncached_items)
                
                # Armazenar respostas no cache e inserir nos resultados
                for idx, (request, response) in enumerate(zip(uncached_items, uncached_responses)):
                    ai_cache.set(request['prompt'], request['context'], response)
                    batch_results[uncached_indices[idx]] = response
                    
            except Exception as e:
                logger.error(f"Erro ao processar lote de IA: {e}")
                # Preencher com None para itens que falharam
                for idx in uncached_indices:
                    batch_results[idx] = None
        
        results.extend(batch_results)
    
    return results