from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.apps import apps
from django.db.models import Count, Sum, F, DecimalField
from django.core.exceptions import ValidationError
from django.db import transaction
from tc_core.mixins import PermissionRequiredMixin

from .models import CentroCusto, RequisicaoCompra, ItemRequisicao, PedidoCompra, AprovacaoRequisicao, RecebimentoItem
from .forms import RequisicaoCompraForm, ItemRequisicaoForm, PedidoCompraForm, RecebimentoItemForm

# Importando modelos externos necessários para a lógica de recebimento e itens
try:
    ProdutoModel = apps.get_model('produtos', 'Produto')
    EstoqueModel = apps.get_model('estoque', 'ItemEstoque')
    MovimentacaoModel = apps.get_model('estoque', 'MovimentacaoEstoque')
except LookupError:
    ProdutoModel = None
    EstoqueModel = None
    MovimentacaoModel = None

# ############################################################################
# REQUISIÇÃO DE COMPRA (Solicitação)
# ############################################################################

class RequisicaoCompraListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'compras.view_requisicaocompra'
    model = RequisicaoCompra
    template_name = 'compras/requisicao_list.html'
    context_object_name = 'requisicoes'
    ordering = ['-data_solicitacao']

    def get_queryset(self):
        # Anota o número de itens e o valor total estimado para exibição na lista
        return RequisicaoCompra.objects.annotate(
            num_itens=Count('itens_requisicao'),
            valor_total_estimado=Sum(F('itens_requisicao__quantidade') * F('itens_requisicao__preco_unitario_estimado'), output_field=DecimalField())
        ).order_by('-data_solicitacao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Requisições de Compra'
        return context

class RequisicaoCompraCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'compras.add_requisicaocompra'
    model = RequisicaoCompra
    form_class = RequisicaoCompraForm
    template_name = 'compras/requisicao_form.html'
    
    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('compras:requisicao_detail', kwargs={'pk': self.object.pk})

class RequisicaoCompraUpdateView(LoginRequiredMixin, UpdateView):
    model = RequisicaoCompra
    form_class = RequisicaoCompraForm
    
    def get_template_names(self):
        if self.request.htmx:
            return ['compras/partials/requisicao_form_modal.html'] 
        return ['compras/requisicao_form.html']
    
    def get_success_url(self):
        return reverse('compras:requisicao_detail', kwargs={'pk': self.object.pk})

class RequisicaoCompraDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'compras.view_requisicaocompra'
    model = RequisicaoCompra
    template_name = 'compras/requisicao_detail.html'
    context_object_name = 'requisicao'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = f'Requisição REQ-{self.object.pk}'
        context['itens'] = self.object.itens_requisicao.all()
        context['aprovacoes'] = self.object.aprovacoes.all().order_by('-data_decisao')
        # Adiciona a URL para criar um novo item (será injetada no botão do template)
        context['item_create_url'] = reverse('compras:itemrequisicao_create', kwargs={'requisicao_pk': self.object.pk})
        return context
        
# ############################################################################
# ITENS DA REQUISIÇÃO (ItemRequisicao)
# ############################################################################

class ItemRequisicaoCreateView(LoginRequiredMixin, CreateView):
    model = ItemRequisicao
    form_class = ItemRequisicaoForm
    template_name = 'compras/partials/itemrequisicao_form_modal.html'

    def form_valid(self, form):
        requisicao = get_object_or_404(RequisicaoCompra, pk=self.kwargs['requisicao_pk'])
        form.instance.requisicao = requisicao
        return super().form_valid(form)

    def get_success_url(self):
        # Após a criação, redireciona para a página de detalhes da requisição
        return reverse('compras:requisicao_detail', kwargs={'pk': self.object.requisicao.pk})

# ############################################################################
# APROVAÇÃO (AprovacaoRequisicao)
# ############################################################################

class AprovacaoRequisicaoCreateView(LoginRequiredMixin, CreateView):
    model = AprovacaoRequisicao
    fields = ['decisao', 'comentarios']
    template_name = 'compras/partials/aprovacao_form_modal.html'

    def form_valid(self, form):
        requisicao = get_object_or_404(RequisicaoCompra, pk=self.kwargs['pk'])
        
        if requisicao.status != RequisicaoCompra.StatusRequisicao.PENDENTE_APROVACAO:
             form.add_error(None, "Esta requisição não está pendente de aprovação.")
             return self.form_invalid(form)
             
        form.instance.requisicao = requisicao
        form.instance.aprovador = self.request.user
        
        # O save() no modelo AprovacaoRequisicao cuidará de atualizar o status da Requisição
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requisicao'] = get_object_or_404(RequisicaoCompra, pk=self.kwargs['pk'])
        return context
    
    def get_success_url(self):
        # Retorna um refresh para atualizar a página de detalhes da requisição
        return reverse('compras:requisicao_detail', kwargs={'pk': self.object.requisicao.pk})

# ############################################################################
# PEDIDO DE COMPRA (PO)
# ############################################################################

class PedidoCompraListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'compras.view_pedidocompra'
    model = PedidoCompra
    template_name = 'compras/pedidocompra_list.html'
    context_object_name = 'pedidos'
    ordering = ['-data_emissao']

class PedidoCompraCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # Permissão de Alto Nível
    permission_required = 'compras.add_pedidocompra'
    model = PedidoCompra
    form_class = PedidoCompraForm
    template_name = 'compras/pedidocompra_form.html' # Usaremos um formulário de página completa aqui

    def get_initial(self):
        initial = super().get_initial()
        requisicao = get_object_or_404(RequisicaoCompra, pk=self.kwargs['requisicao_pk'])
        initial['requisicao_origem'] = requisicao.pk
        
        # Lógica para pré-preencher fornecedor (se relevante)
        # ... (similar ao que foi comentado no form.py) ...
        return initial
        
    def form_valid(self, form):
        # Validação extra: a requisição deve estar APROVADA
        requisicao = get_object_or_404(RequisicaoCompra, pk=self.kwargs['requisicao_pk'])
        if requisicao.status != RequisicaoCompra.StatusRequisicao.APROVADA:
            form.add_error(None, "Somente requisições aprovadas podem ser convertidas em Pedido de Compra.")
            return self.form_invalid(form)
            
        form.instance.requisicao_origem = requisicao
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Copia itens da Requisição para o Pedido de Compra (ItemPedidoCompra)
            ItemPedidoCompraModel = apps.get_model('compras', 'ItemPedidoCompra')
            for item_req in requisicao.itens_requisicao.all():
                ItemPedidoCompraModel.objects.create(
                    pedido_compra=self.object,
                    requisicao_item=item_req,
                    descricao_item=item_req.nome_customizado or item_req.produto.nome if item_req.produto else item_req.servico.nome,
                    quantidade_pedida=item_req.quantidade,
                    preco_unitario=item_req.preco_unitario_estimado
                )
            
            # Atualiza o status da Requisição para CONVERTIDA
            requisicao.status = RequisicaoCompra.StatusRequisicao.CONVERTIDA
            requisicao.save(update_fields=['status'])
            
            return response
        
    def get_success_url(self):
        return reverse('compras:pedidocompra_detail', kwargs={'pk': self.object.pk})

class PedidoCompraDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'compras.view_pedidocompra'
    model = PedidoCompra
    template_name = 'compras/pedidocompra_detail.html'
    context_object_name = 'pedido'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = f'Pedido de Compra PO-{self.object.pk}'
        context['itens'] = self.object.itens_pedido.all()
        return context

# ############################################################################
# RECEBIMENTO DE ITEM (Integração com ESTOQUE e FINANCEIRO)
# ############################################################################

class RecebimentoItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # Permissão de Estoquista/Recebimento
    permission_required = 'compras.add_recebimentoitem'
    model = RecebimentoItem
    form_class = RecebimentoItemForm
    template_name = 'compras/partials/recebimento_form_modal.html'

    def form_valid(self, form):
        item_pedido = get_object_or_404(PedidoCompra.itens_pedido.through, pk=self.kwargs['item_pk'])
        
        form.instance.item_pedido = item_pedido
        form.instance.recebedor = self.request.user
        
        # A lógica crítica de atualização de saldo, status e validação de quantidade
        # está no save() do modelo RecebimentoItem (que criamos no turno anterior do modelo)
        try:
            response = super().form_valid(form)
            # Força o refresh da página pai (PedidoCompra Detail)
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'}) 
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_pedido'] = get_object_or_404(PedidoCompra.itens_pedido.through, pk=self.kwargs['item_pk'])
        context['page_heading'] = f'Registrar Recebimento para PO-{context["item_pedido"].pedido_compra.pk}'
        return context
        
    def get_success_url(self):
        return reverse('compras:pedidocompra_detail', kwargs={'pk': self.object.item_pedido.pedido_compra.pk})

# ############################################################################
# CADASTROS MESTRES (Centro de Custo)
# ############################################################################

class CentroCustoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'compras.view_centrocusto'
    model = CentroCusto
    template_name = 'compras/centrocusto_list.html'
    context_object_name = 'centros_custo'
    ordering = ['nome']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Centros de Custo'
        return context