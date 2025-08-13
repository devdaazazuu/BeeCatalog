# api/spreadsheet_importer.py

import pandas as pd
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .memory_utils import (
    extract_product_identifier,
    save_generated_content_to_memory,
    normalize_generated_content
)
from .product_memory import product_memory

logger = logging.getLogger(__name__)

class SpreadsheetImporter:
    """
    Classe para importar planilhas preenchidas e popular o sistema de memória inteligente.
    """
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.field_mappings = {
            # Mapeamentos de campos comuns em planilhas
            'sku': ['sku', 'SKU', 'codigo', 'código', 'product_id', 'id_produto'],
            'title': ['titulo', 'título', 'title', 'nome', 'name', 'produto', 'product_name'],
            'description': ['descricao', 'descrição', 'description', 'desc', 'detalhes'],
            'price': ['preco', 'preço', 'price', 'valor', 'value'],
            'brand': ['marca', 'brand', 'fabricante', 'manufacturer'],
            'category': ['categoria', 'category', 'cat', 'tipo', 'type'],
            'model': ['modelo', 'model', 'mod'],
            'weight': ['peso', 'weight', 'massa'],
            'dimensions': ['dimensoes', 'dimensões', 'dimensions', 'medidas'],
            'color': ['cor', 'color', 'colour'],
            'material': ['material', 'materials', 'materiais'],
            'keywords': ['palavras_chave', 'keywords', 'tags', 'etiquetas'],
            'bullet_points': ['pontos_principais', 'bullet_points', 'caracteristicas', 'características'],
            'specifications': ['especificacoes', 'especificações', 'specifications', 'specs']
        }
    
    def detect_file_format(self, file_path: str) -> str:
        """
        Detecta o formato do arquivo.
        """
        if file_path.lower().endswith('.csv'):
            return 'csv'
        elif file_path.lower().endswith(('.xlsx', '.xls')):
            return 'excel'
        else:
            raise ValueError(f"Formato de arquivo não suportado: {file_path}")
    
    def read_spreadsheet(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lê a planilha e retorna um DataFrame.
        """
        try:
            file_format = self.detect_file_format(file_path)
            
            if file_format == 'csv':
                # Tentar diferentes encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.info(f"Arquivo CSV lido com encoding: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Não foi possível ler o arquivo CSV com nenhum encoding suportado")
            
            elif file_format == 'excel':
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    df = pd.read_excel(file_path)
            
            logger.info(f"Planilha lida com sucesso: {len(df)} linhas, {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao ler planilha {file_path}: {e}")
            raise
    
    def map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Mapeia as colunas da planilha para os campos padrão.
        """
        column_mapping = {}
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        for standard_field, possible_names in self.field_mappings.items():
            for possible_name in possible_names:
                if possible_name.lower() in df_columns_lower:
                    # Encontrar o nome original da coluna
                    original_col = df.columns[df_columns_lower.index(possible_name.lower())]
                    column_mapping[standard_field] = original_col
                    break
        
        logger.info(f"Mapeamento de colunas detectado: {column_mapping}")
        return column_mapping
    
    def clean_and_validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e valida os dados da planilha.
        """
        # Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        # Remover espaços em branco extras
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            # Substituir 'nan' string por NaN real
            df[col] = df[col].replace('nan', pd.NA)
        
        # Converter valores numéricos
        numeric_fields = ['price', 'weight']
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')
        
        logger.info(f"Dados limpos: {len(df)} linhas válidas")
        return df
    
    def convert_to_product_data(self, df, column_mapping):
        """Converte DataFrame em lista de dados de produtos."""
        products = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                product_data = self.row_to_product_data(row, column_mapping)
                if product_data:
                    products.append(product_data)
                
            except Exception as e:
                errors.append(f"Linha {index + 2}: {str(e)}")
        
        return products, errors
    
    def row_to_product_data(self, row, column_mapping):
        """Converte uma linha do DataFrame em dados de produto."""
        product_data = {}
        
        # Mapear campos padrão
        for standard_field, original_col in column_mapping.items():
            if original_col and original_col in row:
                value = row[original_col]
                if pd.notna(value) and str(value).strip():
                    product_data[standard_field] = str(value).strip()
        
        # Verificar se tem pelo menos um identificador
        if not any(product_data.get(field) for field in ['sku', 'title', 'name']):
            return None
        
        # Processar campos especiais
        if 'bullet_points' in product_data:
            # Converter características em lista
            bullet_points = product_data['bullet_points']
            if ';' in bullet_points:
                product_data['bullet_points'] = [bp.strip() for bp in bullet_points.split(';')]
            elif ',' in bullet_points:
                product_data['bullet_points'] = [bp.strip() for bp in bullet_points.split(',')]
            else:
                product_data['bullet_points'] = [bullet_points]
        
        if 'keywords' in product_data:
            # Converter palavras-chave em lista
            keywords = product_data['keywords']
            if ',' in keywords:
                product_data['keywords'] = [kw.strip() for kw in keywords.split(',')]
            else:
                product_data['keywords'] = [keywords]
        
        # Converter preço para float se possível
        if 'price' in product_data:
            try:
                price_str = product_data['price'].replace(',', '.').replace('R$', '').strip()
                product_data['price'] = float(price_str)
            except (ValueError, AttributeError):
                pass
        
        return product_data
    
    def import_to_memory(self, file_path: str, sheet_name: Optional[str] = None, 
                        force_update: bool = False, batch_size: int = 100) -> Dict[str, Any]:
        """
        Importa dados da planilha para o sistema de memória inteligente.
        """
        try:
            start_time = datetime.now()
            
            # Ler planilha
            df = self.read_spreadsheet(file_path, sheet_name)
            
            # Mapear colunas
            column_mapping = self.map_columns(df)
            
            if not column_mapping:
                raise ValueError("Nenhuma coluna reconhecida foi encontrada na planilha")
            
            # Limpar dados
            df = self.clean_and_validate_data(df)
            
            # Estatísticas de importação
            stats = {
                'total_rows': len(df),
                'imported': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0,
                'error_details': []
            }
            
            # Processar em lotes
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                
                for idx, row in batch_df.iterrows():
                    try:
                        # Converter para dados de produto
                        product_data = self.convert_to_product_data(row, column_mapping)
                        
                        # Verificar se tem dados mínimos necessários
                        if not any(field in product_data for field in ['sku', 'title', 'name']):
                            stats['skipped'] += 1
                            continue
                        
                        # Extrair identificador
                        identifier = extract_product_identifier(product_data)
                        
                        # Verificar se já existe
                        exists = product_memory.exists(identifier)
                        
                        if exists and not force_update:
                            stats['skipped'] += 1
                            continue
                        
                        # Normalizar conteúdo
                        normalized_content = normalize_generated_content(product_data)
                        
                        # Salvar na memória
                        success = save_generated_content_to_memory(
                            product_data=product_data,
                            generated_content=normalized_content,
                            force_update=force_update
                        )
                        
                        if success:
                            if exists:
                                stats['updated'] += 1
                            else:
                                stats['imported'] += 1
                        else:
                            stats['errors'] += 1
                            stats['error_details'].append(f"Falha ao salvar produto: {identifier}")
                    
                    except Exception as e:
                        stats['errors'] += 1
                        error_msg = f"Erro na linha {idx}: {str(e)}"
                        stats['error_details'].append(error_msg)
                        logger.error(error_msg)
                
                # Log de progresso
                processed = min(i + batch_size, len(df))
                logger.info(f"Processadas {processed}/{len(df)} linhas")
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            stats.update({
                'processing_time_seconds': processing_time,
                'file_path': file_path,
                'sheet_name': sheet_name,
                'column_mapping': column_mapping,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            })
            
            logger.info(f"Importação concluída: {stats['imported']} importados, {stats['updated']} atualizados, {stats['skipped']} ignorados, {stats['errors']} erros")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro durante importação: {e}")
            raise
    
    def preview_import(self, file_path: str, sheet_name: Optional[str] = None, 
                      sample_size: int = 5) -> Dict[str, Any]:
        """
        Faz uma prévia da importação sem salvar dados.
        """
        try:
            # Ler apenas uma amostra
            df = self.read_spreadsheet(file_path, sheet_name)
            sample_df = df.head(sample_size)
            
            # Mapear colunas
            column_mapping = self.map_columns(df)
            
            # Limpar dados da amostra
            sample_df = self.clean_and_validate_data(sample_df)
            
            # Converter amostras
            sample_products = []
            for idx, row in sample_df.iterrows():
                try:
                    product_data = self.convert_to_product_data(row, column_mapping)
                    identifier = extract_product_identifier(product_data)
                    sample_products.append({
                        'identifier': identifier,
                        'data': product_data
                    })
                except Exception as e:
                    sample_products.append({
                        'error': str(e),
                        'row_index': idx
                    })
            
            return {
                'total_rows': len(df),
                'sample_size': len(sample_df),
                'column_mapping': column_mapping,
                'available_columns': list(df.columns),
                'sample_products': sample_products,
                'file_info': {
                    'path': file_path,
                    'sheet_name': sheet_name,
                    'format': self.detect_file_format(file_path)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro durante preview: {e}")
            raise
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        Retorna os nomes das planilhas em um arquivo Excel.
        """
        try:
            if self.detect_file_format(file_path) == 'excel':
                excel_file = pd.ExcelFile(file_path)
                return excel_file.sheet_names
            else:
                return []
        except Exception as e:
            logger.error(f"Erro ao obter nomes das planilhas: {e}")
            return []

# Instância global
spreadsheet_importer = SpreadsheetImporter()