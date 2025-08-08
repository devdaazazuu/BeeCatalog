# 🚀 Guia Completo de Migração e Otimização - BeeCatalog

## 📋 Diagnóstico Inicial

Este guia consolida todas as otimizações implementadas no BeeCatalog, incluindo:
- ✅ Migração SQLite → PostgreSQL com connection pooling
- ✅ Sistema de cache inteligente Redis + Django-Redis
- ✅ Processamento em lote otimizado para IA
- ✅ Monitoramento com Prometheus + Grafana
- ✅ Observabilidade com Sentry + logs estruturados
- ✅ Otimizações Celery com filas dedicadas

## 🎯 Plano de Execução

### Fase 1: Preparação e Backup

#### 1.1 Backup dos Dados Atuais
```bash
# Execute o backup do SQLite
python backup_sqlite.py

# Verificar se o backup foi criado
ls backup_*/
```

#### 1.2 Instalação das Dependências
```bash
# Instalar novas dependências
pip install -r requirements.txt

# Verificar instalação
pip list | grep -E "psycopg2|redis|sentry|prometheus"
```

### Fase 2: Configuração da Infraestrutura

#### 2.1 Iniciar Serviços com Docker
```bash
# Iniciar PostgreSQL, Redis e ferramentas de monitoramento
docker-compose up -d postgres redis prometheus grafana

# Verificar status dos serviços
docker-compose ps
```

#### 2.2 Configurar Variáveis de Ambiente
```bash
# Adicionar ao .env
DATABASE_URL=postgresql://beecatalog_user:beecatalog_password@localhost:5432/beecatalog
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=your_sentry_dsn_here
DJANGO_SETTINGS_MODULE=backbeecatalog.settings
```

### Fase 3: Migração do Banco de Dados

#### 3.1 Executar Migração Automatizada
```bash
# Executar script de migração completo
python migrate_to_postgresql.py
```

#### 3.2 Restaurar Dados do Backup
```bash
# Carregar dados do backup
cd backup_YYYYMMDD_HHMMSS/
python restore_backup.py
```

#### 3.3 Verificar Integridade
```bash
# Verificar dados migrados
python manage.py shell
>>> from django.contrib.auth.models import User
>>> print(f"Usuários: {User.objects.count()}")
>>> # Verificar outras tabelas importantes
```

### Fase 4: Configuração do Celery Otimizado

#### 4.1 Iniciar Workers Especializados
```bash
# Terminal 1: Worker para planilhas (CPU intensivo)
celery -A backbeecatalog worker -Q spreadsheet --concurrency=4 --loglevel=info

# Terminal 2: Worker para scraping (I/O intensivo)
celery -A backbeecatalog worker -Q scraping --concurrency=2 --loglevel=info

# Terminal 3: Worker para IA (balanceado)
celery -A backbeecatalog worker -Q ai --concurrency=3 --loglevel=info

# Terminal 4: Flower para monitoramento
celery -A backbeecatalog flower --port=5555
```

#### 4.2 Verificar Filas
```bash
# Verificar status das filas
celery -A backbeecatalog inspect active_queues
```

### Fase 5: Teste das Otimizações

#### 5.1 Teste do Cache Inteligente
```python
# No Django shell
from api.cache_utils import get_or_cache_ai_response, get_cache_stats

# Testar cache
result = get_or_cache_ai_response(
    "test_prompt",
    lambda: "test_response",
    {"context": "test"},
    cache_ttl=300
)

# Verificar estatísticas
stats = get_cache_stats()
print(f"Cache stats: {stats}")
```

#### 5.2 Teste do Processamento em Lote
```python
# Testar nova task otimizada
from api.tasks import optimized_generate_spreadsheet_task

# Executar task otimizada
result = optimized_generate_spreadsheet_task.delay(
    produtos_data=[...],  # seus dados de teste
    user_id=1
)

print(f"Task ID: {result.id}")
```

## 🔧 Entrega: Arquivos de Configuração

### Arquivos Criados/Modificados:

1. **requirements.txt** - Dependências otimizadas
2. **settings.py** - Configurações PostgreSQL, Redis, Sentry, Prometheus
3. **celery.py** - Configurações otimizadas com filas dedicadas
4. **api/cache_utils.py** - Sistema de cache inteligente
5. **api/utils.py** - Funções IA otimizadas com cache
6. **api/tasks.py** - Tasks em lote otimizadas
7. **docker-compose.yml** - Infraestrutura completa
8. **migrate_to_postgresql.py** - Script de migração
9. **backup_sqlite.py** - Script de backup

### Configurações de Monitoramento:

10. **prometheus.yml** - Configuração de métricas
11. **redis.conf** - Redis otimizado
12. **pgbouncer.ini** - Connection pooling
13. **beecatalog_rules.yml** - Alertas Prometheus

## ⚡ Otimizações Implementadas

### 1. Performance de Banco de Dados
- **PostgreSQL** com connection pooling via PgBouncer
- **Índices otimizados** para consultas frequentes
- **Configurações de memória** ajustadas para workload

### 2. Sistema de Cache Inteligente
- **Cache em duas camadas**: Django (rápido) + Redis (persistente)
- **Cache de respostas IA** com hash SHA256 de prompts
- **Invalidação automática** e estatísticas de hit rate
- **Processamento em lote** para múltiplas requisições IA

### 3. Otimizações Celery
- **Filas dedicadas** por tipo de workload:
  - `spreadsheet`: CPU intensivo (4 workers)
  - `scraping`: I/O intensivo (2 workers)
  - `ai`: Balanceado (3 workers)
- **Configurações de performance**: prefetch, compression, retry
- **Logs estruturados** para debugging

### 4. Monitoramento e Observabilidade
- **Prometheus**: Coleta de métricas
- **Grafana**: Dashboards visuais
- **Sentry**: Tracking de erros
- **Flower**: Monitoramento Celery
- **Logs estruturados**: JSON format para análise

## 🔍 Próximos Passos

### Monitoramento Contínuo
1. **Acessar Dashboards**:
   - Grafana: http://localhost:3000 (admin/admin123)
   - Prometheus: http://localhost:9090
   - Flower: http://localhost:5555

2. **Configurar Alertas**:
   - Configurar notificações Slack/Email no Grafana
   - Ajustar thresholds de alerta conforme necessário

### Otimizações Futuras
1. **Scaling Horizontal**:
   - Configurar múltiplas instâncias Celery
   - Implementar load balancer

2. **Cache Avançado**:
   - Implementar cache de resultados de scraping
   - Cache de embeddings para busca semântica

3. **IA Otimizada**:
   - Implementar rate limiting inteligente
   - Cache de modelos pré-treinados
   - Batch processing para embeddings

### Manutenção
1. **Backup Automático**:
   - Configurar backup diário PostgreSQL
   - Rotação de logs Redis

2. **Monitoramento de Recursos**:
   - Alertas de uso de memória/CPU
   - Monitoramento de espaço em disco

## 📊 Métricas de Sucesso

### Performance Esperada
- **Redução de 60-80%** no tempo de geração de planilhas
- **Cache hit rate > 70%** para requisições IA
- **Throughput 3-5x maior** para processamento em lote
- **Redução de 50%** no uso de API IA (devido ao cache)

### Monitoramento
- **Response time < 2s** para 95% das requisições
- **Error rate < 1%** em produção
- **Uptime > 99.5%** dos serviços críticos

## 🚨 Troubleshooting

### Problemas Comuns

#### PostgreSQL não conecta
```bash
# Verificar se o serviço está rodando
docker-compose logs postgres

# Testar conexão manual
psql -h localhost -U beecatalog_user -d beecatalog
```

#### Redis não conecta
```bash
# Verificar Redis
docker-compose logs redis

# Testar conexão
redis-cli ping
```

#### Celery workers não processam
```bash
# Verificar filas
celery -A backbeecatalog inspect active_queues

# Verificar workers ativos
celery -A backbeecatalog inspect active
```

#### Cache não funciona
```python
# Verificar configuração Redis
from django.core.cache import cache
cache.set('test', 'value', 30)
print(cache.get('test'))  # Deve retornar 'value'
```

---

**🎉 Parabéns! Seu BeeCatalog agora está otimizado para alta performance e escalabilidade!**

Para suporte adicional, consulte os logs estruturados em `/var/log/beecatalog/` ou monitore via Grafana.