import json
import uuid
import mimetypes
import base64
import os
from datetime import timedelta
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from celery.result import AsyncResult

import pandas as pd

from . import utils
from .tasks import generate_spreadsheet_task, scrape_images_task, organizador_ia_task
from .models import UploadedImage
from backbeecatalog.celery import app as celery_app 

class ScrapeImagesView(APIView):
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        link = request.data.get('link')
        if not link:
            return Response({'error': 'O link do anúncio é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = scrape_images_task.delay(link)
            return Response({'message': 'Extração de imagens iniciada.', 'task_id': task.id}, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'error': f'Erro ao iniciar a tarefa de extração: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SpreadsheetUploadView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('planilha')
        if not file_obj:
            return Response({'error': 'Nenhum arquivo de planilha enviado.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            df = pd.read_excel(file_obj, skiprows=1, engine='openpyxl')
            
            df_selecionado = df.head(20)

            registros = df_selecionado.fillna('').to_dict("records")
            lista_produtos = []
            for linha in registros:
                sku_original = str(linha.get("SKU:", "")).strip()
                if not sku_original:
                    continue

                processed_sku = utils.processar_string_produto_pai(sku_original)
                
                titulo = str(linha.get("NOME DO PRODUTO", "")).strip()
                if not titulo:
                    tipo_marca = str(linha.get("TIPO DE MARCA", "")).strip()
                    marca = str(linha.get("MARCA:", "")).strip()
                    nome_base = marca if tipo_marca == "Marca" else tipo_marca
                    titulo = f"{nome_base} {processed_sku}" if nome_base else processed_sku

                produto = {
                    "titulo": titulo,
                    "sku": processed_sku,
                    "tipo_marca": str(linha.get("TIPO DE MARCA", "")).strip(),
                    "nome_marca": str(linha.get("MARCA:", "")).strip(),
                    "preco": linha.get("PREÇO DE VENDA:", ""),
                    "fba_dba": str(linha.get("LOGÍSTICA", "")).strip(),
                    "id_produto": str(linha.get("EAN:", "")).strip(),
                    "ncm": str(linha.get("NCM:", "")).strip(),
                    "quantidade": linha.get("QUANTIDADE EM ESTOQUE PARA DBA", ""),
                    "tipo_id_produto": str(linha.get("TIPO DE ID DO PRODUTO", "")).strip(),
                    "peso_pacote": linha.get("PESO DO PACOTE: (Em gramas)", ""),
                    "c_l_a_pacote": str(linha.get("COMPRIMENTO X  LARGURA X ALTURA  (DO PACOTE)", "")).strip(),
                    "peso_produto": str(linha.get("PESO DO PRODUTO: (Em gramas) ", "")),
                    "c_l_a_produto": str(linha.get("COMPRIMENTO X  LARGURA X ALTURA (DO PRODUTO)", "")).strip(),
                    "ajuste": str(linha.get("O PRODUTO É AJUSTÁVEL?", "")).strip(),
                    "tema_variacao_pai": str(linha.get("TEMA DE VARIAÇÃO PAI", "")).strip()
                }
                lista_produtos.append(produto)
            return Response(lista_produtos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Erro ao processar a planilha: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SpreadsheetGenerateView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, *args, **kwargs):
        products_data_str = request.data.get('products_data')
        amazon_template_file = request.FILES.get('amazon_template')

        if not products_data_str:
            return Response({'error': 'Dados dos produtos não encontrados.'}, status=status.HTTP_400_BAD_REQUEST)
        if not amazon_template_file:
            return Response({'error': 'Modelo de planilha da Amazon não enviado.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            products_data = json.loads(products_data_str)
        except json.JSONDecodeError:
            return Response({'error': 'JSON de dados dos produtos inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        
        temp_dir = os.path.join(settings.BASE_DIR, "temp_files")
        os.makedirs(temp_dir, exist_ok=True)
        temp_template_path = os.path.join(temp_dir, f"input_{uuid.uuid4()}.xlsm")

        with open(temp_template_path, 'wb+') as destination:
            for chunk in amazon_template_file.chunks():
                destination.write(chunk)

        image_urls_map = {}
        s3_client = utils.get_s3_client()
        for key, uploaded_file in request.FILES.items():
            if not key.startswith('imagem_'): continue
            try:
                parts = key.split('_')
                product_index = int(parts[1].replace('p', ''))
                image_type = parts[2]
            except (IndexError, ValueError):
                continue

            if str(product_index) not in image_urls_map:
                image_urls_map[str(product_index)] = {'principal': '', 'amostra': '', 'extra': []}
            
            s3_filename = f"produto_{product_index}/{image_type}/{uuid.uuid4()}_{uploaded_file.name}"
            content_type, _ = mimetypes.guess_type(uploaded_file.name, strict=False)
            if content_type is None: content_type = 'application/octet-stream'
            
            try:
                s3_client.upload_fileobj(
                    uploaded_file, utils.AWS_STORAGE_BUCKET_NAME, s3_filename,
                    ExtraArgs={'ContentType': content_type, 'ACL': 'public-read'}
                )
                s3_url = f"https://{utils.AWS_STORAGE_BUCKET_NAME}.s3.{utils.AWS_S3_REGION_NAME}.amazonaws.com/{s3_filename}"
                UploadedImage.objects.create(url=s3_url, expires_at=timezone.now() + timedelta(hours=12))
                
                if image_type == 'extra':
                    image_urls_map[str(product_index)]['extra'].append(s3_url)
                else:
                    image_urls_map[str(product_index)][image_type] = s3_url
            except Exception as e:
                return Response({'error': f'Erro no upload da imagem {uploaded_file.name}: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        maestra_task = generate_spreadsheet_task.delay(products_data, image_urls_map, temp_template_path)
        
        try:
            chord_id = maestra_task.get(timeout=20) 
        except Exception as e:
            if os.path.exists(temp_template_path):
                os.remove(temp_template_path)
            return Response(
                {'error': f'Falha ao iniciar a cadeia de processamento: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {'message': 'Processamento da planilha iniciado.', 'task_id': chord_id}, 
            status=status.HTTP_202_ACCEPTED
        )

class OrganizadorIAView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('product_info_csv')
        if not csv_file:
            return Response({'error': 'Arquivo CSV não enviado.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            csv_content_base64 = base64.b64encode(csv_file.read()).decode('utf-8')
            task = organizador_ia_task.delay(csv_content_base64)
            return Response({'message': 'Processamento do Organizador iniciado.', 'task_id': task.id}, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({'error': f'Falha ao iniciar a tarefa do Organizador: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskStatusView(APIView):
    def get(self, request, task_id, format=None):
        task_result = AsyncResult(task_id)

        if task_result.state == 'SUCCESS':
            return Response({
                'status': 'SUCCESS',
                'result': task_result.result
            })
        elif task_result.state == 'FAILURE':
            return Response({
                'status': 'FAILURE',
                'result': str(task_result.info)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else: # PENDING, PROGRESS, etc.
            return Response({
                'status': task_result.state,
                'result': task_result.info
            })
