import io
import json
import mimetypes
import os
import random
import re
import time
import uuid
import sys
import chardet
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup

import pandas as pd
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.http import FileResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError

import boto3
from botocore.exceptions import ClientError
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries

from langchain.prompts import PromptTemplate
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser, CommaSeparatedListOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from pydantic.v1 import BaseModel, Field, constr, conlist

caminho_dotenv = os.path.join(settings.BASE_DIR, ".env")
load_dotenv(dotenv_path=caminho_dotenv)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'sa-east-1')

GEMINI_FLASH_INPUT_COST_PER_K_TOKENS = 0.00035
GEMINI_FLASH_OUTPUT_COST_PER_K_TOKENS = 0.00045

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME
)

THROTTLE_SECONDS = 0.2

DIRETORIO_UPLOAD = os.path.join(settings.BASE_DIR, "uploads")
NOME_TEMPLATE = "AMAZON_TEMPLATE.xlsm"

NOME_CSV_VALORES_VALIDOS = "valores_validos.csv"
NOME_CSV_J_PLANILHA = "J_planilha.csv"
NOME_CSV_J = "J.csv"
NOME_CSV_EXPLORAR_DADOS = "explorar_dados.csv"
NOME_CSV_DEFINICOES_DADOS = "definicoes_dados.csv"

FAISS_INDEX_DIR = os.path.join(settings.BASE_DIR, "faiss_index")
FAISS_INDEX_NAME = "amazon_base"

MAPA_CAMPOS = [
    ("sku", "SKU"),
    ("tipo_marca", "Nome da marca"), 
    ("nome_marca", "Nome da marca"),
    ("preco", "Preço padrão BRL"),
    ("quantidade", "Quantidade (BR)"),
    ("fba_dba", "Código do canal de processamento (BR)"),
    ("id_produto", "ID do produto"),
    ("ncm", "Código NCM"),
    ("peso_pacote", "Peso do pacote"),
    ("peso_produto", "Peso do item"), 
    ("ajuste", "Tipo de ajuste"),
]

MAPA_CLP = { "c_l_a_pacote": [
    "Comprimento do pacote",
    "Largura do pacote",
    "Altura do pacote"
]}

MAPA_CLPR = { "c_l_a_produto": [
    "Comprimento do item",
    "Largura do item",
    "Altura do item"
]}

# CORREÇÃO: Removido MAPA_UNIDADES para evitar preenchimento automático de unidades
# As unidades devem ser preenchidas apenas quando explicitamente necessário
# conforme solicitado pelo usuário
MAPA_UNIDADES = {
    # Mapa vazio - unidades não devem ser preenchidas automaticamente
}

campos_criticos = {
    "Baterias são necessárias?",
    "Quantidade de itens",
    "Cor",
    "Contagem de unidades",
    "Tipo de ID do produto",
    "Caminhos de Navegação Recomendados",
    "País de Origem",
    "Regulamentações de produtos perigosos"
}
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) '
        'Gecko/20100101 Firefox/112.0'
    )
}

def format_product_context(product: dict) -> str:
    """Formata os dados do produto em uma string legível para a IA."""
    context_parts = []
    readable_keys = {
        "titulo": "Título do Produto", "sku": "SKU", "tipo_marca": "Tipo de Marca",
        "nome_marca": "Nome da Marca", "preco": "Preço", "fba_dba": "Logística (FBA ou DBA)",
        "id_produto": "ID do Produto (EAN/GTIN/UPC)", "tipo_id_produto": "Tipo de ID do Produto",
        "ncm": "NCM", "quantidade": "Quantidade em Estoque", "peso_pacote": "Peso do Pacote (g)",
        "c_l_a_pacote": "Dimensões do Pacote C x L x A", "peso_produto": "Peso do Produto (g)",
        "c_l_a_produto": "Dimensões do Produto C x L x A", "ajuste": "Produto Ajustável?",
        "tema_variacao_pai": "Tema de Variação Principal"
    }
    for key, value in product.items():
        if value and key in readable_keys:
            context_parts.append(f"- {readable_keys[key]}: {value}")

    variations = product.get('variacoes', [])
    if variations:
        context_parts.append("\n- Variações do Produto:")
        for i, var in enumerate(variations):
            var_details = []
            readable_var_keys = {
                "sku": "SKU da Variação", "tipo": "Tipo de Variação", "cor": "Nome da Cor",
                "cla": "Dimensões (C x L x A)", "peso": "Peso (g)", "imagem": "URL da Imagem"
            }
            for v_key, v_value in var.items():
                if v_value and v_key in readable_var_keys:
                    var_details.append(f"  - {readable_var_keys[v_key]}: {v_value}")
            if var_details:
                context_parts.append(f"  Variação {i+1}:\n" + "\n".join(var_details))
    
    return "\n".join(context_parts)

def scrape_mercadolivre_images(url: str) -> list[str]:
    if "mercadolivre.com.br" not in url and "mercadolivre.com" not in url:
        raise ValueError("A URL fornecida não parece ser do Mercado Livre.")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Erro ao acessar a URL: {e}")
    soup = BeautifulSoup(resp.text, 'html.parser')
    gallery = soup.find('div', class_='ui-pdp-gallery')
    images: list[str] = []
    if gallery:
        for img in gallery.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if not src: continue
            high_res_src = re.sub(r'-\w\.(jpg|jpeg|webp)$', '-O.webp', src)
            src_lower = high_res_src.lower()
            if src_lower.endswith('.gif') or src_lower.startswith('data:'): continue
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    if int(width) < 100 or int(height) < 100: continue
                except ValueError: pass
            if high_res_src not in images: images.append(high_res_src)
    if not images: raise ValueError("Nenhuma imagem encontrada na galeria do produto.")
    return images

class OpcaoCampo(NamedTuple):
    field_name: str
    options: List[str]
    col_indices: List[int]

class PlanilhaChunk:
    def __init__(self, nome, col_start, col_end):
        self.nome = nome
        self.col_start = col_start
        self.col_end = col_end
        self.campos = [] 
    def adicionar_campo(self, campo_info: dict): self.campos.append(campo_info)
    def to_dict(self): return {"nome": self.nome, "col_start": self.col_start, "col_end": self.col_end, "campos": self.campos}
    def __repr__(self): return f"<PlanilhaChunk: {self.nome} (Colunas {self.col_start}-{self.col_end}), {len(self.campos)} campos>"

EXPL_RANGE = re.compile(r"^(?:'(?P<sheet_quoted>[^']+?)'|(?P<sheet_unquoted>[^'!]+?))!(?P<start>\$?[A-Z]{1,3}\$?\d+)(?::(?P<end>\$?[A-Z]{1,3}\$?\d+))?$")
RE_DIRECT = re.compile(r"^=?\s*([A-Za-z0-9_.\-]+)\s*$")
RE_INDIRECT_SUFFIX = re.compile(r'&\s*"([A-Za-z0-9_\.]+)"')

@lru_cache(maxsize=None)
def get_s3_client():
    return boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_S3_REGION_NAME)

@lru_cache(maxsize=None)
def get_model(temperature=0.2):
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY não está configurada. Configure a chave da API do Google Gemini no arquivo .env")
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=temperature, google_api_key=GOOGLE_API_KEY)

@lru_cache(maxsize=None)
def get_embeddings_model():
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY não está configurada. Configure a chave da API do Google Gemini no arquivo .env")
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", 
        google_api_key=GOOGLE_API_KEY,
        # Forçar modo síncrono
        transport="rest"
    )

def test_google_api_connection():
    """Testa se a conexão com a API do Google está funcionando."""
    try:
        model = get_model(temperature=0)
        response = model.invoke("Teste de conexão. Responda apenas 'OK'.")
        return True, "Conexão com Google API funcionando"
    except Exception as e:
        return False, f"Erro na conexão com Google API: {str(e)}"

class BulletPoint(BaseModel):
    bullet_point: str = Field(description="Um único bullet point, com 80 a 120 caracteres. Formato: 'TERMO EM CAIXA ALTA: Frase objetiva.'")

class AmazonListing(BaseModel):
    titulo: constr(min_length=80, max_length=120) = Field(description="Título do produto com 80 a 120 caracteres, sem símbolos como travessão ou barra.")
    bullet_points: conlist(BulletPoint, min_items=5, max_items=5) = Field(description="Uma lista com exatamente 5 bullet points.")
    descricao_produto: str = Field(description="Descrição detalhada do produto, seguindo a estrutura com subtítulos e especificações técnicas.")
    palavras_chave: str = Field(description="String única contendo 10 a 15 palavras-chave relevantes, separadas por ponto e vírgula.")

@lru_cache(maxsize=None)
def get_main_ia_chain():
    output_parser = JsonOutputParser(pydantic_object=AmazonListing)
    prompt_template = PromptTemplate(
        input_variables=["product_context"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
        template="""
        Crie um listing de produto para a Amazon com base nas informações fornecidas, seguindo exatamente o modelo abaixo.
        Atenção: Todo o conteúdo deve respeitar as diretrizes da Amazon Seller Central, evitando: termos proibidos como "garantido", "perfeito", "melhor", "alta qualidade", "cura" ou qualquer promessa; uso de símbolos como travessão (–), barra (/) ou emojis; declarações absolutas ou subjetivas.

        ESTRUTURA DO LISTING

        TÍTULO
        Deve conter entre 80 a 120 caracteres.
        Não usar símbolos como travessão ou barra.
        Incluir nome do produto e principais características técnicas ou dimensões.

        BULLET POINTS
        Inserir 5 bullets, cada um com entre 80 a 120 caracteres.
        Formato: primeiro termo em caixa alta seguido de dois pontos, depois a frase objetiva.
        Exemplo: CONFORTO: superfície adaptável que ajuda a reduzir pontos de pressão.

        DESCRIÇÃO DO PRODUTO
        Comece com o nome do produto e um breve reforço do benefício principal.
        Desenvolva 3 a 4 parágrafos curtos, cada um com um subtítulo, seguindo o padrão:
        Subtítulo 1 (exemplo: Ajuste Personalizado ao Corpo)
        Explique de forma clara como o produto entrega esse benefício.
        Subtítulo 2 (exemplo: Indicação de Uso)
        Descreva para quem o produto é indicado e situações de uso.
        Subtítulo 3 (exemplo: Prático de Higienizar)
        Explique sobre limpeza, manutenção e conservação.
        Especificações Técnicas
        Tipo: [tipo do produto]
        Dimensões: [medidas em metros]
        Peso máximo suportado: [exemplo: 130 kg]
        Certificação (se houver): [exemplo: ANVISA nº...]
        Outras informações técnicas relevantes em lista.
        Finalize com uma frase de impacto que incentive a compra, reforçando o benefício principal.
        Exemplo: Ideal para quem busca mais conforto e segurança no dia a dia.

        PALAVRAS-CHAVE
        OBRIGATÓRIO: Inclua EXATAMENTE entre 10 a 15 palavras-chave relevantes, separadas por ponto e vírgula (;).
        As palavras-chave devem ser específicas do produto e categoria.
        Exemplo para organizador de mala: "Organizador de mala; Acessórios para viagem; Organizador de bagagem; Mala de viagem; Acessórios de viagem; Organizador portátil; Bagagem organizada; Viagem organizada; Acessórios práticos; Organizador funcional; Mala organizada; Viagem prática; Bagagem funcional; Organizador durável; Acessórios úteis"
        NUNCA use vírgulas (,) como separador - use APENAS ponto e vírgula (;).

        {format_instructions}

        **Informações Completas do Produto para Análise:**
        ```
        {product_context}
        ```
        """
    )
    return prompt_template | get_model(temperature=0.2) | output_parser

@lru_cache(maxsize=None)
def get_extrator_chain():
    prompt_extrator = PromptTemplate.from_template("... (seu template de extrator aqui) ...")
    return prompt_extrator | get_model(temperature=0) | CommaSeparatedListOutputParser()

@lru_cache(maxsize=None)
def get_tradutor_chain():
    prompt_tradutor = PromptTemplate.from_template("... (seu template de tradutor aqui) ...")
    return prompt_tradutor | get_model(temperature=0) | StrOutputParser()

def preencher_grupo_de_colunas(ws, row: int, col_indices: list, valores: list, field_name_debug: str):
    try:
        if not valores: return
        valores_unicos = list(dict.fromkeys(valores))
        colunas_ordenadas = sorted(col_indices)
        pares_coluna_valor = list(zip(colunas_ordenadas, valores_unicos))
        for col_idx, valor_item in pares_coluna_valor:
            cell = ws.cell(row=row, column=col_idx)
            if not cell.value and valor_item and str(valor_item).lower() != 'nan':
                cell.value = valor_item
    except Exception as e:
        try: print(f"ERRO CRÍTICO DENTRO DE 'preencher_grupo_de_colunas' para o campo '{field_name_debug}': {e}")
        except Exception: print(f"ERRO CRÍTICO DENTRO DE 'preencher_grupo_de_colunas'. Falha ao imprimir detalhes do erro: {e}")

ia_cache = {}
def obter_com_cache(key, func, *args, **kwargs):
    if key in ia_cache: return ia_cache[key]
    resultado = func(*args, **kwargs)
    ia_cache[key] = resultado
    return resultado

def limpar_cache_ia():
    """Limpa o cache manual da IA para evitar problemas com preenchimento de campos."""
    global ia_cache
    ia_cache.clear()
    print("Cache da IA limpo com sucesso.")

def detectar_codificacao(path: str) -> str:
    with open(path, "rb") as f: bruto = f.read(10_000)
    return chardet.detect(bruto)["encoding"] or "utf-8"

def carregar_docs_csv(path: str, delimiter: str = ","):
    if not os.path.exists(path): return []
    loader = CSVLoader(file_path=path, csv_args={"delimiter": delimiter, "quotechar": '"'}, encoding=detectar_codificacao(path))
    return loader.load()

def carregar_explorar_dados_csv(path: str) -> List[Document]:
    if not os.path.exists(path): return []
    try: encoding = detectar_codificacao(path); df = pd.read_csv(path, encoding=encoding)
    except Exception as e: return []
    documents = []
    for index, row in df.iterrows():
        node_number = row.get("Número do Node"); browse_path = row.get("Caminho de Navegação"); positive_keywords = row.get("Palavras-Chave Positivas"); negative_keywords = row.get("Palavras-Chave Negativas")
        if pd.notna(node_number) and pd.notna(browse_path):
            content_parts = [f"Caminho de Navegação: {browse_path}."]
            if pd.notna(positive_keywords): content_parts.append(f"Tópicos e funções relevantes para este caminho: {positive_keywords}.")
            if pd.notna(negative_keywords): content_parts.append(f"Tópicos e funções a evitar para este caminho: {negative_keywords}.")
            enriched_page_content = " ".join(content_parts); full_path_with_id = f"{browse_path} ({node_number})"
            doc = Document(page_content=enriched_page_content, metadata={"tipo_dado": "caminho_navegacao", "Número do Node": str(node_number).strip(), "Caminho de Navegação": str(browse_path).strip(), "valor_opcao": full_path_with_id, "positive_keywords": str(positive_keywords).strip() if pd.notna(positive_keywords) else "", "negative_keywords": str(negative_keywords).strip() if pd.notna(negative_keywords) else ""})
            documents.append(doc)
    return documents

def carregar_tipos_de_produto(path: str) -> List[Document]:
    if not os.path.exists(path): return []
    try: encoding = detectar_codificacao(path); df = pd.read_csv(path, encoding=encoding)
    except Exception as e: return []
    df_tipos_produto = df[df['campo'] == 'Tipo de produto -'].copy(); documentos = []
    for index, row in df_tipos_produto.iterrows():
        tipo_produto_valor = row.get("valor_opcao")
        if pd.notna(tipo_produto_valor):
            termo_em_pt = tipo_produto_valor.replace('_', ' ').lower()
            conteudo_descritivo = f"Tipo de Produto da Amazon: {tipo_produto_valor}. Categoria de produto para o item {termo_em_pt}."
            doc = Document(page_content=conteudo_descritivo, metadata={"tipo_dado": "tipo_de_produto", "valor_opcao": tipo_produto_valor})
            documentos.append(doc)
    return documentos

@lru_cache(maxsize=None)
def get_vectorstore():
    embeddings = get_embeddings_model()
    faiss_index_path = os.path.join(settings.BASE_DIR, "faiss_index")
    if os.path.exists(os.path.join(faiss_index_path, "index.faiss")):
        return FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
    j_csv_path = os.path.join(settings.BASE_DIR, "memo", NOME_CSV_J); j_planilha_csv_path = os.path.join(settings.BASE_DIR, "memo", NOME_CSV_J_PLANILHA); valores_validos_csv_path = os.path.join(settings.BASE_DIR, "memo", NOME_CSV_VALORES_VALIDOS) ; explorar_dados_csv_path = os.path.join(settings.BASE_DIR, "memo", NOME_CSV_EXPLORAR_DADOS); definicoes_dados_csv_path = os.path.join(settings.BASE_DIR, "memo", NOME_CSV_DEFINICOES_DADOS)
    all_docs = (carregar_docs_csv(j_csv_path) + carregar_docs_csv(j_planilha_csv_path) + carregar_docs_csv(valores_validos_csv_path) + carregar_explorar_dados_csv(explorar_dados_csv_path) + carregar_docs_csv(definicoes_dados_csv_path))
    if not all_docs: return None
    vectorstore = FAISS.from_documents(all_docs, embeddings)
    if not os.path.exists(faiss_index_path): os.makedirs(faiss_index_path)
    vectorstore.save_local(faiss_index_path, index_name="index")
    return vectorstore

def escolher_com_ia(product_data: dict, fields_to_fill: List[Dict], assumed_items: FrozenSet[Tuple[str, str]], retriever) -> Tuple[Dict[str, str], int]:
    if not fields_to_fill:
        return {}, 0
    
    titulo_produto = product_data.get("titulo", "produto")
    product_context_str = format_product_context(product_data)
    
    assumed_values = dict(assumed_items)
    context_query = f"Forneça informações e especificações para o produto '{titulo_produto}' para ajudar no preenchimento de seus atributos."
    
    # Implementar retry para resolver problemas de conexão
    max_retries = 3
    retry_delay = 2
    relevant_docs = []
    
    for attempt in range(max_retries):
        try:
            relevant_docs = retriever.invoke(context_query)
            break
        except Exception as e:
            print(f"Tentativa {attempt + 1} falhou ao buscar documentos relevantes: {e}")
            if attempt < max_retries - 1:
                print(f"Tentando novamente em {retry_delay} segundos...")
                import time
                time.sleep(retry_delay)
                retry_delay *= 2  # Backoff exponencial
            else:
                print("Todas as tentativas falharam. Continuando sem documentos relevantes.")
                relevant_docs = []
    
    retriever_context_str = "\n".join([f"- {doc.page_content}" for doc in relevant_docs]) or "Nenhuma informação adicional encontrada na base de conhecimento."
    
    full_context = f"DADOS DO PRODUTO:\n{product_context_str}\n\nINFORMAÇÕES ADICIONAIS DA BASE DE CONHECIMENTO:\n{retriever_context_str}"
    
    fields_json_str = json.dumps(fields_to_fill, indent=2, ensure_ascii=False)
    
    multi_value_field_names = [f['field_name'] for f in fields_to_fill if f.get('multi_value', False)]
    multi_value_context = (f"Para os seguintes campos, se aplicável, retorne uma LISTA JSON de strings com os valores relevantes: {', '.join(multi_value_field_names)}\n" if multi_value_field_names else "")
    
    critical_field_names = [f['field_name'] for f in fields_to_fill if f.get('is_critical', False)]
    critical_context = ""
    if critical_field_names:
        critical_context = (
            "ATENÇÃO MÁXIMA: Os seguintes campos são CRÍTICOS e devem ter um valor válido e preciso: "
            f"**{', '.join(critical_field_names)}**. "
            "É OBRIGATÓRIO que você escolha a melhor opção da lista para estes campos. NÃO use 'nan' para eles, a menos que seja absolutamente impossível determinar um valor.\n"
        )
    
    prompt = PromptTemplate(
        input_variables=["product", "context", "assumed_values", "fields_json", "multi_value_context", "critical_context"],
        template=(
            "Você é um especialista em catalogação de produtos para e-commerce, seguindo as diretrizes da Amazon.\n"
            "Sua tarefa é preencher vários campos para um produto com base nas opções disponíveis para cada um.\n"
            "Analise o título do produto, o CONTEXTO COMPLETO e os valores de referência para tomar a decisão mais precisa para CADA campo.\n\n"
            "REGRAS IMPORTANTES:\n"
            "- {critical_context}"
            "- Para a maioria dos campos, retorne uma única string como valor.\n"
            "- {multi_value_context}"
            "- CAMPOS DE UNIDADE: NUNCA preencha automaticamente os seguintes campos de unidade específicos: 'Unidade de altura', 'Unidade de comprimento', 'Unidade da largura', 'Unidade de Altura do Pacote Principal', 'Unidade de Comprimento do Pacote Principal', 'Unidade de Largura do Pacote Principal', 'Unidade de Peso do Pacote Principal', 'Unidade da profundidade do artigo', 'Unidade de altura do artigo', 'Unidade de largura do artigo'. Para estes campos, sempre use 'nan'. Para outros campos de unidade (como 'Unidade de comprimento do item', 'Unidade de largura do item', 'Unidade de altura do item'), preencha apenas se explicitamente fornecido no contexto.\n"
            "- Se nenhuma opção for adequada ou se a informação for desconhecida, use a string 'nan'.\n\n"
            "--- DADOS DO PRODUTO E CONTEXTO ---\nProduto de Referência: '{product}'\n\nContexto Completo:\n{context}\n\n"
            "--- VALORES DE REFERÊNCIA ---\n{assumed_values}\n\n"
            "--- CAMPOS PARA PREENCHER ---\n{fields_json}\n\n"
            "--- INSTRUÇÃO DE SAÍDA ---\n"
            "Responda APENAS com um único objeto JSON válido, mapeando cada 'field_name' para a sua escolha.\n"
            "Exemplo de formato de saída: {{\"Material\": [\"Plástico\", \"Metal\"], \"Cor\": \"Azul\", \"Regulamentações...\": \"Não aplicável\"}}\n"
            "Não inclua NENHUM texto, explicação ou formatação de código antes ou depois do objeto JSON."
        )
    ).format(
        product=titulo_produto,
        context=full_context,
        assumed_values=json.dumps(assumed_values, indent=2, ensure_ascii=False),
        fields_json=fields_json_str,
        multi_value_context=multi_value_context,
        critical_context=critical_context
    )
    response = get_model(temperature=0.2).invoke(prompt)
    response_content = response.content.strip()
    total_tokens = response.response_metadata.get('usage', {}).get('total_tokens', 0)
    
    try:
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            ai_choices = json.loads(json_match.group(0))
            return ai_choices, total_tokens
        return {}, total_tokens
    except json.JSONDecodeError:
        return {}, total_tokens

def processar_chunk_com_ia(chunk_name: str, chunk_data: dict, product_data: dict, retriever_context_info: str, campos_criticos: set, persona_especialista: str):
    print(f"\nINFO: Processando o Chunk '{chunk_name}'...")
    
    titulo_produto = product_data.get("titulo", "produto")
    product_context_str = format_product_context(product_data)
    full_context = f"DADOS COMPLETOS DO PRODUTO:\n{product_context_str}\n\nINFORMAÇÕES ADICIONAIS DA BASE DE CONHECIMENTO:\n{retriever_context_info}"

    chunk = PlanilhaChunk(chunk_data['nome'], chunk_data['col_start'], chunk_data['col_end'])
    chunk.campos = chunk_data['campos']

    campos_vazios = chunk.campos
    if not campos_vazios:
        print(f"INFO: Nenhum campo a ser preenchido no chunk '{chunk_name}'. Pulando.")
        return {}

    nomes_l4_dos_campos_vazios = list(dict.fromkeys([campo['cabecalho_l4'] for campo in campos_vazios if campo['cabecalho_l4']]))
    if not nomes_l4_dos_campos_vazios:
        print(f"INFO: Nenhum campo com cabeçalho na linha 4 para ser avaliado no chunk '{chunk_name}'.")
        return {}

    print(f"  -> Estágio 1: Verificando a relevância de {len(nomes_l4_dos_campos_vazios)} grupos de campos para o produto...")
    prompt_triagem = (
        f"Com base nas informações completas do produto: \n\n{product_context_str}\n\n"
        f"Avalie a lista de grupos de atributos a seguir: {', '.join(nomes_l4_dos_campos_vazios)}. "
        f"Responda APENAS com um objeto JSON contendo uma única chave 'campos_relevantes', "
        f"cujo valor é uma lista de strings com os nomes dos atributos da lista que são REALMENTE RELEVANTES. "
        f"Exemplo: para uma VELA, o atributo 'Voltagem' é irrelevante e não deve ser incluído na resposta."
    )
    nomes_l4_relevantes = []
    try:
        modelo_triagem = get_model(temperature=0.2)
        resposta_triagem_raw = modelo_triagem.invoke(prompt_triagem).content.strip()
        json_match_triagem = re.search(r'\{.*\}', resposta_triagem_raw, re.DOTALL)
        nomes_l4_relevantes = json.loads(json_match_triagem.group(0))['campos_relevantes']
        print(f"  -> Triagem concluída. Grupos de campos relevantes identificados: {nomes_l4_relevantes}")
    except (AttributeError, json.JSONDecodeError, KeyError) as e:
        print(f"  -> AVISO: Não foi possível determinar os campos relevantes na triagem ({e}). O preenchimento seguirá sem o filtro de relevância.")
        nomes_l4_relevantes = nomes_l4_dos_campos_vazios

    print(f"  -> Aplicando 'Passe VIP' para campos críticos...")
    for campo_critico in campos_criticos:
        if campo_critico not in nomes_l4_relevantes:
            if any(campo['cabecalho_l4'] == campo_critico for campo in campos_vazios):
                print(f"    -> PASSE VIP: Campo crítico '{campo_critico}' não foi escolhido pela IA. Adicionando manualmente à lista.")
                nomes_l4_relevantes.append(campo_critico)

    campos_para_preencher = [campo for campo in campos_vazios if campo['cabecalho_l4'] in nomes_l4_relevantes]
    if not campos_para_preencher:
        print(f"INFO: Nenhum campo relevante encontrado para preencher no chunk '{chunk_name}' após a triagem.")
        return {}

    print(f"  -> Estágio 2: Pedindo à IA especialista para preencher os {len(campos_para_preencher)} campos relevantes...")
    nomes_campos_criticos = [campo['cabecalho_l5'] for campo in campos_para_preencher if campo['cabecalho_l4'] in campos_criticos]
    contexto_critico = ""
    if nomes_campos_criticos:
        contexto_critico = (f"ATENÇÃO MÁXIMA: Os seguintes campos deste grupo são CRÍTICOS e devem ter um valor válido: "
                            f"**{', '.join(nomes_campos_criticos)}**. Evite 'nan' para eles a todo custo.\n")

    campos_str_detalhado = "\n".join([f"- **{campo['cabecalho_l5']}** (do grupo '{campo['cabecalho_l4']}')" for campo in campos_para_preencher])

    prompt_final = (
        "{persona}\n\n"
        "Sua missão é preencher DE FORMA PRECISA E COMPLETA **CADA CAMPO** da lista fornecida...\n\n"
        "### REGRAS DE OURO:\n"
        "1.  **NÃO INVENTE INFORMAÇÕES:** Use apenas dados fornecidos no contexto do produto. Se não houver informação suficiente, use 'nan'.\n"
        "2.  **PENSE PASSO A PASSO:** Analise cada campo individualmente com base no contexto fornecido.\n"
        "3.  **SAÍDA EXCLUSIVAMENTE EM JSON:** Responda apenas com um objeto JSON válido, sem texto adicional.\n"
        "4.  **CHAVES EXATAS:** Use exatamente os nomes dos campos fornecidos como chaves no JSON.\n"
        "5.  **VALORES EM PORTUGUÊS BRASILEIRO.**\n"
        "6.  **CAMPOS DE UNIDADE:** NUNCA preencha automaticamente os seguintes campos de unidade específicos: 'Unidade de altura', 'Unidade de comprimento', 'Unidade da largura', 'Unidade de Altura do Pacote Principal', 'Unidade de Comprimento do Pacote Principal', 'Unidade de Largura do Pacote Principal', 'Unidade de Peso do Pacote Principal', 'Unidade da profundidade do artigo', 'Unidade de altura do artigo', 'Unidade de largura do artigo'. Para estes campos, sempre use 'nan'. Para outros campos de unidade (como 'Unidade de comprimento do item', 'Unidade de largura do item', 'Unidade de altura do item'), preencha apenas se explicitamente fornecido no contexto.\n"
        "7.  **CAMPOS CRÍTICOS:** {contexto_critico}\n\n"
        "### DADOS PARA ANÁLISE\n"
        "**Produto de Referência:**\n`{titulo_produto}`\n\n"
        "**Contexto Completo:**\n{context_info}\n\n"
        "### CAMPOS PARA PREENCHER (APENAS DESTE GRUPO RELEVANTE)\n"
        "{campos_str_detalhado}\n"
        "### INSTRUÇÃO DE SAÍDA FINAL\n"
        "Gere o objeto JSON com uma entrada para CADA um dos campos listados acima. Não omita nenhum."
    ).format(
        persona=persona_especialista,
        contexto_critico=contexto_critico or "Nenhum campo crítico neste grupo.",
        titulo_produto=titulo_produto,
        context_info=full_context,
        campos_str_detalhado=campos_str_detalhado
    )
    
    try:
        resposta_ia = get_model(temperature=0.2).invoke(prompt_final)
        response_content = resposta_ia.content.strip()
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if not json_match:
            print(f"AVISO: Nenhum JSON encontrado na resposta para o chunk '{chunk_name}'.")
            return {}

        ai_choices = json.loads(json_match.group(0))
        return ai_choices

    except json.JSONDecodeError:
        print(f"ERRO: Falha ao decodificar o JSON para o chunk '{chunk_name}'. Resposta: {response_content}")
        return {}
    except Exception as e:
        print(f"ERRO inesperado ao processar o chunk '{chunk_name}': {e}")
        return {}

def filtrar_documentos_dinamicamente(documentos_brutos: list, titulo_produto: str) -> list:
    documentos_filtrados = []
    for doc in documentos_brutos:
        palavras_negativas_str = doc.metadata.get('negative_keywords', '')
        if not palavras_negativas_str: documentos_filtrados.append(doc); continue
        lista_palavras_negativas = [kw.strip() for kw in palavras_negativas_str.split(',')]
        houve_conflito = False
        for palavra in lista_palavras_negativas:
            if palavra and palavra in titulo_produto: houve_conflito = True; break
        if not houve_conflito: documentos_filtrados.append(doc)
    return documentos_filtrados

def filtrar_por_relevancia_lexical(documentos: list, must_have_keywords: list) -> list:
    if not must_have_keywords: return documentos
    documentos_filtrados = []
    for doc in documentos:
        conteudo_doc_lower = doc.page_content.lower()
        if any(keyword.strip() in conteudo_doc_lower for keyword in must_have_keywords):
            documentos_filtrados.append(doc)
    return documentos_filtrados

def parse_form_data(post_data, files_data):
    output = {}; key_regex = re.compile(r'\[([^\]]*)\]')
    for key, value in post_data.items():
        parts = key_regex.findall(key)
        if not parts: continue
        main_key = key.split('[')[0]
        current_level = output.setdefault(main_key, {}).setdefault(parts[0], {})
        inner_key = parts[1]
        current_level[inner_key] = value
    for key, uploaded_file in files_data.items():
        parts = key_regex.findall(key)
        if not parts: continue
        main_key, index, field, sub_field = key.split('[')[0], parts[0], parts[1], parts[2].replace(']', '')
        output.setdefault(main_key, {}).setdefault(index, {}).setdefault(field, {})[sub_field] = uploaded_file.name
    return output

def mapear_chunks_da_planilha(ws) -> dict[str, PlanilhaChunk]:
    chunks = {}
    for merged_cell_range in ws.merged_cells.ranges:
        min_col, min_row, max_col, max_row = merged_cell_range.bounds
        if min_row == 3:
            chunk_name = ws.cell(row=min_row, column=min_col).value
            if not chunk_name: continue
            chunk_obj = PlanilhaChunk(nome=chunk_name, col_start=min_col, col_end=max_col)
            for col in range(min_col, max_col + 1):
                header_l4 = str(ws.cell(row=4, column=col).value or '').strip()
                header_l5 = str(ws.cell(row=5, column=col).value or '').strip()
                if header_l4 or header_l5: chunk_obj.adicionar_campo({'col': col, 'cabecalho_l4': header_l4, 'cabecalho_l5': header_l5})
            chunks[chunk_name] = chunk_obj
    return chunks

def _ler_range(ws, coord):
    bounds = coord if ':' in coord else f"{coord}:{coord}"; min_col, min_row, max_col, max_row = range_boundaries(bounds); valores = []
    for r in range(min_row, max_row + 1):
        for c in range(min_col, max_col + 1):
            valor = ws.cell(row=r, column=c).value
            if valor is not None: valores.append(str(valor))
    return valores

def construir_mapas_nomeados(wb):
    full_map = {}; suffix_map = {}
    for name, defn in wb.defined_names.items():
        if not defn.destinations: continue
        for sheet_title, coord in defn.destinations:
            try:
                ws = wb[sheet_title]; full_map[name] = (ws, coord); suffix = name.split('_', 1)[-1]; suffix_map.setdefault(suffix, []).append(name)
            except KeyError: print(f"AVISO: Planilha '{sheet_title}' não encontrada para o range nomeado '{name}'.")
    return full_map, suffix_map

def extrair_opcoes(wb, ws, bruto_formula, nr_full_map, nr_suffix_map, row):
    f_bruto = bruto_formula or ''
    if f_bruto.strip().upper().startswith('IF(') and 'INDIRECT' in f_bruto.upper():
        inner_indirects = re.findall(r'INDIRECT\((.*?)\)', f_bruto, flags=re.IGNORECASE)
        for inner in inner_indirects:
            # *** INÍCIO DA CORREÇÃO: Garante que 'opts' sempre tenha um valor ***
            opts = extrair_opcoes(wb, ws, f"INDIRECT({inner})", nr_full_map, nr_suffix_map, row)
            if opts: return opts
            # *** FIM DA CORREÇÃO ***
    
    # *** INÍCIO DA CORREÇÃO: Inicializa 'opts' antes do loop ***
    opts = []
    literal_names = re.findall(r'"([A-Za-z0-9_\.\[\]\=\#\-]+)"', f_bruto)
    for name in literal_names:
        if name in nr_full_map: 
            ws_nr, coord = nr_full_map[name]
            opts = _ler_range(ws_nr, coord)
            if opts: return opts
    # *** FIM DA CORREÇÃO ***

    f = f_bruto.lstrip('=').strip(); m = RE_DIRECT.match(f)
    if m:
        name = m.group(1)
        if name in nr_full_map: 
            ws_nr, coord = nr_full_map[name]
            opts = _ler_range(ws_nr, coord)
            if opts: return opts
    if f.upper().startswith('INDIRECT'):
        prefix = str(ws.cell(row=row, column=3).value or '').replace('-', '_').replace(' ', '_'); cleaned = re.sub(r'VLOOKUP\([^)]*\)', '', f_bruto); match = RE_INDIRECT_SUFFIX.search(cleaned)
        if match:
            suffix = match.group(1); cand = prefix + suffix
            if cand in nr_full_map: 
                ws1, coord1 = nr_full_map[cand]
                opts = _ler_range(ws1, coord1)
                if opts: return opts
            for nm in nr_full_map:
                if suffix in nm: 
                    ws2, coord2 = nr_full_map[nm]
                    opts = _ler_range(ws2, coord2)
                    if opts: return opts
    if f.startswith('"') and f.endswith('"'): return [valor.strip() for valor in re.split(r'[;,]', f.strip('"')) if valor.strip()]
    if f.startswith('{') and f.endswith('}'): return [valor.strip() for valor in re.split(r'[;,]', f.strip('{}')) if valor.strip()]
    m2 = EXPL_RANGE.match(f)
    if m2:
        sheet = (m2.group('sheet_quoted') or m2.group('sheet_unquoted') or ws.title).strip(); coord = m2.group('start') + (':' + m2.group('end') if m2.group('end') else '')
        try: 
            tgt = wb[sheet]
            opts = _ler_range(tgt, coord)
            if opts: return opts
        except KeyError: print(f"AVISO: Planilha referenciada '{sheet}' não encontrada: {f_bruto}")
    if f in nr_full_map: 
        ws_fb, coord_fb = nr_full_map[f]
        opts = _ler_range(ws_fb, coord_fb)
        if opts: return opts
    return []

def coletar_opcoes_campo(wb, sheet_name: str, data_row: int) -> dict:
    ws = wb[sheet_name]; nr_full_map, nr_suffix_map = construir_mapas_nomeados(wb); field_groups = {}
    for dv in ws.data_validations.dataValidation:
        if dv and (dv.type or '').lower() != 'list': continue
        opts = extrair_opcoes(wb, ws, dv.formula1 or "", nr_full_map, nr_suffix_map, data_row)
        if not opts: opts = ["nan"]
        cols = []
        for cr in dv.ranges:
            min_c, min_r, max_c, max_r = cr.bounds
            if min_r <= data_row <= max_r: cols.extend(range(min_c, max_c + 1))
        if not cols: continue
        cabecalho = str(ws.cell(row=4, column=cols[0]).value or "").strip()
        if not cabecalho: continue
        if cabecalho not in field_groups: field_groups[cabecalho] = {'field_name': cabecalho, 'options': opts, 'col_indices': cols}
        else: field_groups[cabecalho]['col_indices'].extend(cols)
    return field_groups

def extract_template_fields(template_path: str):
    if not os.path.exists(template_path): raise FileNotFoundError(f"O arquivo de template não foi encontrado em: {template_path}")
    workbook = load_workbook(filename=template_path, read_only=True, keep_vba=True)
    try: sheet = workbook["Modelo"]
    except KeyError: raise ValueError("A aba 'Modelo' não foi encontrada no arquivo.")
    headers_map = {}; max_col = sheet.max_column
    for col_idx in range(1, max_col + 1):
        header_l4 = str(sheet.cell(row=4, column=col_idx).value or '').strip()
        header_l5 = str(sheet.cell(row=5, column=col_idx).value or '').strip()
        if not header_l4: continue
        if header_l4 not in headers_map: headers_map[header_l4] = {'tech_names': []}
        headers_map[header_l4]['tech_names'].append({'name': header_l5, 'col': col_idx})
    template_structure = {}
    for header, data in headers_map.items():
        if len(data['tech_names']) > 1: template_structure[header] = { item['name']: "" for item in data['tech_names'] if item['name'] }
        else:
            if data['tech_names']: template_structure[header] = ""
            else: template_structure[header] = ""
    return template_structure, headers_map

def parse_ai_response_to_dict(text_response: str) -> dict:
    response_dict = {}; lines = text_response.strip().split('\n')
    for line in lines:
        if '::' not in line: continue
        key, value = line.split('::', 1); key = key.strip(); value = value.strip()
        if '>' in key:
            parent_key, child_key = key.split('>', 1); parent_key = parent_key.strip(); child_key = child_key.strip()
            if parent_key not in response_dict: response_dict[parent_key] = {}
            response_dict[parent_key][child_key] = value
        else: response_dict[key] = value
    return response_dict

def write_to_sheet(sheet, row_num, ai_response_dict, headers_map):
    for header, value in ai_response_dict.items():
        if header not in headers_map: continue
        if isinstance(value, dict):
            for tech_name, sub_value in value.items():
                for item in headers_map[header]['tech_names']:
                    if item['name'] == tech_name: sheet.cell(row=row_num, column=item['col'], value=sub_value); break
        else:
            if headers_map[header]['tech_names']: col_idx = headers_map[header]['tech_names'][0]['col']; sheet.cell(row=row_num, column=col_idx, value=value)

def identificar_campos_multi_valor(ws) -> set:
    base_name_counts = defaultdict(int); base_name_to_header_l4 = {}; regex_base_name = re.compile(r"^(.*?)(?:\[.*?\])?#\d+\.value$"); header_l4_cache = {}
    for col_idx in range(1, ws.max_column + 1):
        header_l5 = ws.cell(row=5, column=col_idx).value
        if not header_l5 or not isinstance(header_l5, str): continue
        match = regex_base_name.match(header_l5)
        if match:
            base_name = match.group(1); base_name_counts[base_name] += 1
            if base_name not in base_name_to_header_l4:
                current_header_l4 = ""
                for back_col_idx in range(col_idx, 0, -1):
                    cached_val = header_l4_cache.get(back_col_idx)
                    if cached_val: current_header_l4 = cached_val; break
                    cell_val = ws.cell(row=4, column=back_col_idx).value
                    if cell_val: current_header_l4 = str(cell_val).strip(); header_l4_cache[back_col_idx] = current_header_l4; break
                if current_header_l4: base_name_to_header_l4[base_name] = current_header_l4
    multi_value_fields = set()
    for base_name, count in base_name_counts.items():
        if count > 1:
            if base_name in base_name_to_header_l4: header_l4 = base_name_to_header_l4[base_name]; multi_value_fields.add(header_l4)
    return multi_value_fields

def normalizar_ncm(bruto_ncm: str) -> str: return re.sub(r'\D', '', bruto_ncm or '') or ""
def gerar_ncm_aleatorio() -> str:
    while True:
        ncm = f"{random.randint(0, 99_999_999):08d}"
        if ncm != "00000000": return ncm

def normalizar_quantidade(qty_str: str, allow_stock: bool) -> Optional[int]:
    try: qty = int(float(qty_str))
    except (ValueError, TypeError): qty = None
    return qty if allow_stock else None

def analisar_dimensoes(bruto: str) -> List[Optional[float]]:
    partes = [p.strip().replace(',', '.') for p in bruto.split('x')]
    def to_float(s):
        try: return float(s)
        except: return None
    return [to_float(p) for p in partes]

def preencher_dimensoes(ws, row, cabecalhos: Dict[str,int], bruto_dim_str: str, campos_valor: List[str], campos_unidade: Optional[List[str]] = None, unidade_padrao: str = "centímetros"):
    partes = [p.strip().replace(',', '.') for p in bruto_dim_str.split('x')]
    valores = []
    tem_valores_validos = False
    
    for p in partes:
        try:
            valor = float(p)
            valores.append(valor)
            if valor > 0: 
                tem_valores_validos = True
        except ValueError:
            valores.append(None)
    
    _celula = ws.cell
    
    # Preencher os valores das dimensões
    for indice, cabecalho in enumerate(campos_valor):
        col = cabecalhos.get(cabecalho)
        if not col:
            continue
        valor = valores[indice] if indice < len(valores) else None
        if valor is not None:
            _celula(row=row, column=col, value=valor)
    
    # CORREÇÃO: Preencher unidades APENAS para campos específicos de pacote e item
    if tem_valores_validos and campos_unidade:
        for indice, cabecalho_unidade in enumerate(campos_unidade):
            if indice < len(valores) and valores[indice] is not None:
                # Só preencher unidades para campos específicos de pacote e item
                if any(termo in cabecalho_unidade for termo in ["pacote", "item"]):
                    col = cabecalhos.get(cabecalho_unidade)
                    if col:
                        _celula(row=row, column=col, value=unidade_padrao)

def tem_atributos_variacao(product):
    """Verifica se o produto possui atributos de variação"""
    atributos_variacao = ['cor', 'tamanho', 'size', 'color', 'modelo', 'estilo']
    
    for atributo in atributos_variacao:
        if product.get(atributo) and str(product.get(atributo)).strip().lower() not in ['', 'nan', 'none']:
            return True
    
    # Verifica se há múltiplos produtos com mesmo SKU base (indicando variações)
    sku = product.get('sku', '')
    if '-' in sku:  # SKUs de variação geralmente têm formato SKU-VARIACAO
        return True
        
    return False

def determinar_tema_variacao(product):
    """Determina o tema de variação baseado nos atributos do produto"""
    tem_cor = bool(product.get('cor') or product.get('color'))
    tem_tamanho = bool(product.get('tamanho') or product.get('size'))
    
    if tem_cor and tem_tamanho:
        return 'SizeColor'
    elif tem_tamanho:
        return 'SizeName'
    elif tem_cor:
        return 'ColorName'
    else:
        return None

def extrair_sku_pai(sku):
    """Extrai o SKU pai removendo sufixos de variação"""
    if '-' in sku:
        return sku.split('-')[0]
    return sku

def preencher_campos_peso(ws, cabecalhos, bruto_peso_value, unit_map, row):
    def normalizar_numero_interno(bruto):
        try: return float(str(bruto).replace(',', '.'))
        except (ValueError, TypeError): return None
    peso_val = normalizar_numero_interno(bruto_peso_value)
    if peso_val is None: return
    for cabecalho_nome, col_indice in cabecalhos.items():
        if "Peso" in cabecalho_nome and (cabecalho_nome.endswith("peso") or cabecalho_nome.startswith("item_package_weight") or cabecalho_nome.endswith("item")):
            ws.cell(row=row, column=col_indice, value=peso_val)
    # Correção: NÃO preencher unidades automaticamente
    # As unidades devem ser preenchidas apenas quando explicitamente necessário

def normalizar_numero(bruto: str) -> float:
    try: return float(bruto.replace(',', '.'))
    except (ValueError, TypeError): return 0.0

def normalizar_unidade(cabecalho: str, bruto_unit: str) -> str: return MAPA_UNIDADES.get(cabecalho.strip(), "").lower().capitalize()

def processar_string_produto_pai(texto_original: Union[str, float]) -> str:
    texto_str = str(texto_original); texto_sem_produto_pai = texto_str.replace("Produto pai:", ""); partes = texto_sem_produto_pai.split("Variações:"); texto_final = partes[0]
    return texto_final.strip()

def set_cell_value(ws, row, header_map, header_name, value):
    if not value or str(value).strip() == '': return
    col_index = header_map.get(header_name)
    if col_index: ws.cell(row=row, column=col_index, value=value)
    else: pass

def preencher_dados_fixos(ws, row, product, image_urls, cabecalho4, cabecalho5):
    print(f"INFO: Aplicando dados do formulário para o produto SKU {product.get('sku')}")
    set_cell_value(ws, row, cabecalho4, "SKU", product.get("sku"))
    nome_modelo = product.get("nome_marca") if product.get("tipo_marca") == "Marca" else product.get("titulo")
    set_cell_value(ws, row, cabecalho4, "Nome do Modelo", nome_modelo)
    set_cell_value(ws, row, cabecalho4, "Preço sugerido com impostos", product.get("preco"))
    marca_valor = "Genérico" if product.get("tipo_marca") in ("Genérico", "") else product.get("nome_marca")
    set_cell_value(ws, row, cabecalho4, "Fabricante", marca_valor)
    set_cell_value(ws, row, cabecalho4, "Nome da marca", marca_valor)
    
    # Correção: produtos genéricos NÃO devem ter ID do produto preenchido
    if product.get("tipo_marca") != "Genérico":
        set_cell_value(ws, row, cabecalho4, "ID do produto", product.get("id_produto"))
        # CORREÇÃO: NÃO preencher automaticamente "Tipo de ID do produto"
        # Este campo deve ser preenchido apenas quando explicitamente necessário
    
    allow_stock = False
    if product.get("fba_dba", "").upper() == "FBA":
        set_cell_value(ws, row, cabecalho4, "Código do canal de processamento (BR)", "AMAZON_NA")
        allow_stock = True
    else:
        set_cell_value(ws, row, cabecalho4, "Código do canal de processamento (BR)", "DEFAULT")
    
    qty = normalizar_quantidade(product.get("quantidade"), allow_stock)
    set_cell_value(ws, row, cabecalho4, "Quantidade (BR)", qty)
    ncm_val = normalizar_ncm(product.get("ncm")) or gerar_ncm_aleatorio()
    set_cell_value(ws, row, cabecalho4, "Código NCM", ncm_val)
    
    # Correção: NÃO preencher automaticamente campos de hierarquia e variação
    # Estes campos devem ser preenchidos apenas quando explicitamente necessário
    # Removido preenchimento automático de:
    # - Nível de hierarquia
    # - Tipo de relação com o secundário  
    # - Nome do tema de variação
    
    # CORREÇÃO: Preencher dimensões do pacote (sem unidades automáticas)
    if product.get("c_l_a_pacote"):
        preencher_dimensoes(ws, row, cabecalho4, product["c_l_a_pacote"], 
                            ["Comprimento do pacote", "Largura do pacote", "Altura do pacote"],
                            ["Unidade de comprimento do pacote", "Unidade de largura do pacote", "Unidade de altura do pacote"],
                            "centímetros")
    
    # CORREÇÃO: peso do pacote obrigatório com valor padrão e unidade
    peso_pacote = product.get("peso_pacote")
    if not peso_pacote:
        peso_pacote = "100"  # Valor padrão em gramas
        print(f"AVISO: Peso do pacote não informado para SKU {product.get('sku')}, usando valor padrão: 100g")
    
    peso_val = None
    try:
        peso_val = float(str(peso_pacote).replace(',', '.'))
    except (ValueError, TypeError):
        peso_val = 100.0  # Valor padrão
    
    if peso_val:
        set_cell_value(ws, row, cabecalho4, "Peso do pacote", peso_val)
        # CORREÇÃO: Preencher unidade de peso do pacote
        set_cell_value(ws, row, cabecalho4, "Unidade de peso do pacote", "gramas")
    
    # CORREÇÃO: Preencher dimensões do item (sem unidades automáticas)
    if product.get("c_l_a_produto"):
        preencher_dimensoes(ws, row, cabecalho4, product["c_l_a_produto"], 
                            ["Comprimento do item", "Largura do item", "Altura do item"],
                            ["Unidade de comprimento do item", "Unidade de largura do item", "Unidade de altura do item"],
                            "centímetros")
    
    # CORREÇÃO: Preencher País de origem (valor padrão: Brasil)
    set_cell_value(ws, row, cabecalho4, "País de origem", "Brasil")
    
    if image_urls.get('principal'):
        set_cell_value(ws, row, cabecalho4, "URL da imagem principal", image_urls['principal'])
    if image_urls.get('amostra'):
        set_cell_value(ws, row, cabecalho4, "URL da imagem de amostra", image_urls['amostra'])
    
    extra_cols = [cell.column for cell in ws[5] if cell.value and str(cell.value).startswith("other_product_image_locator")]
    for j, url in enumerate(image_urls.get('extra', [])):
        if j < len(extra_cols):
            ws.cell(row=row, column=extra_cols[j], value=url)