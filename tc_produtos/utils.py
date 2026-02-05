# tc_produtos/utils.py
import pandas as pd
from django.db import transaction, IntegrityError
from .models import Produto, CategoriaProduto
from decimal import Decimal
import logging
from django.utils.text import slugify

logger = logging.getLogger(__name__)

def limpar_decimal(valor):
    if valor is None or str(valor).lower() == 'nan' or str(valor).strip() == '':
        return Decimal('0.00')
    try:
        v = str(valor).replace('R$', '').replace(' ', '')
        if ',' in v and '.' in v:
            v = v.replace('.', '').replace(',', '.')
        elif ',' in v:
            v = v.replace(',', '.')
        return Decimal(v)
    except:
        return Decimal('0.00')

def processar_importacao_produtos(arquivo, user, is_servico_context=False):
    extension = arquivo.name.split('.')[-1].lower()
    try:
        if extension == 'csv':
            df = pd.read_csv(arquivo)
        elif extension in ['xls', 'xlsx']:
            df = pd.read_excel(arquivo, engine='openpyxl')
        else:
            return False, "Formato não suportado."
    except Exception as e:
        return False, f"Erro ao ler arquivo: {str(e)}"

    df = df.where(pd.notnull(df), None)
    logs = {'criados': 0, 'atualizados': 0, 'erros': 0, 'itens_novos': [], 'itens_atualizados': []}

    for index, row in df.iterrows():
        try:
            # ISOLAMENTO TOTAL: Cada linha é uma transação independente
            with transaction.atomic():
                nome_item = row.get('nome') or row.get('descrição')
                if not nome_item or str(nome_item).strip().lower() == 'nan':
                    continue
                
                nome_item = str(nome_item).strip().upper()
                
                # --- LÓGICA DE CATEGORIA COM PROTEÇÃO DE SLUG ---
                categoria_nome = row.get('categoria')
                categoria_obj = None
                if categoria_nome and str(categoria_nome).strip().lower() != 'nan':
                    cat_upper = str(categoria_nome).strip().upper()
                    # Busca primeiro para evitar tentativa de create duplicado
                    categoria_obj = CategoriaProduto.objects.filter(nome__iexact=cat_upper).first()
                    if not categoria_obj:
                        try:
                            # Cria em um sub-bloco para não quebrar a transação do produto
                            with transaction.atomic():
                                categoria_obj = CategoriaProduto.objects.create(nome=cat_upper)
                        except IntegrityError:
                            # Se falhou o create, o slug já existe, então buscamos pelo slug
                            categoria_obj = CategoriaProduto.objects.filter(slug=slugify(cat_upper)).first()

                obj_id = row.get('id')
                if obj_id is None or str(obj_id).lower() in ['nan', '', 'none']:
                    obj_id = None
                
                codigo = row.get('codigo_interno') or row.get('código') or row.get('sku')
                if codigo and str(codigo).lower() != 'nan':
                    codigo = str(codigo).strip().upper()
                else:
                    codigo = None

                # BUSCA DO PRODUTO/SERVIÇO
                produto = None
                if obj_id:
                    produto = Produto.objects.filter(id=obj_id).first()
                if not produto and codigo:
                    produto = Produto.objects.filter(codigo_interno__iexact=codigo).first()
                if not produto:
                    # Busca pelo nome exato para evitar erro de UNIQUE SLUG
                    produto = Produto.objects.filter(nome__iexact=nome_item).first()

                data_fields = {
                    'nome': nome_item,
                    'categoria': categoria_obj,
                    'preco_venda_padrao': limpar_decimal(row.get('preco_venda_padrao')),
                    'tipo_produto': 'SERV' if is_servico_context else 'PROD',
                    'descricao_curta': str(row.get('descricao_curta') or '').strip().upper(),
                    'ativo': True
                }

                if produto:
                    for key, value in data_fields.items():
                        setattr(produto, key, value)
                    produto.modificado_por = user
                    produto.save()
                    logs['itens_atualizados'].append(produto)
                    logs['atualizados'] += 1
                else:
                    if codigo:
                        data_fields['codigo_interno'] = codigo
                    
                    novo_item = Produto.objects.create(
                        criado_por=user,
                        modificado_por=user,
                        **data_fields
                    )
                    logs['itens_novos'].append(novo_item)
                    logs['criados'] += 1

        except Exception as e:
            # Se houver qualquer erro nesta linha, ela será revertida e o loop segue
            logger.error(f"Falha na linha {index + 1}: {str(e)}")
            logs['erros'] += 1
            continue # Garante a ida para a próxima linha

    return True, logs