# Sistema de Memória Inteligente - BeeCatalog

## Visão Geral

O Sistema de Memória Inteligente é uma funcionalidade avançada que armazena e reutiliza dados de produtos processados pela IA, reduzindo significativamente o consumo de tokens e melhorando a performance do sistema.

## Características Principais

### 🧠 Armazenamento Inteligente
- **Redis**: Armazenamento primário em memória para acesso rápido
- **Cache Django**: Cache secundário para consultas frequentes
- **Backup Local**: Arquivos JSON para persistência e recuperação

### ⚡ Performance
- Redução de até 90% no consumo de tokens da IA
- Tempo de resposta até 10x mais rápido para produtos já processados
- Processamento em lote otimizado

### 🔄 Gestão Automática
- TTL (Time To Live) configurável (padrão: 90 dias)
- Limpeza automática de dados expirados
- Sincronização entre diferentes camadas de cache

## Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django Cache  │◄──►│      Redis      │◄──►│  Backup Local   │
│   (L1 Cache)    │    │   (L2 Cache)    │    │   (L3 Backup)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ ProductMemory   │
                    │     Class       │
                    └─────────────────┘
```

## Componentes

### 1. ProductMemory (`product_memory.py`)
Classe principal que gerencia o armazenamento e recuperação de dados.

**Métodos principais:**
- `save_product_data()`: Salva dados do produto
- `get_product_data()`: Recupera dados do produto
- `exists()`: Verifica se produto existe na memória
- `delete_product()`: Remove produto da memória
- `list_products()`: Lista produtos armazenados

### 2. Memory Utils (`memory_utils.py`)
Funções utilitárias para integração com o sistema.

**Funções principais:**
- `extract_product_identifier()`: Gera identificador único
- `check_product_in_memory()`: Verifica existência
- `save_generated_content_to_memory()`: Salva conteúdo gerado
- `get_cached_content_or_generate()`: Recupera ou gera conteúdo
- `batch_check_products_in_memory()`: Verificação em lote

### 3. Memory Views (`memory_views.py`)
APIs REST para gerenciamento via interface web.

**Endpoints disponíveis:**
- `GET /api/memory/stats/`: Estatísticas da memória
- `POST /api/memory/clear/`: Limpar toda a memória
- `POST /api/memory/delete/`: Remover produto específico
- `GET /api/memory/export/`: Exportar dados
- `GET /api/memory/list/`: Listar produtos
- `POST /api/memory/get/`: Obter dados de produto
- `POST /api/memory/force-regenerate/`: Forçar regeneração
- `GET /api/memory/health/`: Health check

### 4. Management Command (`manage_memory.py`)
Comando Django para administração via terminal.

## Como Usar

### Via API REST

#### Obter Estatísticas
```bash
curl -X GET http://localhost:8000/api/memory/stats/
```

#### Listar Produtos na Memória
```bash
curl -X GET "http://localhost:8000/api/memory/list/?limit=50"
```

#### Obter Dados de um Produto
```bash
curl -X POST http://localhost:8000/api/memory/get/ \
  -H "Content-Type: application/json" \
  -d '{"product_data": {"sku": "ABC123", "title": "Produto Teste"}}'
```

#### Forçar Regeneração
```bash
curl -X POST http://localhost:8000/api/memory/force-regenerate/ \
  -H "Content-Type: application/json" \
  -d '{"product_data": {"sku": "ABC123"}}'
```

#### Limpar Memória
```bash
curl -X POST http://localhost:8000/api/memory/clear/
```

### Via Command Line

#### Mostrar Estatísticas
```bash
python manage.py manage_memory stats
```

#### Listar Produtos
```bash
python manage.py manage_memory list --limit 100
```

#### Exportar Dados
```bash
python manage.py manage_memory export --limit 1000 --output-file backup.json
```

#### Health Check
```bash
python manage.py manage_memory health
```

#### Limpar Memória
```bash
python manage.py manage_memory clear --confirm
```

#### Remover Produto Específico
```bash
python manage.py manage_memory delete --product-id "ABC123" --confirm
```

## Integração com Tarefas Existentes

### Processamento Individual
```python
# Usar memória inteligente
result = generate_main_content_task.delay(
    product_data, 
    force_regenerate=False  # Usar cache se disponível
)

# Forçar regeneração
result = generate_main_content_task.delay(
    product_data, 
    force_regenerate=True   # Ignorar cache
)
```

### Processamento em Lote
```python
# Processamento otimizado com memória
result = batch_generate_main_content_task.delay(
    products_list, 
    batch_size=10,
    force_regenerate=False
)
```

## Configuração

### Variáveis de Ambiente
```bash
# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Diretório de backup (opcional)
MEMORY_BACKUP_DIR=/path/to/memory/backup

# TTL padrão em segundos (opcional)
MEMORY_DEFAULT_TTL=7776000  # 90 dias
```

### Settings Django
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Monitoramento

### Métricas Importantes
- **Taxa de Cache Hit**: Percentual de produtos encontrados na memória
- **Economia de Tokens**: Tokens economizados vs. tokens que seriam usados
- **Tempo de Resposta**: Comparação entre cache hit e miss
- **Uso de Memória**: Consumo de Redis e espaço em disco

### Logs
O sistema gera logs detalhados para monitoramento:
```
[INFO] Produto ABC123 encontrado na memória - economia de 1500 tokens
[INFO] Processamento em lote: 8/10 produtos reutilizados da memória
[INFO] Salvando produto XYZ789 na memória para reutilização futura
```

## Troubleshooting

### Problemas Comuns

#### Redis Não Conecta
```bash
# Verificar se Redis está rodando
redis-cli ping

# Health check do sistema
python manage.py manage_memory health
```

#### Memória Cheia
```bash
# Verificar uso
python manage.py manage_memory stats

# Limpar dados antigos
python manage.py manage_memory clear --confirm
```

#### Performance Degradada
```bash
# Verificar estatísticas
curl -X GET http://localhost:8000/api/memory/stats/

# Exportar dados para análise
python manage.py manage_memory export --output-file analysis.json
```

## Benefícios

### 💰 Economia de Custos
- Redução significativa no consumo de tokens da IA
- Menor uso de recursos computacionais
- Otimização de custos operacionais

### ⚡ Performance
- Resposta instantânea para produtos já processados
- Processamento em lote mais eficiente
- Menor latência geral do sistema

### 🔄 Escalabilidade
- Suporte a milhares de produtos
- Distribuição de carga entre camadas
- Crescimento horizontal facilitado

### 🛡️ Confiabilidade
- Múltiplas camadas de backup
- Recuperação automática de falhas
- Consistência de dados garantida

## Roadmap

### Próximas Funcionalidades
- [ ] Compressão de dados para otimizar armazenamento
- [ ] Métricas avançadas e dashboards
- [ ] Sincronização entre múltiplas instâncias
- [ ] Cache preditivo baseado em padrões de uso
- [ ] API GraphQL para consultas complexas
- [ ] Integração com sistemas de monitoramento externos

---

**Desenvolvido para BeeCatalog** - Sistema de Memória Inteligente v1.0