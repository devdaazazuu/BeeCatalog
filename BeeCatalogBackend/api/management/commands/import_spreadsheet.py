# api/management/commands/import_spreadsheet.py

import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from api.spreadsheet_importer import spreadsheet_importer
from api.memory_utils import get_memory_statistics

class Command(BaseCommand):
    help = 'Importa dados de planilhas para o sistema de memória inteligente'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Caminho para o arquivo da planilha (CSV, Excel)'
        )
        
        parser.add_argument(
            '--sheet-name',
            type=str,
            help='Nome da planilha (para arquivos Excel)'
        )
        
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Apenas visualizar preview dos dados sem importar'
        )
        
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Forçar atualização de produtos existentes'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Tamanho do lote para processamento (padrão: 100)'
        )
        
        parser.add_argument(
            '--sample-size',
            type=int,
            default=5,
            help='Número de linhas para preview (padrão: 5)'
        )
        
        parser.add_argument(
            '--columns',
            action='store_true',
            help='Mostrar informações sobre as colunas da planilha'
        )
        
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostrar estatísticas da memória antes e depois'
        )
    
    def handle(self, *args, **options):
        file_path = options['file_path']
        sheet_name = options.get('sheet_name')
        preview_only = options['preview']
        force_update = options['force_update']
        batch_size = options['batch_size']
        sample_size = options['sample_size']
        show_columns = options['columns']
        show_stats = options['stats']
        
        # Verificar se arquivo existe
        if not os.path.exists(file_path):
            raise CommandError(f'Arquivo não encontrado: {file_path}')
        
        # Verificar formato suportado
        if not any(file_path.lower().endswith(ext) for ext in spreadsheet_importer.supported_formats):
            raise CommandError(
                f'Formato não suportado. Use: {", ".join(spreadsheet_importer.supported_formats)}'
            )
        
        try:
            # Mostrar estatísticas iniciais se solicitado
            if show_stats:
                self.stdout.write(self.style.SUCCESS('\n=== ESTATÍSTICAS INICIAIS DA MEMÓRIA ==='))
                initial_stats = get_memory_statistics()
                self._display_stats(initial_stats)
            
            # Se for Excel, mostrar planilhas disponíveis
            if file_path.lower().endswith(('.xlsx', '.xls')):
                sheet_names = spreadsheet_importer.get_sheet_names(file_path)
                self.stdout.write(f'\nPlanilhas disponíveis: {", ".join(sheet_names)}')
                
                if not sheet_name and len(sheet_names) > 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Múltiplas planilhas encontradas. Usando a primeira: {sheet_names[0]}'
                        )
                    )
                    sheet_name = sheet_names[0]
            
            # Mostrar informações das colunas
            if show_columns:
                self.stdout.write(self.style.SUCCESS('\n=== ANÁLISE DAS COLUNAS ==='))
                df = spreadsheet_importer.read_spreadsheet(file_path, sheet_name)
                column_mapping = spreadsheet_importer.map_columns(df)
                
                self.stdout.write(f'Total de linhas: {len(df)}')
                self.stdout.write(f'Total de colunas: {len(df.columns)}')
                self.stdout.write('\nMapeamento de colunas:')
                
                for standard_field, original_col in column_mapping.items():
                    if original_col:
                        non_null = df[original_col].count()
                        self.stdout.write(f'  {standard_field} ← {original_col} ({non_null} valores)')
                
                unmapped_cols = [col for col in df.columns if col not in column_mapping.values()]
                if unmapped_cols:
                    self.stdout.write('\nColunas não mapeadas:')
                    for col in unmapped_cols:
                        self.stdout.write(f'  {col}')
            
            # Preview dos dados
            if preview_only:
                self.stdout.write(self.style.SUCCESS('\n=== PREVIEW DOS DADOS ==='))
                preview_data = spreadsheet_importer.preview_import(
                    file_path, sheet_name, sample_size
                )
                
                self.stdout.write(f'Arquivo: {file_path}')
                if sheet_name:
                    self.stdout.write(f'Planilha: {sheet_name}')
                self.stdout.write(f'Total de linhas: {preview_data["total_rows"]}')
                self.stdout.write(f'Linhas válidas: {preview_data["valid_rows"]}')
                self.stdout.write(f'Produtos identificados: {preview_data["identified_products"]}')
                
                if preview_data['sample_products']:
                    self.stdout.write('\nAmostra de produtos:')
                    for i, product in enumerate(preview_data['sample_products'], 1):
                        self.stdout.write(f'\n  Produto {i}:')
                        for key, value in product.items():
                            if value:
                                display_value = str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                                self.stdout.write(f'    {key}: {display_value}')
                
                if preview_data['errors']:
                    self.stdout.write(self.style.WARNING('\nErros encontrados:'))
                    for error in preview_data['errors'][:5]:  # Mostrar apenas os primeiros 5
                        self.stdout.write(f'  {error}')
                
                return
            
            # Importação real
            self.stdout.write(self.style.SUCCESS('\n=== INICIANDO IMPORTAÇÃO ==='))
            self.stdout.write(f'Arquivo: {file_path}')
            if sheet_name:
                self.stdout.write(f'Planilha: {sheet_name}')
            self.stdout.write(f'Forçar atualização: {"Sim" if force_update else "Não"}')
            self.stdout.write(f'Tamanho do lote: {batch_size}')
            
            # Confirmar importação
            if not force_update:
                confirm = input('\nDeseja continuar com a importação? (s/N): ')
                if confirm.lower() not in ['s', 'sim', 'y', 'yes']:
                    self.stdout.write('Importação cancelada.')
                    return
            
            # Executar importação
            import_stats = spreadsheet_importer.import_to_memory(
                file_path=file_path,
                sheet_name=sheet_name,
                force_update=force_update,
                batch_size=batch_size
            )
            
            # Mostrar resultados
            self.stdout.write(self.style.SUCCESS('\n=== IMPORTAÇÃO CONCLUÍDA ==='))
            self.stdout.write(f'Produtos importados: {import_stats["imported"]}')
            self.stdout.write(f'Produtos atualizados: {import_stats["updated"]}')
            self.stdout.write(f'Produtos ignorados: {import_stats["skipped"]}')
            self.stdout.write(f'Erros: {import_stats["errors"]}')
            self.stdout.write(f'Total processado: {import_stats["total_processed"]}')
            
            if import_stats['error_details']:
                self.stdout.write(self.style.WARNING('\nDetalhes dos erros:'))
                for error in import_stats['error_details'][:10]:  # Mostrar apenas os primeiros 10
                    self.stdout.write(f'  {error}')
            
            # Mostrar estatísticas finais se solicitado
            if show_stats:
                self.stdout.write(self.style.SUCCESS('\n=== ESTATÍSTICAS FINAIS DA MEMÓRIA ==='))
                final_stats = get_memory_statistics()
                self._display_stats(final_stats)
            
        except Exception as e:
            raise CommandError(f'Erro durante a importação: {e}')
    
    def _display_stats(self, stats):
        """Exibe estatísticas da memória de forma formatada."""
        self.stdout.write(f'Total de produtos na memória: {stats["total_products"]}')
        self.stdout.write(f'Produtos com conteúdo gerado: {stats["products_with_content"]}')
        self.stdout.write(f'Uso de memória: {stats["memory_usage"]}')
        self.stdout.write(f'Cache hits: {stats["cache_hits"]}')
        self.stdout.write(f'Cache misses: {stats["cache_misses"]}')
        
        if stats['storage_info']:
            self.stdout.write('\nInformações de armazenamento:')
            for storage_type, info in stats['storage_info'].items():
                if isinstance(info, dict):
                    self.stdout.write(f'  {storage_type}: {info.get("status", "N/A")}')
                else:
                    self.stdout.write(f'  {storage_type}: {info}')