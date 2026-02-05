from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from decimal import Decimal
import uuid

class FinanceiroBase(models.Model):
    """Classe base expandida para Faturas, Boletos e Notas Fiscais"""
    
    # Identificação Única
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    numero_documento = models.CharField(max_length=100, blank=True, null=True, unique=False, verbose_name="Nº Documento/Fatura")
    descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descrição")
    
    class OrigemTitulo(models.TextChoices):
        MANUAL = 'MANUAL', _('Lançamento Manual')
        PEDIDO = 'PEDIDO', _('Pedido de Venda')
        CONTRATO = 'CONTRATO', _('Contrato Recorrente')
        NF = 'NF', _('Nota Fiscal')
        IMPORTACAO = 'IMPORTACAO', _('Importação de Planilha/XML')

    class TipoTitulo(models.TextChoices):
        VENDA = 'VENDA', _('Venda de Produto')
        SERVICO = 'SERVICO', _('Prestação de Serviço')
        MENSALIDADE = 'MENSALIDADE', _('Mensalidade')
        ASSINATURA = 'ASSINATURA', _('Assinatura SaaS')
        OUTROS = 'OUTROS', _('Outros')

    origem = models.CharField(max_length=50, choices=OrigemTitulo.choices, default=OrigemTitulo.MANUAL)
    tipo_titulo = models.CharField(max_length=50, choices=TipoTitulo.choices, default=TipoTitulo.SERVICO)
    
    # Datas e Competência
    data_emissao = models.DateField(default=timezone.now, verbose_name="Data de Emissão")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_liquidacao = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    data_competencia = models.DateField(verbose_name="Mês de Competência", help_text="Referência para DRE")
    
    # Valores Estruturados
    valor_original = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    valor_desconto = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_juros = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    valor_multa = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    valor_acrescimo = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor Líquido")
    valor_pago = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_saldo = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    # Pagamento e Dados Bancários
    class FormaPagamento(models.TextChoices):
        BOLETO = 'BOLETO', _('Boleto Bancário')
        PIX = 'PIX', _('Chave Pix')
        CREDITO = 'CREDITO', _('Cartão de Crédito')
        DEBITO = 'DEBITO', _('Cartão de Débito')
        TRANSFERENCIA = 'TRANSF', _('Transferência/TED/DOC')
        DINHEIRO = 'DINHEIRO', _('Espécie/Dinheiro')

    forma_pagamento = models.CharField(max_length=20, choices=FormaPagamento.choices, default=FormaPagamento.BOLETO)
    banco_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name="Banco Emissor")
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta_corrente = models.CharField(max_length=30, blank=True, null=True)
    chave_pix = models.CharField(max_length=255, blank=True, null=True)
    codigo_barras = models.CharField(max_length=255, blank=True, null=True)
    linha_digitavel = models.CharField(max_length=255, blank=True, null=True)

    # Auditoria e Arquivos
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações") 
    comprovante = models.FileField(upload_to='financeiro/comprovantes/%Y/%m/', null=True, blank=True)
    
    # REINTRODUZIDO: Campo para arquivos importados (Blindado contra erros NOT NULL)
    anexos_json = models.JSONField(
        default=dict, 
        blank=True, 
        null=True, 
        help_text="Metadados de arquivos vinculados (XML, Planilhas, etc)"
    )

    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="%(class)s_criado")
    alterado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="%(class)s_alterado")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        
    def recalcular_totais(self):
        """Lógica centralizada de cálculo financeiro"""
        original = self.valor_original or Decimal('0.00')
        juros = self.valor_juros or Decimal('0.00')
        multa = self.valor_multa or Decimal('0.00')
        acrescimo = self.valor_acrescimo or Decimal('0.00')
        desconto = self.valor_desconto or Decimal('0.00')
        recebido = self.valor_pago or Decimal('0.00')

        self.valor_total = (original + juros + multa + acrescimo) - desconto
        self.valor_saldo = self.valor_total - recebido

    def save(self, *args, **kwargs):
        self.recalcular_totais()
        super().save(*args, **kwargs)

class Fatura(FinanceiroBase):
    """Especialização para Contas a Receber (Clientes)"""
    class StatusFatura(models.TextChoices):
        ABERTO = 'aberto', _('Aberto')
        PAGO = 'pago', _('Pago Total')
        PARCIAL = 'parcial', _('Pago Parcial')
        ATRASADO = 'atrasado', _('Em Atraso')
        CANCELADO = 'cancelado', _('Cancelado')
        RENEGOCIADO = 'renegociado', _('Renegociado')

    cliente = models.ForeignKey('tc_crm.Cliente', on_delete=models.PROTECT, related_name='faturas_receber')
    contrato = models.ForeignKey('tc_contratos.Contrato', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusFatura.choices, default=StatusFatura.ABERTO)
    
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        # NOVA REGRA: Lógica de Numeração Automática (Ano-0000000)
        if not self.pk and not self.numero_documento:
            ano_atual = timezone.now().year
            prefixo = f"{ano_atual}-"
            
            # Busca a última fatura gerada para o ano atual
            ultima = Fatura.objects.filter(numero_documento__startswith=prefixo).order_by('numero_documento').last()

            if ultima:
                try:
                    # Extrai o número após o hífen e incrementa
                    ultimo_num = int(ultima.numero_documento.split('-')[1])
                    novo_num = ultimo_num + 1
                except (IndexError, ValueError):
                    novo_num = 1
            else:
                novo_num = 1
            
            self.numero_documento = f"{prefixo}{novo_num:07d}"

        # Automação de Status original
        self.recalcular_totais()
        if self.valor_pago >= self.valor_total and self.valor_total > 0:
            self.status = self.StatusFatura.PAGO
        elif self.valor_pago > 0:
            self.status = self.StatusFatura.PARCIAL
        elif self.data_vencimento and self.data_vencimento < timezone.now().date():
            self.status = self.StatusFatura.ATRASADO
            
        super(Fatura, self).save(*args, **kwargs)

class Despesa(FinanceiroBase):
    """Especialização para Contas a Pagar (Fornecedores)"""
    class StatusDespesa(models.TextChoices):
        AGUARDANDO = 'aguardando', _('Aguardando Pagamento')
        PAGO = 'pago', _('Pago')
        ATRASADO = 'atrasado', _('Em Atraso')
        CANCELADO = 'cancelada', _('Cancelado')

    fornecedor = models.ForeignKey('tc_produtos.Fornecedor', on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusDespesa.choices, default=StatusDespesa.AGUARDANDO)
    
    # Adicione estes campos aqui:
    pago = models.BooleanField(default=False, verbose_name="Pago")
    valor_juros = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Juros")
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Multa")
    data_liquidacao = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        bruto = self.valor_original + self.valor_juros + self.valor_multa + getattr(self, 'valor_acrescimo', 0)
        self.valor_total = bruto - getattr(self, 'valor_desconto', 0)

        # 1. Se estiver marcado como pago
        if self.pago:
            self.status = self.StatusDespesa.PAGO
            if not self.data_liquidacao:
                self.data_liquidacao = hoje
            self.valor_pago = self.valor_total
        else:
            # 2. Se a data de vencimento já passou de HOJE
            if self.data_vencimento and self.data_vencimento < hoje:
                self.status = self.StatusDespesa.ATRASADO
            # 3. Se vence hoje ou no futuro
            else:
                self.status = self.StatusDespesa.AGUARDANDO
                
        super(Despesa, self).save(*args, **kwargs)

class MetaVenda(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='metas_venda')
    ano = models.PositiveIntegerField()
    metas_mensais = models.JSONField(default=dict)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('usuario', 'ano')