# api/management/commands/manage_memory.py

import json
from django.core.management.base import BaseCommand, CommandError
from api.memory_utils import (
    get_memory_statistics,
    clear_product_memory,
    delete_product_from_memory,
    export_memory_data,
    extract_product_identifier
)
from api.product_memory import product_memory

class Command(BaseCommand):
    help = 'Gerencia o sistema de memória inteligente de produtos'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['stats', 'clear', 'list', 'export', 'delete', 'health'],
            help='Ação a ser executada'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limite de resultados para list e export (padrão: 100)'
        )
        
        parser.add_argument(
            '--product-id',
            type=str,
            help='ID do produto para operações específicas'
        )
        
        parser.add_argument(
            '--output-file',
            type=str,
            help='Arquivo de saída para export (formato JSON)'
        )
        
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma operações destrutivas sem prompt'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'stats':
                self.show_stats()
            elif action == 'clear':
                self.clear_memory(options['confirm'])
            elif action == 'list':
                self.list_products(options['limit'])
            elif action == 'export':
                self.export_data(options['limit'], options['output_file'])
            elif action == 'delete':
                self.delete_product(options['product_id'], options['confirm'])
            elif action == 'health':
                self.health_check()
                
        except Exception as e:
            raise CommandError(f'Erro ao executar comando: {e}')

    def show_stats(self):
        """Mostra estatísticas da memória."""
        self.stdout.write(self.style.SUCCESS('\n=== Estatísticas da Memória Inteligente ===\n'))
        
        stats = get_memory_statistics()
        
        self.stdout.write(f"Redis conectado: {stats.get('redis_connected', False)}")
        self.stdout.write(f"Produtos no Redis: {stats.get('redis_products', 0)}")
        self.stdout.write(f"Backups locais: {stats.get('local_backups', 0)}")
        self.stdout.write(f"Diretório de memória: {stats.get('memory_dir', 'N/A')}")
        
        if 'redis_memory_usage' in stats:
            self.stdout.write(f"Uso de memória Redis: {stats['redis_memory_usage']}")
        
        if 'oldest_entry' in stats:
            self.stdout.write(f"Entrada mais antiga: {stats['oldest_entry']}")
        
        if 'newest_entry' in stats:
            self.stdout.write(f"Entrada mais recente: {stats['newest_entry']}")

    def clear_memory(self, confirm):
        """Limpa toda a memória."""
        if not confirm:
            response = input('\nTem certeza que deseja limpar TODA a memória? (sim/não): ')
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write(self.style.WARNING('Operação cancelada.'))
                return
        
        self.stdout.write('Limpando memória...')
        success = clear_product_memory()
        
        if success:
            self.stdout.write(self.style.SUCCESS('Memória limpa com sucesso!'))
        else:
            self.stdout.write(self.style.ERROR('Falha ao limpar memória.'))

    def list_products(self, limit):
        """Lista produtos na memória."""
        self.stdout.write(self.style.SUCCESS(f'\n=== Produtos na Memória (limite: {limit}) ===\n'))
        
        products = product_memory.list_products(limit=limit)
        
        if not products:
            self.stdout.write(self.style.WARNING('Nenhum produto encontrado na memória.'))
            return
        
        for i, product_id in enumerate(products, 1):
            self.stdout.write(f"{i:3d}. {product_id}")
        
        self.stdout.write(f'\nTotal: {len(products)} produtos')

    def export_data(self, limit, output_file):
        """Exporta dados da memória."""
        self.stdout.write(f'Exportando dados (limite: {limit})...')
        
        data = export_memory_data(limit=limit)
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.stdout.write(self.style.SUCCESS(f'Dados exportados para: {output_file}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao salvar arquivo: {e}'))
        else:
            # Mostrar no terminal (limitado)
            self.stdout.write(self.style.SUCCESS(f'\n=== Dados Exportados ({len(data)} produtos) ===\n'))
            
            for product_id, product_data in list(data.items())[:10]:  # Mostrar apenas os primeiros 10
                self.stdout.write(f"ID: {product_id}")
                if 'title' in product_data:
                    self.stdout.write(f"  Título: {product_data['title'][:50]}...")
                if 'created_at' in product_data:
                    self.stdout.write(f"  Criado em: {product_data['created_at']}")
                self.stdout.write('')
            
            if len(data) > 10:
                self.stdout.write(f'... e mais {len(data) - 10} produtos.')
                self.stdout.write('\nUse --output-file para exportar todos os dados.')

    def delete_product(self, product_id, confirm):
        """Remove um produto específico da memória."""
        if not product_id:
            raise CommandError('--product-id é obrigatório para a ação delete')
        
        if not confirm:
            response = input(f'\nTem certeza que deseja remover o produto "{product_id}"? (sim/não): ')
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write(self.style.WARNING('Operação cancelada.'))
                return
        
        # Criar um product_data fictício com o ID
        product_data = {'sku': product_id}
        
        success = delete_product_from_memory(product_data)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Produto "{product_id}" removido da memória.'))
        else:
            self.stdout.write(self.style.ERROR(f'Falha ao remover produto "{product_id}" ou produto não encontrado.'))

    def health_check(self):
        """Verifica a saúde do sistema de memória."""
        self.stdout.write(self.style.SUCCESS('\n=== Health Check da Memória Inteligente ===\n'))
        
        try:
            stats = get_memory_statistics()
            
            # Verificar Redis
            redis_status = '✓ Conectado' if stats.get('redis_connected', False) else '✗ Desconectado'
            self.stdout.write(f"Redis: {redis_status}")
            
            # Verificar backups locais
            local_backups = stats.get('local_backups', 0)
            backup_status = f'✓ {local_backups} backups' if local_backups > 0 else '⚠ Nenhum backup'
            self.stdout.write(f"Backups locais: {backup_status}")
            
            # Verificar diretório
            memory_dir = stats.get('memory_dir', 'N/A')
            self.stdout.write(f"Diretório: {memory_dir}")
            
            # Status geral
            if stats.get('redis_connected', False) or local_backups > 0:
                self.stdout.write(self.style.SUCCESS('\n✓ Sistema de memória funcionando'))
            else:
                self.stdout.write(self.style.ERROR('\n✗ Sistema de memória com problemas'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Erro no health check: {e}'))