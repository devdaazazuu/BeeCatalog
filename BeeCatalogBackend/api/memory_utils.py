# api/memory_utils.py

import logging
from typing import Dict, Any, Optional, List, Tuple
from .product_memory import product_memory

logger = logging.getLogger(__name__)

def extract_product_identifier(product_data: Dict[str, Any]) -> str:
    """
    Extrai um identificador único do produto a partir dos dados.
    
    Prioridade:
    1. SKU (se disponível)
    2. Título do produto
    3. Nome do item
    4. Combinação de marca + modelo
    5. Hash dos dados principais
    
    Args:
        product_data: Dados do produto
    
    Returns:
        Identificador único do produto
    """
    try:
        # Tentar SKU primeiro
        sku = product_data.get('sku') or product_data.get('SKU')
        if sku and str(sku).strip():
            return f"sku_{str(sku).strip()}"
        
        # Tentar título do produto
        titulo = (product_data.get('titulo') or 
                 product_data.get('item_name') or 
                 product_data.get('product_title') or
                 product_data.get('nome_produto'))
        if titulo and str(titulo).strip():
            return f"titulo_{str(titulo).strip()[:100]}"
        
        # Tentar combinação marca + modelo
        marca = product_data.get('marca') or product_data.get('brand')
        modelo = product_data.get('modelo') or product_data.get('model')
        if marca and modelo:
            return f"marca_modelo_{str(marca).strip()}_{str(modelo).strip()}"
        
        # Fallback: usar hash dos dados principais
        import hashlib
        key_fields = ['titulo', 'item_name', 'marca', 'brand', 'modelo', 'model', 'descricao']
        combined_data = ""
        for field in key_fields:
            value = product_data.get(field)
            if value:
                combined_data += str(value).strip().lower()
        
        if combined_data:
            hash_id = hashlib.md5(combined_data.encode('utf-8')).hexdigest()[:16]
            return f"hash_{hash_id}"
        
        # Último recurso: usar índice se disponível
        index = product_data.get('index') or product_data.get('row_index')
        if index is not None:
            return f"index_{index}"
        
        # Se nada funcionar, usar timestamp
        import time
        return f"unknown_{int(time.time())}"
        
    except Exception as e:
        logger.error(f"Erro ao extrair identificador do produto: {e}")
        import time
        return f"error_{int(time.time())}"

def check_product_in_memory(product_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Verifica se o produto já existe na memória.
    
    Args:
        product_data: Dados do produto
    
    Returns:
        Tupla (existe_na_memoria, dados_salvos)
    """
    try:
        identifier = extract_product_identifier(product_data)
        saved_data = product_memory.get_product_data(identifier)
        
        if saved_data:
            logger.info(f"Produto encontrado na memória: {identifier}")
            return True, saved_data
        else:
            logger.debug(f"Produto não encontrado na memória: {identifier}")
            return False, None
            
    except Exception as e:
        logger.error(f"Erro ao verificar produto na memória: {e}")
        return False, None

def save_generated_content_to_memory(product_data: Dict[str, Any], 
                                   generated_content: Dict[str, Any],
                                   force_update: bool = False) -> bool:
    """
    Salva o conteúdo gerado na memória de produtos.
    
    Args:
        product_data: Dados originais do produto
        generated_content: Conteúdo gerado pela IA
        force_update: Se True, sobrescreve dados existentes
    
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        identifier = extract_product_identifier(product_data)
        
        # Normalizar o conteúdo gerado
        normalized_content = normalize_generated_content(generated_content)
        
        success = product_memory.save_product_data(
            product_identifier=identifier,
            product_data=product_data,
            generated_content=normalized_content,
            force_update=force_update
        )
        
        if success:
            logger.info(f"Conteúdo salvo na memória para produto: {identifier}")
        else:
            logger.warning(f"Falha ao salvar conteúdo na memória para produto: {identifier}")
        
        return success
        
    except Exception as e:
        logger.error(f"Erro ao salvar conteúdo gerado na memória: {e}")
        return False

def normalize_generated_content(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza o conteúdo gerado para um formato padrão.
    
    Args:
        content: Conteúdo gerado pela IA
    
    Returns:
        Conteúdo normalizado
    """
    try:
        normalized = {
            'titulo': None,
            'descricao_produto': None,
            'bullet_points': [],
            'palavras_chave': [],
            'categoria': None,
            'subcategoria': None,
            'marca': None,
            'modelo': None,
            'cor': None,
            'tamanho': None,
            'material': None,
            'peso': None,
            'dimensoes': None,
            'outros_campos': {}
        }
        
        # Mapear campos comuns
        field_mappings = {
            'titulo': ['titulo', 'title', 'item_name', 'product_title', 'nome_produto'],
            'descricao_produto': ['descricao_produto', 'description', 'descricao', 'product_description'],
            'bullet_points': ['bullet_points', 'bullet_point', 'topicos', 'features', 'caracteristicas'],
            'palavras_chave': ['palavras_chave', 'keywords', 'generic_keyword', 'search_terms'],
            'categoria': ['categoria', 'category', 'product_type'],
            'subcategoria': ['subcategoria', 'subcategory', 'sub_category'],
            'marca': ['marca', 'brand', 'manufacturer'],
            'modelo': ['modelo', 'model', 'model_name'],
            'cor': ['cor', 'color', 'colour'],
            'tamanho': ['tamanho', 'size', 'size_name'],
            'material': ['material', 'fabric_type', 'material_type'],
            'peso': ['peso', 'weight', 'item_weight'],
            'dimensoes': ['dimensoes', 'dimensions', 'size_map']
        }
        
        # Aplicar mapeamentos
        for normalized_key, possible_keys in field_mappings.items():
            for key in possible_keys:
                if key in content and content[key] is not None:
                    normalized[normalized_key] = content[key]
                    break
        
        # Processar bullet points especialmente
        if isinstance(normalized['bullet_points'], str):
            # Se for string, tentar dividir em lista
            normalized['bullet_points'] = [bp.strip() for bp in normalized['bullet_points'].split('\n') if bp.strip()]
        elif not isinstance(normalized['bullet_points'], list):
            normalized['bullet_points'] = []
        
        # Processar palavras-chave
        if isinstance(normalized['palavras_chave'], str):
            # Se for string, tentar dividir em lista
            normalized['palavras_chave'] = [kw.strip() for kw in normalized['palavras_chave'].split(',') if kw.strip()]
        elif not isinstance(normalized['palavras_chave'], list):
            normalized['palavras_chave'] = []
        
        # Salvar campos não mapeados em 'outros_campos'
        mapped_keys = set()
        for keys_list in field_mappings.values():
            mapped_keys.update(keys_list)
        
        for key, value in content.items():
            if key not in mapped_keys and value is not None:
                normalized['outros_campos'][key] = value
        
        return normalized
        
    except Exception as e:
        logger.error(f"Erro ao normalizar conteúdo gerado: {e}")
        return content

def get_cached_content_or_generate(product_data: Dict[str, Any], 
                                 generation_function,
                                 force_regenerate: bool = False,
                                 **generation_kwargs) -> Dict[str, Any]:
    """
    Verifica se o produto já tem conteúdo na memória, caso contrário gera novo conteúdo.
    
    Args:
        product_data: Dados do produto
        generation_function: Função para gerar conteúdo novo
        force_regenerate: Se True, força regeneração mesmo se existir na memória
        **generation_kwargs: Argumentos para a função de geração
    
    Returns:
        Conteúdo do produto (da memória ou recém-gerado)
    """
    try:
        identifier = extract_product_identifier(product_data)
        
        # Verificar se deve usar memória
        if not force_regenerate:
            exists, saved_data = check_product_in_memory(product_data)
            
            if exists and saved_data:
                logger.info(f"Reutilizando conteúdo da memória para produto: {identifier}")
                return saved_data.get('generated_content', {})
        
        # Gerar novo conteúdo
        logger.info(f"Gerando novo conteúdo para produto: {identifier}")
        generated_content = generation_function(product_data, **generation_kwargs)
        
        # Salvar na memória
        save_generated_content_to_memory(
            product_data=product_data,
            generated_content=generated_content,
            force_update=force_regenerate
        )
        
        return generated_content
        
    except Exception as e:
        logger.error(f"Erro ao obter/gerar conteúdo: {e}")
        # Em caso de erro, tentar gerar normalmente
        try:
            return generation_function(product_data, **generation_kwargs)
        except Exception as gen_error:
            logger.error(f"Erro também na geração: {gen_error}")
            return {}

def batch_check_products_in_memory(products_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Verifica em lote quais produtos já existem na memória.
    
    Args:
        products_data: Lista de dados de produtos
    
    Returns:
        Dicionário {identificador: dados_salvos} para produtos encontrados
    """
    try:
        found_products = {}
        
        for product_data in products_data:
            try:
                identifier = extract_product_identifier(product_data)
                saved_data = product_memory.get_product_data(identifier)
                
                if saved_data:
                    found_products[identifier] = saved_data
                    
            except Exception as e:
                logger.warning(f"Erro ao verificar produto individual na memória: {e}")
                continue
        
        logger.info(f"Encontrados {len(found_products)} produtos na memória de {len(products_data)} verificados")
        return found_products
        
    except Exception as e:
        logger.error(f"Erro ao verificar produtos em lote na memória: {e}")
        return {}

def get_memory_statistics() -> Dict[str, Any]:
    """
    Retorna estatísticas da memória de produtos.
    
    Returns:
        Dicionário com estatísticas
    """
    try:
        stats = product_memory.get_memory_stats()
        
        # Adicionar estatísticas extras
        products_list = product_memory.list_products(limit=1000)
        
        stats.update({
            'total_products_sample': len(products_list),
            'products_with_title': sum(1 for p in products_list if p.get('has_title')),
            'products_with_description': sum(1 for p in products_list if p.get('has_description')),
            'products_with_bullet_points': sum(1 for p in products_list if p.get('has_bullet_points'))
        })
        
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas da memória: {e}")
        return {}

def clear_product_memory() -> bool:
    """
    Limpa toda a memória de produtos.
    
    Returns:
        True se limpou com sucesso, False caso contrário
    """
    try:
        return product_memory.clear_all_memory()
    except Exception as e:
        logger.error(f"Erro ao limpar memória de produtos: {e}")
        return False

def delete_product_from_memory(product_data: Dict[str, Any]) -> bool:
    """
    Remove um produto específico da memória.
    
    Args:
        product_data: Dados do produto
    
    Returns:
        True se removeu com sucesso, False caso contrário
    """
    try:
        identifier = extract_product_identifier(product_data)
        return product_memory.delete_product(identifier)
    except Exception as e:
        logger.error(f"Erro ao remover produto da memória: {e}")
        return False

def export_memory_data(limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Exporta dados da memória para análise ou backup.
    
    Args:
        limit: Número máximo de produtos a exportar
    
    Returns:
        Lista de produtos com dados completos
    """
    try:
        products_summary = product_memory.list_products(limit=limit)
        detailed_products = []
        
        for product_summary in products_summary:
            identifier = product_summary.get('identifier')
            if identifier:
                full_data = product_memory.get_product_data(identifier)
                if full_data:
                    detailed_products.append(full_data)
        
        logger.info(f"Exportados {len(detailed_products)} produtos da memória")
        return detailed_products
        
    except Exception as e:
        logger.error(f"Erro ao exportar dados da memória: {e}")
        return []