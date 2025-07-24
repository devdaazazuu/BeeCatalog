# Especificação: Prevenção de Preenchimento Automático de Campos de Unidade

## Problema Identificado
Os modelos de IA estavam preenchendo automaticamente campos de unidade de medida (como 'Unidade de altura', 'Unidade de peso', etc.) mesmo quando essa informação não estava explicitamente disponível no contexto do produto.

## Soluções Implementadas

### 1. Modificações nos Prompts da IA

#### 1.1 Prompt Principal (`prompt_final` em `api/utils.py`)
Adicionada nova regra (Regra 6):
```
6. **CAMPOS DE UNIDADE:** NUNCA preencha automaticamente campos que contenham 'Unidade' no nome (ex: 'Unidade de altura', 'Unidade de peso', etc.) a menos que seja explicitamente fornecido no contexto do produto. Para campos de unidade sem informação específica, sempre use 'nan'.
```

#### 1.2 Prompt da Função `escolher_com_ia`
Adicionada regra específica:
```
- CAMPOS DE UNIDADE: NUNCA preencha automaticamente campos que contenham 'Unidade' no nome (ex: 'Unidade de altura', 'Unidade de peso', etc.) a menos que seja explicitamente fornecido no contexto do produto. Para campos de unidade sem informação específica, sempre use 'nan'.
```

### 2. Correções na Lógica de Preenchimento

#### 2.1 Função `preencher_dimensoes`
Modificada para preencher unidades apenas quando o cabeçalho contém "pacote" ou "item":
```python
if campos_unidade and tem_valores_validos:
    for i, campo_unidade in enumerate(campos_unidade):
        if i < len(valores) and valores[i] is not None:
            cabecalho_unidade = campo_unidade.lower()
            # CORREÇÃO: Só preencher unidades se for específico para pacote ou item
            if "pacote" in cabecalho_unidade or "item" in cabecalho_unidade:
                set_cell_value(ws, row, cabecalhos, campo_unidade, unidade_padrao)
```

#### 2.2 Função `preencher_dados_fixos`
Remoção de comentários e lógica que preenchiam automaticamente unidades para dimensões de pacote e item.

### 3. Gerenciamento de Cache

#### 3.1 Nova Função `limpar_cache_ia()`
Criada função para limpar o cache manual da IA:
```python
def limpar_cache_ia():
    """Limpa o cache manual da IA para evitar problemas com preenchimento de campos."""
    global ia_cache
    ia_cache.clear()
    print("Cache da IA limpo com sucesso.")
```

#### 3.2 Limpeza Automática de Cache
Adicionada limpeza automática do cache no início das principais funções de processamento:
- `generate_spreadsheet_task`
- `organizador_ia_task`

#### 3.3 Endpoint Manual para Limpeza de Cache
Criado endpoint `/api/limpar-cache-ia/` (POST) para permitir limpeza manual do cache.

### 4. Campos Afetados

#### 4.1 Campos que NÃO serão mais preenchidos automaticamente:
- Unidade de altura
- Unidade de comprimento
- Unidade da largura
- Unidade de Peso do Pacote Principal
- Nível de hierarquia
- Tipo de relação
- Nome do tema
- Outros campos de unidade genéricos

#### 4.2 Campos que CONTINUAM sendo preenchidos:
- País de origem
- Peso do pacote
- Unidade de peso do pacote (apenas quando específico)
- Dimensões específicas de pacote/item (quando aplicável)

## Funções com Cache LRU Identificadas

As seguintes funções utilizam `@lru_cache(maxsize=None)` e podem ser afetadas por problemas de cache:
- `get_s3_client()`
- `get_model()`
- `get_embeddings_model()`
- `get_main_ia_chain()`
- `get_extrator_chain()`
- `get_tradutor_chain()`
- `get_vectorstore()`

## Recomendações de Uso

1. **Teste após implementação**: Verifique se os campos de unidade não estão sendo preenchidos automaticamente
2. **Limpeza de cache**: Use o endpoint `/api/limpar-cache-ia/` se suspeitar de problemas relacionados ao cache
3. **Monitoramento**: Observe se há inconsistências no preenchimento de campos após atualizações

## Arquivos Modificados

- `api/utils.py`: Prompts da IA, lógica de preenchimento, função de limpeza de cache
- `api/tasks.py`: Limpeza automática de cache nas tarefas principais
- `api/views.py`: Novo endpoint para limpeza manual de cache
- `api/urls.py`: Nova rota para o endpoint de limpeza de cache

## Data de Implementação

**Data**: 24 de dezembro de 2024
**Versão**: 1.0
**Status**: Implementado e testado