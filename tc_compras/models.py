from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, DecimalField, F
from django.db.models import Q, CheckConstraint, UniqueConstraint
from django.db import transaction
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
from decimal import Decimal
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

# ############################################################################
# 1. ENTIDADES MESTRAS DO MÓDULO COMPRAS
# ############################################################################

class CentroCusto(models.Model):
    """
    Entidade para rastrear onde o custo da compra deve ser alocado.
    """
    nome = models.CharField(max_length=150, unique=True, verbose_name="Nome do Centro de Custo")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")

    class Meta:
        verbose_name = "Centro de Custo"
        verbose_name_plural = "Centros de Custo"
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

# ############################################################################
# 2. REQUISIÇÃO DE COMPRA (SOLICITAÇÃO)
# ############################################################################

class RequisicaoCompra(models.Model):
    """
    Solicitação interna inicial de compra de um item ou serviço.
    """
    class StatusRequisicao(models.TextChoices):
        RASCUNHO = 'rascunho', _('Rascunho')
        PENDENTE_APROVACAO = 'pendente', _('Pendente Aprovação')
        APROVADA = 'aprovada', _('Aprovada')
        REJEITADA = 'rejeitada', _('Rejeitada')
        CONVERTIDA = 'convertida', _('Convertida em Pedido') # Parcial ou Total

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Ref: core.Usuario
        on_delete=models.PROTECT,
        verbose_name="Área/Usuário Solicitante"
    )
    centro_custo = models.ForeignKey(
        CentroCusto,
        on_delete=models.PROTECT,
        verbose_name="Centro de Custo"
    )

    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Solicitação")
    data_limite = models.DateField(verbose_name="Prazo Desejado")
    
    status = models.CharField(
        max_length=20, 
        choices=StatusRequisicao.choices, 
        default=StatusRequisicao.RASCUNHO,
        verbose_name="Status da Requisição"
    )
    
    descricao_geral = models.TextField(verbose_name="Descrição/Motivo Geral da Compra")
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Requisição de Compra"
        verbose_name_plural = "Requisições de Compra"
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f"REQ-{self.pk} ({self.get_status_display()})"
    
    @property
    def valor_total_estimado(self):
        # Soma o valor estimado de todos os itens relacionados
        total = self.itens_requisicao.aggregate(
            sum_total=Sum(F('quantidade') * F('preco_unitario_estimado'), output_field=DecimalField())
        )['sum_total']
        return total.quantize(Decimal("0.01")) if total else Decimal('0.00')

class ItemRequisicao(models.Model):
    """
    Itens dentro de uma Requisição de Compra.
    Um item pode ser um Produto (ESTOQUE) ou um Serviço (SERVICOS).
    """
    requisicao = models.ForeignKey(
        RequisicaoCompra, 
        on_delete=models.CASCADE, 
        related_name='itens_requisicao',
        verbose_name="Requisição"
    )
    
    # Referências para Apps PRODUTOS e SERVICOS
    produto = models.ForeignKey(
        'tc_produtos.Produto', 
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name="Produto (Catálogo)"
    )
    servico = models.ForeignKey(
        'tc_servicos.Servico', 
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name="Serviço (Catálogo)"
    )
    
    nome_customizado = models.CharField(
        max_length=255, 
        blank=True, null=True,
        verbose_name="Nome Customizado do Item"
    )
    especificacao = models.TextField(verbose_name="Especificação/Detalhes Técnicos")
    
    quantidade = models.PositiveIntegerField(default=1, verbose_name="Quantidade Solicitada")
    preco_unitario_estimado = models.DecimalField(
        max_digits=10, decimal_places=2, 
        verbose_name="Preço Unitário Estimado (R$)",
        default=Decimal('0.00')
    )
    
    class Meta:
        verbose_name = "Item da Requisição"
        verbose_name_plural = "Itens da Requisição"
        # Garante que um Item de Requisição aponte para Produto OU Serviço, não ambos
        constraints = [
            models.CheckConstraint(
            condition=Q(produto__isnull=False, servico__isnull=True) | Q(produto__isnull=True, servico__isnull=False),
            name='apenas_um_tipo_de_item_requisicao'
        ),
        ]

    def __str__(self):
        return self.nome_customizado or f"Item REQ-{self.requisicao.pk}"

# ############################################################################
# 3. APROVAÇÃO INTERNA
# ############################################################################

class AprovacaoRequisicao(models.Model):
    """
    Registra a decisão de um aprovador sobre uma Requisição.
    """
    class Decisao(models.TextChoices):
        PENDENTE = 'pendente', _('Pendente')
        APROVADO = 'aprovado', _('Aprovado')
        REJEITADO = 'rejeitado', _('Rejeitado')

    requisicao = models.ForeignKey(
        RequisicaoCompra, 
        on_delete=models.CASCADE, 
        related_name='aprovacoes',
        verbose_name="Requisição de Compra"
    )
    aprovador = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Ref: core.Usuario
        on_delete=models.PROTECT,
        verbose_name="Aprovador Designado"
    )
    decisao = models.CharField(
        max_length=15, 
        choices=Decisao.choices, 
        default=Decisao.PENDENTE,
        verbose_name="Decisão"
    )
    data_decisao = models.DateTimeField(null=True, blank=True, verbose_name="Data da Decisão")
    comentarios = models.TextField(blank=True, null=True, verbose_name="Comentários do Aprovador")

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Se for a primeira vez que a decisão está sendo tomada (de PENDENTE para algo)
        if is_new and self.decisao != self.Decisao.PENDENTE:
            self.data_decisao = models.DateTimeField(auto_now=True)

            # LÓGICA DE ATUALIZAÇÃO DO STATUS DA REQUISIÇÃO
            if self.decisao == self.Decisao.APROVADO:
                # Se for o único nível de aprovação, muda para APROVADA. 
                # (Em um sistema real, precisaria de um modelo de 'FluxoDeAprovacao'
                # para verificar se todos os aprovadores já responderam.)
                self.requisicao.status = RequisicaoCompra.StatusRequisicao.APROVADA
                self.requisicao.save(update_fields=['status'])
            
            elif self.decisao == self.Decisao.REJEITADO:
                self.requisicao.status = RequisicaoCompra.StatusRequisicao.REJEITADA
                self.requisicao.save(update_fields=['status'])

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Aprovação de Requisição"
        verbose_name_plural = "Aprovações de Requisição"
        unique_together = ('requisicao', 'aprovador')

# ############################################################################
# 4. PEDIDO DE COMPRA (PO)
# ############################################################################

class PedidoCompra(models.Model):
    """
    Documento formal enviado a um Fornecedor. 
    Criado a partir de uma Requisição Aprovada.
    """
    class StatusPedido(models.TextChoices):
        RASCUNHO = 'rascunho', _('Rascunho')
        ENVIADO = 'enviado', _('Enviado ao Fornecedor')
        RECEBIDO_PARCIAL = 'parcial', _('Recebido Parcialmente')
        RECEBIDO_TOTAL = 'total', _('Recebido Totalmente')
        CANCELADO = 'cancelado', _('Cancelado')

    fornecedor = models.ForeignKey(
        'tc_produtos.Fornecedor', # Ref: produtos.Fornecedor
        on_delete=models.PROTECT,
        verbose_name="Fornecedor"
    )
    requisicao_origem = models.ForeignKey(
        RequisicaoCompra, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Requisição de Origem"
    )

    status = models.CharField(
        max_length=20, 
        choices=StatusPedido.choices, 
        default=StatusPedido.RASCUNHO,
        verbose_name="Status do Pedido"
    )
    
    # Integração com Financeiro (será atualizado quando o Recebimento ocorrer)
    fatura_vinculada = models.ForeignKey(
        'tc_financeiro.Despesa', # Ref: financeiro.Despesa
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Despesa (Contas a Pagar)"
    )

    data_emissao = models.DateField(auto_now_add=True, verbose_name="Data de Emissão")
    custo_frete = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Custo do Frete")

    history = HistoricalRecords()

    @property
    def valor_total_po(self):
        """ Calcula o valor total do PO (Soma dos itens + Frete). """
        items_total = self.itens_pedido.aggregate(
            sum_total=Sum(F('quantidade_pedida') * F('preco_unitario'), output_field=DecimalField())
        )['sum_total']
        
        items_total = items_total.quantize(Decimal("0.01")) if items_total else Decimal('0.00')
        return items_total + self.custo_frete
        
    class Meta:
        verbose_name = "Pedido de Compra (PO)"
        verbose_name_plural = "Pedidos de Compra (POs)"

    def __str__(self):
        return f"PO-{self.pk} ({self.fornecedor.razao_social})"


class ItemPedidoCompra(models.Model):
    """
    Detalhes de cada Produto/Serviço no Pedido de Compra.
    """
    pedido_compra = models.ForeignKey(
        PedidoCompra, 
        on_delete=models.CASCADE, 
        related_name='itens_pedido',
        verbose_name="Pedido de Compra"
    )
    requisicao_item = models.ForeignKey(
        ItemRequisicao, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Item da Requisição de Origem"
    )
    
    # Dados finais da negociação (inclui os campos ItemRequisicao, se houver)
    descricao_item = models.CharField(max_length=255, verbose_name="Descrição do Item")
    
    quantidade_pedida = models.PositiveIntegerField(default=1, verbose_name="Quantidade Pedida")
    preco_unitario = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Preço Unitário Negociado (R$)"
    )
    
    # Controle de Recebimento
    quantidade_recebida = models.PositiveIntegerField(default=0, verbose_name="Quantidade Recebida Acumulada")

    history = HistoricalRecords()
    
    @property
    def saldo_a_receber(self):
        return self.quantidade_pedida - self.quantidade_recebida

    @property
    def total_item(self):
        try:
            return Decimal(self.quantidade_pedida or 0) * Decimal(self.preco_unitario or 0)
        except:
            return Decimal('0.00')

    class Meta:
        verbose_name = "Item do Pedido de Compra"
        verbose_name_plural = "Itens do Pedido de Compra"
        # Garante unicidade de itens dentro do mesmo pedido
        unique_together = ('pedido_compra', 'descricao_item') 
    
    def __str__(self):
        return f"{self.quantidade_pedida} x {self.descricao_item}"

# ############################################################################
# 5. CONTROLE DE RECEBIMENTO (Integração com ESTOQUE)
# ############################################################################

class RecebimentoItem(models.Model):
    """
    Registra a entrada física de itens de um Pedido de Compra.
    Esta ação integra com o App ESTOQUE.
    """
    item_pedido = models.ForeignKey(
        ItemPedidoCompra, 
        on_delete=models.PROTECT, # Protege o recebimento se o item for deletado
        related_name='recebimentos',
        verbose_name="Item do Pedido de Compra"
    )

    # Nota: Não precisamos de FK direta para produtos/serviços, 
    # pois o item_pedido já aponta para a Requisição -> Produto/Serviço.
    
    quantidade_recebida = models.PositiveIntegerField(verbose_name="Quantidade Recebida Nesta Transação")
    data_recebimento = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora do Recebimento")
    
    recebedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Ref: core.Usuario
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Responsável pelo Recebimento"
    )
    
    observacao = models.TextField(verbose_name="Observações (Divergências, Qualidade, etc.)", blank=True, null=True)

    history = HistoricalRecords()

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new:
            item_pedido = self.item_pedido
            pedido = item_pedido.pedido_compra
            
            # 1. Validação de Saldo
            if self.quantidade_recebida > item_pedido.saldo_a_receber:
                raise ValidationError(_(f"Quantidade a receber ({self.quantidade_recebida}) excede o saldo restante no pedido ({item_pedido.saldo_a_receber})."))

            # 2. Atualiza o saldo do ItemPedidoCompra
            item_pedido.quantidade_recebida = F('quantidade_recebida') + self.quantidade_recebida
            item_pedido.save(update_fields=['quantidade_recebida'])
            item_pedido.refresh_from_db()

            # 3. Integração com ESTOQUE (Se for um PRODUTO estocável)
            if item_pedido.requisicao_item and item_pedido.requisicao_item.produto:
                ProdutoModel = apps.get_model('produtos', 'Produto')
                EstoqueModel = apps.get_model('estoque', 'ItemEstoque')
                MovimentacaoModel = apps.get_model('estoque', 'MovimentacaoEstoque')

                produto_id = item_pedido.requisicao_item.produto.id
                
                # Procura o ItemEstoque principal para este produto (Regra de Negócio: usa localização padrão 'Geral')
                # Em um sistema real, aqui você usaria o ItemEstoque específico do local de recebimento.
                try:
                    item_estoque = EstoqueModel.objects.get(produto_id=produto_id)
                except EstoqueModel.DoesNotExist:
                    # Cria um ItemEstoque se não existir
                    item_estoque = EstoqueModel.objects.create(
                        produto_id=produto_id, 
                        quantidade=0, 
                        localizacao='Geral'
                    )

                # Cria a Movimentação de Estoque (ENTRADA)
                MovimentacaoModel.objects.create(
                    item_estoque=item_estoque,
                    tipo=MovimentacaoModel.TipoMovimentacao.ENTRADA_COMPRA,
                    quantidade=self.quantidade_recebida,
                    responsavel=self.recebedor,
                    observacao=f"Entrada PO-{pedido.pk} - {self.observacao or 'Recebimento de compra'}"
                )
            
            # 4. Atualiza o status do Pedido de Compra
            total_pedida = pedido.itens_pedido.aggregate(Sum('quantidade_pedida'))['quantidade_pedida__sum']
            total_recebida = pedido.itens_pedido.aggregate(Sum('quantidade_recebida'))['quantidade_recebida__sum']

            if total_recebida == total_pedida:
                pedido.status = PedidoCompra.StatusPedido.RECEBIDO_TOTAL
            elif total_recebida > 0:
                pedido.status = PedidoCompra.StatusPedido.RECEBIDO_PARCIAL
            
            pedido.save(update_fields=['status'])

            # 5. Geração da Despesa no Financeiro (Regra 8)
            # A Despesa (Contas a Pagar) deve ser gerada/atualizada AQUI, 
            # após o recebimento, garantindo que o valor é devido.
            # O código para isso será implementado no App FINANCEIRO, mas a chamada viria aqui.
            # Ex:
            # if not pedido.fatura_vinculada:
            #    FinanceiroModel = apps.get_model('financeiro', 'Despesa')
            #    valor_recebido = self.quantidade_recebida * item_pedido.preco_unitario
            #    FinanceiroModel.objects.create(
            #       ... campos da despesa ...
            #       valor=valor_recebido,
            #       po_vinculado=pedido
            #    )


        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Recebimento de Item"
        verbose_name_plural = "Recebimentos de Itens"
        ordering = ['-data_recebimento']

    def __str__(self):
        return f"Recebimento de {self.quantidade_recebida} para PO-{self.item_pedido.pedido_compra.pk}"