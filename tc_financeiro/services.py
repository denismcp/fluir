import xmltodict
from decimal import Decimal
from django.utils import timezone
from .models import Despesa
from tc_crm.models import Fornecedor

class XMLInvoiceService:
    @staticmethod
    def process_nfe(xml_file):
        """
        Processa o arquivo XML de uma NF-e e cria automaticamente
        um registro no Contas a Pagar (Despesa).
        """
        # Converte XML para dicionário Python
        # Usamos .read() e depois resetamos o ponteiro se necessário, 
        # mas aqui o Django já entrega o arquivo pronto para leitura.
        data = xmltodict.parse(xml_file.read())
        
        # Caminho padrão da infNFe no XML da NF-e
        try:
            nfe = data['nfeProc']['NFe']['infNFe']
        except KeyError:
            # Caso o XML seja apenas a NFe sem o protocolo de autorização
            nfe = data['NFe']['infNFe']
        
        # 1. Extração do Fornecedor (Emitente)
        emitente = nfe['emit']
        cnpj_emit = emitente['CNPJ']
        
        # Busca fornecedor ou cria se for novo (utilizando o padrão do seu CRM)
        fornecedor, fornecedor_novo = Fornecedor.objects.get_or_create(
            cnpj=cnpj_emit,
            defaults={'razao_social': emitente['xNome']}
        )
        
        # 2. Dados Financeiros Principais
        valor_total = Decimal(nfe['total']['ICMSTot']['vNF'])
        numero_nota = nfe['ide']['nNF']
        
        # 3. Extração da Data de Vencimento
        # A NF-e pode ter múltiplas duplicatas ou nenhuma. 
        # Tentamos pegar a primeira, senão usamos a data atual + 7 dias como fallback.
        data_vencimento = None
        try:
            # Tenta acessar o bloco de cobrança/duplicata
            cobranca = nfe.get('cobr', {})
            duplicata = cobranca.get('dup', [])
            
            if isinstance(duplicata, list):
                # Se houver várias parcelas, pegamos a data da primeira para o registro principal
                data_venc_str = duplicata[0]['dVenc']
            else:
                # Se houver apenas uma parcela
                data_venc_str = duplicata['dVenc']
                
            data_vencimento = data_venc_str
        except (KeyError, TypeError):
            # Se não houver bloco de cobrança no XML, define vencimento para hoje + 7 dias
            data_vencimento = timezone.now().date() + timezone.timedelta(days=7)

        # 4. Criação da Despesa
        # Nota: O campo 'status' será automatizado pelo método save() do model que sugerimos
        despesa = Despesa.objects.create(
            descricao=f"Importação NF-e #{numero_nota} - {fornecedor.razao_social}",
            fornecedor=fornecedor,
            valor=valor_total,
            data_vencimento=data_vencimento,
            pago=False,
            status='aguardando'
        )
        
        return despesa, fornecedor_novo