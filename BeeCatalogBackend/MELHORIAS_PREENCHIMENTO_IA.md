# Melhorias no Sistema de Preenchimento Automático - BeeCatalog

## Problemas Identificados

### 1. Qualidade do Conteúdo Gerado
- **Títulos genéricos**: Falta de especificidade técnica e características únicas
- **Descrições básicas**: Conteúdo superficial sem detalhes técnicos relevantes
- **Bullet points repetitivos**: Falta de variação e informações específicas
- **Palavras-chave genéricas**: Uso de termos muito amplos em vez de específicos

### 2. Campos Selecionados
- **Seleção automática limitada**: Sistema escolhe opções básicas sem análise contextual
- **Falta de inteligência contextual**: Não considera categoria específica do produto
- **Campos críticos vazios**: Campos importantes ficam como 'nan'

## Soluções Propostas

### 1. Melhorias no Prompt Principal

#### 1.1 Prompt Mais Específico por Categoria
```python
# Adicionar ao utils.py
CATEGORY_SPECIFIC_PROMPTS = {
    'eletronicos': {
        'titulo_focus': 'especificações técnicas, voltagem, potência, conectividade',
        'bullet_focus': 'compatibilidade, recursos técnicos, certificações, garantia',
        'keywords_base': ['eletrônico', 'tecnologia', 'digital', 'conectividade']
    },
    'casa_jardim': {
        'titulo_focus': 'material, dimensões, capacidade, uso específico',
        'bullet_focus': 'durabilidade, facilidade de uso, manutenção, versatilidade',
        'keywords_base': ['casa', 'decoração', 'organização', 'praticidade']
    },
    'moda': {
        'titulo_focus': 'material, tamanho, cor, estilo, ocasião de uso',
        'bullet_focus': 'conforto, estilo, versatilidade, cuidados',
        'keywords_base': ['moda', 'estilo', 'conforto', 'tendência']
    }
}
```

#### 1.2 Prompt Aprimorado para Títulos
```python
TITULO_ENHANCED_PROMPT = """
CRIE UM TÍTULO OTIMIZADO seguindo estas diretrizes:

1. **ESTRUTURA OBRIGATÓRIA**:
   - Nome do produto + Característica principal + Especificação técnica/dimensão
   - Entre 80-120 caracteres
   - SEM símbolos (–, /, emojis)

2. **PRIORIDADES POR CATEGORIA**:
   - Eletrônicos: Voltagem, potência, conectividade, compatibilidade
   - Casa/Jardim: Material, dimensões, capacidade, uso específico
   - Moda: Material, tamanho, cor, estilo
   - Esporte: Modalidade, nível, material, tamanho

3. **PALAVRAS PROIBIDAS**: garantido, perfeito, melhor, alta qualidade, cura

4. **EXEMPLO DE QUALIDADE**:
   ❌ Ruim: "Organizador de Mala Prático"
   ✅ Bom: "Organizador de Mala 6 Compartimentos Tecido Oxford Impermeável 35x25x12cm"
"""
```

#### 1.3 Prompt Aprimorado para Descrições
```python
DESCRICAO_ENHANCED_PROMPT = """
CRIE UMA DESCRIÇÃO DETALHADA seguindo esta estrutura:

**PARÁGRAFO INTRODUTÓRIO** (2-3 linhas)
- Nome do produto + benefício principal específico
- Contexto de uso ou problema que resolve

**SUBTÍTULO 1: [Característica Principal]**
- Detalhe técnico específico
- Como isso beneficia o usuário
- Exemplo prático de uso

**SUBTÍTULO 2: [Aplicação/Uso]**
- Para quem é indicado (público específico)
- Situações de uso detalhadas
- Compatibilidades ou requisitos

**SUBTÍTULO 3: [Praticidade/Manutenção]**
- Facilidade de uso/instalação
- Cuidados e manutenção
- Durabilidade e resistência

**ESPECIFICAÇÕES TÉCNICAS**
- Lista organizada com dados precisos
- Dimensões, peso, material, certificações
- Informações de compatibilidade

**FRASE DE IMPACTO FINAL**
- Reforce o benefício principal
- Incentive a decisão de compra
"""
```

### 2. Sistema de Análise Contextual

#### 2.1 Detector de Categoria Automático
```python
def detect_product_category(product_data):
    """
    Detecta a categoria do produto baseado em título, marca e características
    """
    titulo = product_data.get('titulo', '').lower()
    marca = product_data.get('nome_marca', '').lower()
    
    category_keywords = {
        'eletronicos': ['eletrônico', 'digital', 'usb', 'bluetooth', 'wifi', 'led', 'lcd'],
        'casa_jardim': ['organizador', 'decoração', 'cozinha', 'banheiro', 'jardim'],
        'moda': ['roupa', 'sapato', 'bolsa', 'acessório', 'tecido', 'algodão'],
        'esporte': ['fitness', 'exercício', 'treino', 'esporte', 'academia'],
        'beleza': ['cosmético', 'perfume', 'cuidado', 'beleza', 'pele']
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in titulo or keyword in marca for keyword in keywords):
            return category
    
    return 'geral'
```

#### 2.2 Gerador de Palavras-chave Inteligente
```python
def generate_smart_keywords(product_data, category):
    """
    Gera palavras-chave específicas baseadas na categoria e características do produto
    """
    base_keywords = CATEGORY_SPECIFIC_PROMPTS.get(category, {}).get('keywords_base', [])
    
    # Extrair palavras do título e características
    titulo_words = extract_relevant_words(product_data.get('titulo', ''))
    marca = product_data.get('nome_marca', '')
    
    # Combinar palavras-chave específicas
    specific_keywords = [
        f"{marca} {word}" for word in titulo_words if word
    ]
    
    # Adicionar variações e sinônimos
    enhanced_keywords = base_keywords + specific_keywords + titulo_words
    
    return '; '.join(enhanced_keywords[:15])  # Máximo 15 palavras-chave
```

### 3. Sistema de Validação de Qualidade

#### 3.1 Métricas de Qualidade
```python
def calculate_content_quality_score(generated_content):
    """
    Calcula score de qualidade do conteúdo gerado (0-100)
    """
    score = 0
    
    # Título (30 pontos)
    titulo = generated_content.get('titulo', '')
    if 80 <= len(titulo) <= 120:
        score += 15
    if any(char.isdigit() for char in titulo):  # Tem especificações numéricas
        score += 10
    if not any(word in titulo.lower() for word in ['perfeito', 'melhor', 'garantido']):
        score += 5
    
    # Descrição (40 pontos)
    descricao = generated_content.get('descricao_produto', '')
    if len(descricao) >= 600:
        score += 15
    if descricao.count('\n') >= 4:  # Tem estrutura com parágrafos
        score += 15
    if 'Especificações Técnicas' in descricao:
        score += 10
    
    # Bullet Points (20 pontos)
    bullets = generated_content.get('bullet_points', [])
    if len(bullets) == 5:
        score += 10
    if all(80 <= len(bp.get('bullet_point', '')) <= 120 for bp in bullets):
        score += 10
    
    # Palavras-chave (10 pontos)
    keywords = generated_content.get('palavras_chave', '')
    keyword_count = len([k for k in keywords.split(';') if k.strip()])
    if 10 <= keyword_count <= 15:
        score += 10
    
    return min(score, 100)
```

### 4. Melhorias na Seleção de Campos

#### 4.1 Sistema de Priorização Inteligente
```python
def intelligent_field_selection(product_data, field_options):
    """
    Seleciona campos baseado em análise contextual inteligente
    """
    category = detect_product_category(product_data)
    titulo = product_data.get('titulo', '').lower()
    
    # Regras específicas por categoria
    selection_rules = {
        'eletronicos': {
            'cor': lambda opts: select_by_keywords(opts, ['preto', 'branco', 'cinza']),
            'material': lambda opts: select_by_keywords(opts, ['plástico', 'metal', 'abs']),
            'voltagem': lambda opts: select_by_context(opts, titulo, ['110v', '220v', 'bivolt'])
        },
        'casa_jardim': {
            'material': lambda opts: select_by_keywords(opts, ['madeira', 'plástico', 'metal']),
            'cor': lambda opts: select_neutral_colors(opts),
            'tamanho': lambda opts: select_by_dimensions(opts, product_data)
        }
    }
    
    return apply_selection_rules(field_options, selection_rules.get(category, {}))
```

### 5. Configurações de Implementação

#### 5.1 Variáveis de Ambiente
```env
# Adicionar ao .env
AI_QUALITY_THRESHOLD=75  # Score mínimo para aceitar conteúdo
AI_MAX_RETRIES=3         # Tentativas máximas se qualidade baixa
AI_ENHANCED_MODE=true    # Ativar modo aprimorado
AI_CATEGORY_DETECTION=true  # Ativar detecção de categoria
```

#### 5.2 Configurações no Django
```python
# settings.py
AI_ENHANCEMENT_CONFIG = {
    'quality_threshold': int(os.getenv('AI_QUALITY_THRESHOLD', 75)),
    'max_retries': int(os.getenv('AI_MAX_RETRIES', 3)),
    'enhanced_mode': os.getenv('AI_ENHANCED_MODE', 'true').lower() == 'true',
    'category_detection': os.getenv('AI_CATEGORY_DETECTION', 'true').lower() == 'true'
}
```

## Implementação Gradual

### Fase 1: Melhorias Básicas (Semana 1)
1. Implementar prompts aprimorados
2. Adicionar sistema de detecção de categoria
3. Melhorar geração de palavras-chave

### Fase 2: Validação de Qualidade (Semana 2)
1. Implementar sistema de scoring
2. Adicionar retry automático para baixa qualidade
3. Criar logs de qualidade

### Fase 3: Seleção Inteligente (Semana 3)
1. Implementar seleção contextual de campos
2. Adicionar regras específicas por categoria
3. Otimizar performance

### Fase 4: Monitoramento (Semana 4)
1. Dashboard de qualidade
2. Métricas de performance
3. Ajustes baseados em feedback

## Resultados Esperados

- **+40% na qualidade dos títulos**: Mais específicos e otimizados
- **+60% na qualidade das descrições**: Conteúdo mais detalhado e estruturado
- **+50% na precisão dos campos**: Seleção mais inteligente e contextual
- **-30% na necessidade de edição manual**: Menos intervenção humana necessária
- **+25% na velocidade de processamento**: Menos regenerações por baixa qualidade

## Monitoramento e Métricas

### KPIs de Qualidade
1. **Score médio de qualidade**: Meta > 80
2. **Taxa de regeneração**: Meta < 15%
3. **Campos críticos preenchidos**: Meta > 90%
4. **Satisfação do usuário**: Meta > 85%

### Logs e Relatórios
- Log diário de qualidade por categoria
- Relatório semanal de performance
- Alertas para qualidade abaixo do threshold
- Dashboard em tempo real no admin