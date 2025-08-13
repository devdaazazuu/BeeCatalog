# Guia de Importação de Planilhas - BeeCatalog

## Visão Geral

O sistema de importação de planilhas do BeeCatalog permite que você importe dados de produtos diretamente de arquivos CSV e Excel para o sistema de memória inteligente. Isso acelera significativamente o processo de catalogação e geração de conteúdo.

## Formatos Suportados

- **CSV** (.csv)
- **Excel** (.xlsx, .xls)

## Campos Reconhecidos

O sistema reconhece automaticamente as seguintes colunas (em português e inglês):

### Campos Obrigatórios
- **SKU**: `sku`, `código`, `code`, `id`, `product_id`
- **Título/Nome**: `title`, `name`, `título`, `nome`, `product_name`

### Campos Recomendados
- **Descrição**: `description`, `descrição`, `desc`
- **Preço**: `price`, `preço`, `valor`, `value`
- **Marca**: `brand`, `marca`, `manufacturer`
- **Categoria**: `category`, `categoria`, `type`, `tipo`

### Campos Opcionais
- **Palavras-chave**: `keywords`, `palavras-chave`, `tags`
- **Características**: `bullet_points`, `características`, `features`
- **Especificações**: `specifications`, `especificações`, `specs`

## Como Usar

### 1. Via Interface Web (API REST)

#### Fazer Preview da Planilha
```bash
POST /api/spreadsheet/preview/
Content-Type: multipart/form-data

file: [arquivo da planilha]
sheet_name: [nome da planilha] (opcional, para Excel)
sample_size: [número de linhas para preview] (padrão: 5)
```

#### Analisar Colunas
```bash
POST /api/spreadsheet/columns/
Content-Type: multipart/form-data

file: [arquivo da planilha]
sheet_name: [nome da planilha] (opcional)
```

#### Importar Planilha
```bash
POST /api/spreadsheet/import/
Content-Type: multipart/form-data

file: [arquivo da planilha]
sheet_name: [nome da planilha] (opcional)
force_update: [true/false] (padrão: false)
batch_size: [tamanho do lote] (padrão: 100)
```

#### Baixar Template
```bash
GET /api/import/template/
```

### 2. Via Linha de Comando

#### Preview dos Dados
```bash
python manage.py import_spreadsheet caminho/para/planilha.xlsx --preview
```

#### Analisar Colunas
```bash
python manage.py import_spreadsheet caminho/para/planilha.xlsx --columns
```

#### Importar com Estatísticas
```bash
python manage.py import_spreadsheet caminho/para/planilha.xlsx --stats
```

#### Importar Forçando Atualização
```bash
python manage.py import_spreadsheet caminho/para/planilha.xlsx --force-update
```

#### Importar Planilha Específica do Excel
```bash
python manage.py import_spreadsheet arquivo.xlsx --sheet-name "Produtos" --batch-size 50
```

## Exemplos Práticos

### Estrutura de Planilha Recomendada

| SKU     | Título              | Descrição                    | Preço  | Marca   | Categoria   |
|---------|---------------------|------------------------------|--------|---------|-------------|
| PROD001 | Smartphone XYZ      | Smartphone com 128GB         | 899.99 | TechCorp| Eletrônicos |
| PROD002 | Fone Bluetooth      | Fone sem fio com cancelamento| 299.99 | AudioMax| Áudio       |
| PROD003 | Camiseta Esportiva  | Camiseta dry-fit para corrida| 79.99  | SportWear| Roupas     |

### Exemplo com Campos Avançados

| SKU | Nome | Descrição | Preço | Marca | Palavras-chave | Características |
|-----|------|-----------|-------|-------|----------------|----------------|
| ABC123 | Notebook Gamer | Notebook para jogos | 2999.99 | GamerTech | gaming, notebook, performance | Placa de vídeo dedicada; 16GB RAM; SSD 512GB |

## Fluxo de Trabalho Recomendado

### 1. Preparação
1. **Organize sua planilha** com as colunas reconhecidas pelo sistema
2. **Baixe o template** se necessário: `GET /api/import/template/`
3. **Certifique-se** de que pelo menos SKU e Título estão preenchidos

### 2. Validação
1. **Faça um preview** primeiro: `--preview` ou `/api/spreadsheet/preview/`
2. **Analise as colunas** mapeadas: `--columns` ou `/api/spreadsheet/columns/`
3. **Verifique** se o mapeamento está correto

### 3. Importação
1. **Importe em lotes pequenos** primeiro para testar
2. **Use force_update=false** inicialmente para evitar sobrescrever dados
3. **Monitore as estatísticas** com `--stats`

### 4. Verificação
1. **Verifique a memória**: `python manage.py manage_memory stats`
2. **Teste a geração** de conteúdo para alguns produtos
3. **Ajuste** se necessário e reimporte com `force_update=true`

## Tratamento de Erros

### Erros Comuns

1. **"Nenhuma coluna de identificação encontrada"**
   - Certifique-se de ter pelo menos uma coluna SKU ou Título
   - Verifique se os nomes das colunas estão corretos

2. **"Formato não suportado"**
   - Use apenas CSV, XLSX ou XLS
   - Verifique a extensão do arquivo

3. **"Planilha não encontrada"**
   - Para Excel, especifique o nome correto da planilha
   - Use `--columns` para ver planilhas disponíveis

4. **"Dados duplicados"**
   - Use `force_update=true` para sobrescrever
   - Ou limpe a memória antes: `python manage.py manage_memory clear`

### Logs e Debugging

- **Logs detalhados** são salvos no sistema de logging do Django
- **Use --preview** para identificar problemas antes da importação
- **Analise as estatísticas** para monitorar o desempenho

## Integração com Sistema de Memória

### Como Funciona
1. **Dados são importados** para o sistema de memória inteligente
2. **Conteúdo é gerado** automaticamente quando solicitado
3. **Cache inteligente** evita regeneração desnecessária
4. **Backup local** garante disponibilidade mesmo sem Redis

### Benefícios
- **Economia massiva de tokens** de IA
- **Geração mais rápida** de conteúdo
- **Consistência** nos dados de produtos
- **Escalabilidade** para milhares de produtos

## Monitoramento e Manutenção

### Comandos Úteis

```bash
# Ver estatísticas da memória
python manage.py manage_memory stats

# Listar produtos na memória
python manage.py manage_memory list --limit 10

# Exportar dados da memória
python manage.py manage_memory export --output backup.json

# Verificar saúde do sistema
python manage.py manage_memory health

# Limpar memória (cuidado!)
python manage.py manage_memory clear --confirm
```

### APIs de Monitoramento

```bash
# Estatísticas via API
GET /api/memory/stats/

# Listar produtos
GET /api/memory/products/

# Verificar saúde
GET /api/memory/health/
```

## Dicas e Melhores Práticas

### Preparação de Dados
1. **Limpe os dados** antes da importação (remova caracteres especiais desnecessários)
2. **Padronize formatos** (preços, datas, etc.)
3. **Use encoding UTF-8** para CSV
4. **Evite células mescladas** no Excel

### Performance
1. **Importe em lotes** de 100-500 produtos por vez
2. **Use force_update=false** para importações incrementais
3. **Monitore o uso de memória** regularmente
4. **Faça backup** dos dados importantes

### Manutenção
1. **Agende limpezas** periódicas da memória
2. **Monitore logs** para identificar problemas
3. **Teste importações** em ambiente de desenvolvimento primeiro
4. **Mantenha templates** atualizados

## Solução de Problemas

### Performance Lenta
- Reduza o `batch_size`
- Verifique disponibilidade do Redis
- Monitore uso de CPU/memória

### Erros de Memória
- Limpe cache antigo
- Reinicie o Redis se necessário
- Verifique configurações do Django

### Dados Inconsistentes
- Use `force_update=true` para reprocessar
- Verifique mapeamento de colunas
- Valide dados de origem

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs do Django
2. Use comandos de diagnóstico (`--preview`, `--columns`, `health`)
3. Consulte a documentação da API
4. Execute testes com dados pequenos primeiro