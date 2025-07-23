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
from collections import defaultdict 


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

# *** INÍCIO DA REFATORAÇÃO: Recebe product_data completo ***
@shared_task
def generate_main_content_task(product_index, product_data):
    try:
        start_time = time.time()
        titulo_produto = product_data.get('titulo', f'Produto {product_index}')
        print(f"INFO: [Sub-tarefa] Iniciando geração de conteúdo principal para produto {product_index} ('{titulo_produto[:30]}...')")
        
        # Formata o contexto completo do produto
        product_context = utils.format_product_context(product_data)
        
        main_ia_chain = utils.get_main_ia_chain()
        # Invoca a IA com o contexto completo
        parsed_content = main_ia_chain.invoke({"product_context": product_context})
        
        end_time = time.time()
        print(f"--- [PROFILE][Sub-tarefa: Conteúdo Principal] Produto {product_index} levou: {end_time - start_time:.2f}s")
        data_to_return = parsed_content.dict() if isinstance(parsed_content, BaseModel) else parsed_content
        return {'type': 'main_content', 'product_index': product_index, 'data': data_to_return}
    except Exception as e:
        print(f"ERRO na sub-tarefa de conteúdo principal para produto {product_index}: {e}")
        traceback.print_exc()
        return {'type': 'main_content', 'product_index': product_index, 'data': {}}
# *** FIM DA REFATORAÇÃO ***

# *** INÍCIO DA REFATORAÇÃO: Recebe product_data completo ***
@shared_task
def choose_options_task(product_index, product_data, temp_file_path):
    wb = None
    try:
        start_time = time.time()
        titulo_produto = product_data.get('titulo', f'Produto {product_index}')
        print(f"INFO: [Sub-tarefa] Iniciando escolha de opções para produto {product_index} ('{titulo_produto[:30]}...')")
        
        wb = load_workbook(filename=temp_file_path, keep_vba=True)
        ws = wb["Modelo"]
        field_options = utils.coletar_opcoes_campo(wb, "Modelo", 7)
        multi_value_fields = utils.identificar_campos_multi_valor(ws)
        fields_for_ai_batch = [
            {"field_name": name, "options": opts, "multi_value": name in multi_value_fields, "is_critical": name in utils.campos_criticos}
            for name, campo_obj in field_options.items()
            if (opts := [o for o in campo_obj['options'] if o and o.lower() != 'nan'])
        ]

        if not fields_for_ai_batch:
            print(f"INFO: [Sub-tarefa] Nenhum campo de seleção para preencher para o produto {product_index}. Pulando.")
            return {'type': 'options', 'product_index': product_index, 'data': {}}
            
        vectorstore = utils.get_vectorstore()
        retriever = vectorstore.as_retriever()
        # Passa o product_data completo para a função da IA
        ai_choices, _ = utils.escolher_com_ia(product_data, fields_for_ai_batch, frozenset(), retriever)
        end_time = time.time()
        print(f"--- [PROFILE][Sub-tarefa: Escolher Opções] Produto {product_index} levou: {end_time - start_time:.2f}s")
        return {'type': 'options', 'product_index': product_index, 'data': ai_choices}
    except Exception as e:
        print(f"ERRO na sub-tarefa de escolher opções para produto {product_index}: {e}")
        traceback.print_exc()
        return {'type': 'options', 'product_index': product_index, 'data': {}}
    finally:
        if wb:
            wb.close()
# *** FIM DA REFATORAÇÃO ***

# *** INÍCIO DA REFATORAÇÃO: Recebe product_data completo ***
@shared_task
def process_chunk_task(product_index, chunk_name, product_data, temp_file_path, campos_criticos_list, persona):
    wb = None
    try:
        start_time = time.time()
        print(f"INFO: [Sub-tarefa] Iniciando processamento do chunk '{chunk_name}' para produto {product_index}...")
        
        wb = load_workbook(filename=temp_file_path, keep_vba=True)
        ws = wb["Modelo"]
        chunks = utils.mapear_chunks_da_planilha(ws)
        chunk_data = chunks[chunk_name].to_dict()
        
        vectorstore = utils.get_vectorstore()
        retriever = vectorstore.as_retriever()
        
        titulo_produto = product_data.get('titulo', f'Produto {product_index}')
        context_str = "\n".join([doc.page_content for doc in retriever.get_relevant_documents(f"Informações para {titulo_produto}")])

        # Passa o product_data completo para a função da IA
        ai_choices = utils.processar_chunk_com_ia(
            chunk_name, chunk_data, product_data, context_str, set(campos_criticos_list), persona
        )
        end_time = time.time()
        print(f"--- [PROFILE][Sub-tarefa: Chunk '{chunk_name}'] Produto {product_index} levou: {end_time - start_time:.2f}s")
        return {'type': 'chunk', 'product_index': product_index, 'chunk_name': chunk_name, 'data': ai_choices}
    except Exception as e:
        print(f"ERRO na sub-tarefa de chunk '{chunk_name}' para produto {product_index}: {e}")
        traceback.print_exc()
        return {'type': 'chunk', 'product_index': product_index, 'chunk_name': chunk_name, 'data': {}}
    finally:
        if wb:
            wb.close()
# *** FIM DA REFATORAÇÃO ***

@shared_task(bind=True)
def assemble_spreadsheet_task(self, results_list, products_data, image_urls_map, temp_file_path):
    wb = None
    try:
        self.update_state(state='PROGRESS', meta={'step': 'Montando planilha final...'})
        print(f"INFO: [Finalizador] Iniciando montagem final para {len(products_data)} produtos.")

        wb = load_workbook(filename=temp_file_path, keep_vba=True)
        ws = wb["Modelo"]
        
        cabecalho4 = {str(cell.value).strip(): cell.column for cell in ws[4] if cell.value}
        cabecalho5 = {str(cell.value).strip(): cell.column for cell in ws[5] if cell.value}
        
        organized_results = defaultdict(lambda: defaultdict(dict))
        for result in results_list:
            if not result: continue
            idx = result.get('product_index')
            res_type = result.get('type')
            if res_type == 'chunk':
                organized_results[idx]['chunks'][result.get('chunk_name')] = result.get('data', {})
            elif res_type:
                organized_results[idx][res_type] = result.get('data', {})

        for i, product in enumerate(products_data):
            row = 7 + i
            print(f"INFO: [Finalizador] Preenchendo linha {row} para SKU {product.get('sku')}")
            
            product_results = organized_results[i]
            updated_product = product.copy()
            image_urls = image_urls_map.get(str(i), {})

            main_content = product_results.get('main_content', {})
            if main_content:
                updated_product['titulo'] = main_content.get("titulo", updated_product['titulo'])
                utils.set_cell_value(ws, row, cabecalho4, "Nome do item", main_content.get("titulo"))
                utils.set_cell_value(ws, row, cabecalho4, "Descrição do Produto", main_content.get("descricao_produto"))
                
                bullet_points = main_content.get("bullet_points", [])
                for idx, bp_data in enumerate(bullet_points):
                    if idx < 5:
                        utils.set_cell_value(ws, row, cabecalho5, f"bullet_point{idx+1}", bp_data.get("bullet_point", ""))
                
                utils.set_cell_value(ws, row, cabecalho5, "generic_keyword1", main_content.get("palavras_chave", ""))

            options_content = product_results.get('options', {})
            if options_content:
                field_options = utils.coletar_opcoes_campo(wb, "Modelo", row)
                for field, choice in options_content.items():
                    if field in field_options:
                        utils.preencher_grupo_de_colunas(ws, row, field_options[field]['col_indices'], choice if isinstance(choice, list) else [choice], field)

            chunks_content = product_results.get('chunks', {})
            if chunks_content:
                chunks_map = utils.mapear_chunks_da_planilha(ws)
                for chunk_name, chunk_data in chunks_content.items():
                    if chunk_name in chunks_map:
                        for campo in chunks_map[chunk_name].campos:
                            field_name = campo['cabecalho_l5']
                            if field_name in chunk_data and not ws.cell(row=row, column=campo["col"]).value:
                                valor = chunk_data[field_name]
                                if valor and str(valor).strip().lower() != 'nan':
                                    ws.cell(row=row, column=campo["col"], value=str(valor))

            utils.preencher_dados_fixos(ws, row, updated_product, image_urls, cabecalho4, cabecalho5)

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
        if wb:
            wb.close()
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@shared_task(bind=True)
def generate_spreadsheet_task(self, products_data, image_urls_map, template_path):
    wb = None
    try:
        if not products_data:
            raise ValueError("Nenhum dado de produto fornecido.")

        self.update_state(state='PROGRESS', meta={'step': 'Preparando ambiente para tarefas...'})

        temp_dir = os.path.join(settings.BASE_DIR, "temp_files")
        os.makedirs(temp_dir, exist_ok=True)
        assemble_temp_path = os.path.join(temp_dir, f"{self.request.id}_assemble.xlsm")
        
        with open(template_path, 'rb') as src, open(assemble_temp_path, 'wb') as dst:
            dst.write(src.read())

        header_tasks = []
        
        wb = load_workbook(filename=template_path, keep_vba=True)
        chunks = utils.mapear_chunks_da_planilha(wb["Modelo"])
        wb.close()
        wb = None

        # *** INÍCIO DA REFATORAÇÃO: Passa o product_data completo para as sub-tarefas ***
        for i, product in enumerate(products_data):
            # Passa o dicionário 'product' inteiro
            header_tasks.append(generate_main_content_task.s(i, product))
            header_tasks.append(choose_options_task.s(i, product, assemble_temp_path))

            chunk_personas = {
                "Oferta (BR) - (Vender na Amazon)": "Especialista em dados de OFERTA...",
                "Detalhes do produto": "Especialista em especificações TÉCNICAS...",
                "Segurança e Conformidade": "Especialista em CONFORMIDADE e segurança..."
            }
            for name, persona in chunk_personas.items():
                if name in chunks:
                    header_tasks.append(
                        process_chunk_task.s(i, name, product, assemble_temp_path, list(utils.campos_criticos), persona)
                    )
        # *** FIM DA REFATORAÇÃO ***

        print(f"INFO: [Maestra] Criando chord para {len(products_data)} produtos.")
        
        body_task = assemble_spreadsheet_task.s(
            products_data, 
            image_urls_map, 
            assemble_temp_path
        )

        the_chord = chord(header_tasks, body_task)
        result_chord = the_chord.apply_async()
        
        return result_chord.id

    except Exception as e:
        traceback.print_exc()
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise
    finally:
        if wb:
            wb.close()
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
        
        # *** INÍCIO DA REFATORAÇÃO: Usa a nova função para formatar o contexto ***
        product_context = utils.format_product_context(product_info)
        
        try:
            # Passa o contexto formatado para a IA
            ia_output = ia_chain.invoke({"product_context": product_context})
            
            new_product_data = {**product_info, **ia_output}
            
            if 'bullet_points' in new_product_data and isinstance(new_product_data['bullet_points'], list):
                new_product_data['bullet_points'] = [bp.get('bullet_point') for bp in new_product_data['bullet_points'] if isinstance(bp, dict) and 'bullet_point' in bp]

            generated_products_data.append(new_product_data)

        except Exception as e:
            logger.error(f"Erro na IA para o produto na linha {i+2}: {e}")
            continue
        # *** FIM DA REFATORAÇÃO ***
        
        time.sleep(1.5)

    return {
        'status': 'SUCCESS',
        'result': {
            'products_data': generated_products_data
        }
    }