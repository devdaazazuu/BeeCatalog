import io
import json
import os
import re
import time
import uuid
import traceback
import base64
from celery import shared_task, group, chord
from celery.result import AsyncResult
from django.conf import settings
from celery.utils.log import get_task_logger
from openpyxl import load_workbook
from pydantic.v1 import BaseModel
import pandas as pd
from . import utils


logger = get_task_logger(__name__)

@shared_task(bind=True)
def scrape_images_task(self, url):
    try:
        self.update_state(state='PROGRESS', meta={'step': 'Iniciando extração...'})
        image_urls = utils.scrape_mercadolivre_images(url)
        print(f"INFO: [Scraper] Extraídas {len(image_urls)} imagens da URL: {url}")
        return {'status': 'SUCCESS', 'image_urls': image_urls}
    except Exception as e:
        print(f"ERRO na tarefa de scraping: {e}")
        traceback.print_exc()
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise

@shared_task
def generate_main_content_task(titulo_produto):
    try:
        start_time = time.time()
        print(f"INFO: [Sub-tarefa] Iniciando geração de conteúdo principal para '{titulo_produto[:30]}...'")
        main_ia_chain = utils.get_main_ia_chain()
        parsed_content = main_ia_chain.invoke({"product_name": titulo_produto})
        end_time = time.time()
        print(f"--- [PROFILE][Sub-tarefa: Conteúdo Principal] Execução levou: {end_time - start_time:.2f}s")
        data_to_return = parsed_content.dict() if isinstance(parsed_content, BaseModel) else parsed_content
        return {'type': 'main_content', 'data': data_to_return}
    except Exception as e:
        print(f"ERRO na sub-tarefa de conteúdo principal: {e}")
        traceback.print_exc()
        return {'type': 'main_content', 'data': {}}

@shared_task
def choose_options_task(titulo_produto, fields_for_ai_batch):
    try:
        start_time = time.time()
        print(f"INFO: [Sub-tarefa] Iniciando escolha de opções para '{titulo_produto[:30]}...'")
        if not fields_for_ai_batch:
            print("INFO: [Sub-tarefa] Nenhum campo de seleção para preencher. Pulando.")
            return {'type': 'options', 'data': {}}
        vectorstore = utils.get_vectorstore()
        retriever = vectorstore.as_retriever()
        ai_choices, _ = utils.escolher_com_ia(titulo_produto, fields_for_ai_batch, frozenset(), retriever)
        end_time = time.time()
        print(f"--- [PROFILE][Sub-tarefa: Escolher Opções] Execução levou: {end_time - start_time:.2f}s")
        return {'type': 'options', 'data': ai_choices}
    except Exception as e:
        print(f"ERRO na sub-tarefa de escolher opções: {e}")
        traceback.print_exc()
        return {'type': 'options', 'data': {}}

@shared_task
def process_chunk_task(chunk_name, chunk_data, titulo_produto, context_str, campos_criticos_list, persona):
    try:
        start_time = time.time()
        print(f"INFO: [Sub-tarefa] Iniciando processamento do chunk '{chunk_name}' para '{titulo_produto[:30]}...'")
        ai_choices = utils.processar_chunk_com_ia(
            chunk_name, chunk_data, titulo_produto, context_str, set(campos_criticos_list), persona
        )
        end_time = time.time()
        print(f"--- [PROFILE][Sub-tarefa: Chunk '{chunk_name}'] Execução levou: {end_time - start_time:.2f}s")
        return {'type': 'chunk', 'chunk_name': chunk_name, 'data': ai_choices}
    except Exception as e:
        print(f"ERRO na sub-tarefa de chunk '{chunk_name}': {e}")
        traceback.print_exc()
        return {'type': 'chunk', 'chunk_name': chunk_name, 'data': {}}

@shared_task(bind=True)
def assemble_spreadsheet_task(self, results_list, product, image_urls, temp_file_path):
    try:
        print(f"INFO: [Finalizador] Iniciando montagem final para o produto SKU {product.get('sku')}")
        self.update_state(state='PROGRESS', meta={'step': 'Montando planilha final...'})

        wb = load_workbook(filename=temp_file_path, keep_vba=True)
        ws = wb["Modelo"]
        
        cabecalho4 = {str(cell.value).strip(): cell.column for cell in ws[4] if cell.value}
        cabecalho5 = {str(cell.value).strip(): cell.column for cell in ws[5] if cell.value}
        
        row = 7

        field_options = utils.coletar_opcoes_campo(wb, "Modelo", row)
        chunks = utils.mapear_chunks_da_planilha(ws)
        
        updated_product = product.copy()

        for result in results_list:
            if not result or not result.get('data'): continue
            
            if result['type'] == 'main_content':
                parsed_content = result['data']
                ai_optimized_title = parsed_content.get("titulo")

                if ai_optimized_title:
                    updated_product['titulo'] = ai_optimized_title
                
                utils.set_cell_value(ws, row, cabecalho4, "Nome do item", ai_optimized_title)
                utils.set_cell_value(ws, row, cabecalho4, "Descrição do Produto", parsed_content.get("descricao_produto"))
                
                bullet_points = parsed_content.get("bullet_points", [])
                for idx, bp_data in enumerate(bullet_points):
                    if idx < 5:
                        bp_text = bp_data.get("bullet_point", "")
                        utils.set_cell_value(ws, row, cabecalho5, f"bullet_point{idx+1}", bp_text)

                palavras_chave_str = parsed_content.get("palavras_chave", "")
                utils.set_cell_value(ws, row, cabecalho5, "generic_keyword1", palavras_chave_str)
            
            elif result['type'] == 'options':
                for field, choice in result['data'].items():
                    if field in field_options:
                        utils.preencher_grupo_de_colunas(ws, row, field_options[field]['col_indices'], choice if isinstance(choice, list) else [choice], field)
            
            elif result['type'] == 'chunk':
                for campo in chunks[result['chunk_name']].campos:
                    field_name = campo['cabecalho_l5']
                    if field_name in result['data'] and not ws.cell(row=row, column=campo["col"]).value:
                        valor = result['data'][field_name]
                        if valor and str(valor).strip().lower() != 'nan':
                            ws.cell(row=row, column=campo["col"], value=str(valor))

        utils.preencher_dados_fixos(ws, row, updated_product, image_urls, cabecalho4, cabecalho5)

        variations = product.get("variacoes", [])
        if variations:
            utils.set_cell_value(ws, row, cabecalho4, "Nível de hierarquia", "Produto Pai")
            utils.set_cell_value(ws, row, cabecalho4, "Tipo de relação com o secundário", "Variação")
            utils.set_cell_value(ws, row, cabecalho4, "Nome do tema de variação", product.get("tema_variacao_pai"))

        for var_idx, var in enumerate(variations):
            linha_variacao = row + var_idx + 1
            for col_idx in range(1, ws.max_column + 1):
                if not ws.cell(row=linha_variacao, column=col_idx).value:
                    ws.cell(row=linha_variacao, column=col_idx, value=ws.cell(row=row, column=col_idx).value)
            
            utils.set_cell_value(ws, linha_variacao, cabecalho4, "SKU", var.get('sku'))
            utils.set_cell_value(ws, linha_variacao, cabecalho4, "Nível de hierarquia", "Produto Filho")
            utils.set_cell_value(ws, linha_variacao, cabecalho4, "SKU do produto pai", product.get("sku"))
            
            tema_variacao_valor = var.get('cor') if var.get('tipo') == 'cor' else f"{var.get('cla')}cm / {var.get('peso')}g"
            utils.set_cell_value(ws, linha_variacao, cabecalho4, "Nome do tema de variação", tema_variacao_valor)
            if var.get('imagem'):
                utils.set_cell_value(ws, linha_variacao, cabecalho4, "URL da imagem principal", var.get('imagem'))

        print("INFO: [Finalizador] Montagem final concluída. Salvando arquivo...")
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        encoded_file = base64.b64encode(buf.getvalue()).decode('utf-8')
        final_filename = f"PLANILHA_AMAZON_{time.strftime('%Y-%m-%d_%H-%M')}.xlsm"
        
        return {'status': 'SUCCESS', 'file_content': encoded_file, 'filename': final_filename}
    except Exception as e:
        traceback.print_exc()
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise
    finally:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@shared_task(bind=True)
def generate_spreadsheet_task(self, products_data, image_urls_map, template_path):
    try:
        if not products_data:
            raise ValueError("Nenhum dado de produto fornecido.")
        product = products_data[0]
        image_urls = image_urls_map.get('0', {})
        
        self.update_state(state='PROGRESS', meta={'step': 'Preparando ambiente para tarefas...'})

        # Carrega o workbook diretamente do caminho do arquivo temporário
        try:
            wb = load_workbook(filename=template_path, keep_vba=True)
            ws = wb["Modelo"]
        except Exception as e:
            logger.error(f"Erro ao carregar o template da Amazon do caminho {template_path}: {e}")
            self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
            raise
        
        # Cria um *outro* arquivo temporário para passar para a task de montagem
        temp_dir = os.path.join(settings.BASE_DIR, "temp_files")
        os.makedirs(temp_dir, exist_ok=True)
        assemble_temp_path = os.path.join(temp_dir, f"{self.request.id}_assemble.xlsm")
        wb.save(assemble_temp_path)

        header_tasks = []
        titulo_produto = product.get("titulo", "")
        
        header_tasks.append(generate_main_content_task.s(titulo_produto))

        field_options = utils.coletar_opcoes_campo(wb, "Modelo", 7)
        multi_value_fields = utils.identificar_campos_multi_valor(ws)
        fields_for_ai_batch = [
            {"field_name": name, "options": opts, "multi_value": name in multi_value_fields, "is_critical": name in utils.campos_criticos}
            for name, campo_obj in field_options.items()
            if (opts := [o for o in campo_obj['options'] if o and o.lower() != 'nan'])
        ]
        header_tasks.append(choose_options_task.s(titulo_produto, fields_for_ai_batch))

        chunks = utils.mapear_chunks_da_planilha(ws)
        vectorstore = utils.get_vectorstore()
        retriever = vectorstore.as_retriever()
        context_str = "\n".join([doc.page_content for doc in retriever.get_relevant_documents(f"Informações para {titulo_produto}")])
        chunk_personas = {
            "Oferta (BR) - (Vender na Amazon)": "Especialista em dados de OFERTA...",
            "Detalhes do produto": "Especialista em especificações TÉCNICAS...",
            "Segurança e Conformidade": "Especialista em CONFORMIDADE e segurança..."
        }
        for name, persona in chunk_personas.items():
            if name in chunks:
                header_tasks.append(
                    process_chunk_task.s(name, chunks[name].to_dict(), titulo_produto, context_str, list(utils.campos_criticos), persona)
                )

        print(f"INFO: [Maestra] Criando chord para o produto SKU {product.get('sku')}")
        
        body_task = assemble_spreadsheet_task.s(
            product=product, 
            image_urls=image_urls, 
            temp_file_path=assemble_temp_path
        )

        the_chord = chord(header_tasks, body_task)
        result_chord = the_chord.apply_async()
        
        return result_chord.id

    except Exception as e:
        traceback.print_exc()
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise
    finally:
        # Garante que o arquivo de template de ENTRADA seja sempre deletado
        if 'template_path' in locals() and os.path.exists(template_path):
            os.remove(template_path)


@shared_task(bind=True)
def organizador_ia_task(self, csv_content_base64):
    logger.info("Iniciando tarefa do Organizador IA.")
    try:
        csv_bytes = base64.b64decode(csv_content_base64)
        csv_file_obj = io.StringIO(csv_bytes.decode('utf-8'))
        df = pd.read_csv(csv_file_obj)
        products_to_process = df.to_dict('records')
        total_products = len(products_to_process)
    except Exception as e:
        logger.error(f"Erro ao ler o arquivo CSV: {e}")
        self.update_state(state='FAILURE', meta={'step': 'Erro de Leitura de CSV'})
        return {'status': 'FAILURE', 'result': 'CSV inválido ou mal formatado.'}

    ia_chain = utils.get_main_ia_chain()
    generated_products_data = []

    for i, product_info in enumerate(products_to_process):
        self.update_state(state='PROGRESS', meta={'step': 'Gerando conteúdo', 'current': i + 1, 'total': total_products})
        
        product_name_str = ", ".join([f"{key}: {value}" for key, value in product_info.items() if pd.notna(value)])
        
        try:
            ia_output = ia_chain.invoke({"product_name": product_name_str})
            
            new_product_data = {**product_info, **ia_output}
            
            if 'bullet_points' in new_product_data and isinstance(new_product_data['bullet_points'], list):
                new_product_data['bullet_points'] = [bp.get('bullet_point') for bp in new_product_data['bullet_points'] if isinstance(bp, dict) and 'bullet_point' in bp]

            generated_products_data.append(new_product_data)

        except Exception as e:
            logger.error(f"Erro na IA para o produto na linha {i+2}: {e}")
            continue
        
        time.sleep(1.5)

    return {
        'status': 'SUCCESS',
        'result': {
            'products_data': generated_products_data
        }
    }
