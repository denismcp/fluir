import datetime
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse
from tc_core.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.apps import apps
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import timedelta
from django.contrib.auth.decorators import login_required

from .models import Cliente, Contato, EtapaVenda, Oportunidade, Atividade, Proposta, ItemProposta, MetaMensal
from .forms import ClienteForm, ContatoForm, OportunidadeForm, AtividadeForm, PropostaForm, FornecedorForm

from tc_produtos.models import Fornecedor # Certifique-se de importar o correto
from tc_produtos.forms import FornecedorForm # Use o form oficial se existir
from tc_core.models import Usuario  # CORRETO: Usuario vem do core

# ############################################################################
# CLIENTES (CRUD COMPLETO)
# ############################################################################

class ClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'tc_crm.view_cliente'
    model = Cliente
    # Se a requisição for HTMX, renderiza apenas a tabela, senão a página inteira
    def get_template_names(self):
        if self.request.htmx:
            return ['crm/partials/cliente_table.html']
        return ['crm/cliente_list.html']
        
    context_object_name = 'clientes'
    ordering = ['razao_social']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro de Busca (Nome ou CNPJ)
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                models.Q(razao_social__icontains=q) | 
                models.Q(nome_fantasia__icontains=q) | 
                models.Q(cnpj_cpf__icontains=q)
            )

        # Filtro por Vendedor Responsável
        # (Filtra clientes que possuem oportunidades vinculadas ao vendedor)
        vendedor_id = self.request.GET.get('vendedor')
        if vendedor_id:
            queryset = queryset.filter(oportunidade__responsavel_id=vendedor_id).distinct()
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Carrega vendedores para o select do filtro
        context['vendedores'] = Usuario.objects.filter(departamento='comercial', is_active=True)
        return context

class ClienteDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'tc_crm.view_cliente'
    model = Cliente
    template_name = 'crm/cliente_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.now()
        
        # Oportunidades Ganhas (Vendas)
        vendas = Oportunidade.objects.filter(
            cliente=self.object, 
            etapa__e_etapa_ganha=True
        )
        
        # Cálculos de Indicadores
        context['total_vendas_geral'] = vendas.aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
        context['total_vendas_ano'] = vendas.filter(data_fechamento_real__year=hoje.year).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
        
        tres_meses_atras = hoje - timedelta(days=90)
        context['total_vendas_trimestre'] = vendas.filter(data_fechamento_real__gte=tres_meses_atras).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
        
        um_mes_atras = hoje - timedelta(days=30)
        context['total_vendas_mes'] = vendas.filter(data_fechamento_real__gte=um_mes_atras).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0

        # Dados para as Abas
        context['oportunidades'] = self.object.oportunidade_set.all().order_by('-id')
        # Busca propostas de todas as oportunidades do cliente
        context['propostas'] = Proposta.objects.filter(oportunidade__cliente=self.object).order_by('-data_criacao')
        context['ultimas_vendas_list'] = vendas.order_by('-data_fechamento_real')[:10]
        
        return context

class ClienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'tc_crm.add_cliente'
    model = Cliente
    form_class = ClienteForm
    template_name = 'crm/partials/cliente_form_modal.html' 
    
    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class ClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'tc_crm.change_cliente'
    model = Cliente
    form_class = ClienteForm
    # Alterado de 'crm/cliente_form.html' para o padrão de modal
    template_name = 'crm/partials/cliente_form_modal.html' 

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class ClienteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'tc_crm.delete_cliente'
    model = Cliente
    template_name = 'crm/cliente_confirm_delete.html'
    success_url = reverse_lazy('crm:cliente_list')

# ############################################################################
# CONTATOS (CRUD COMPLETO)
# ############################################################################

class ContatoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'tc_crm.add_contato'
    model = Contato
    form_class = ContatoForm
    template_name = 'crm/partials/contato_form_modal.html'
    
    def form_valid(self, form):
        cliente = get_object_or_404(Cliente, pk=self.kwargs['cliente_pk'])
        form.instance.cliente = cliente
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class ContatoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'tc_crm.change_contato'
    model = Contato
    form_class = ContatoForm
    template_name = 'crm/partials/contato_form_modal.html'

    def form_valid(self, form):
        # O Django já sabe quem é o cliente porque ele está vinculado ao objeto 'contato'
        self.object = form.save()
        
        if self.request.htmx:
            # Retornamos 204 para fechar a modal e HX-Refresh para atualizar a lista de contatos na tela de detalhes
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
            
        return super().form_valid(form)

class ContatoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'tc_crm.delete_contato'
    model = Contato
    template_name = 'crm/contato_confirm_delete.html' 

    def get_success_url(self):
        cliente_pk = self.object.cliente.pk
        return reverse('crm:cliente_detail', kwargs={'pk': cliente_pk})

# ############################################################################
# PIPELINE (Kanban & Oportunidades)
# ############################################################################

class KanbanView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'tc_crm.view_oportunidade'
    template_name = 'crm/kanban.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Pega o vendedor da URL, se não houver, assume o próprio usuário
        vendedor_id = self.request.GET.get('vendedor')
        
        etapas = EtapaVenda.objects.all().order_by('ordem')
        for etapa in etapas:
            # Filtro base
            queryset = Oportunidade.objects.filter(etapa=etapa)
            
            # Se for vendedor comum, ele só vê as DELE, independente do que estiver na URL
            if not (user.is_superuser or user.departamento in ['diretoria', 'financeiro']):
                queryset = queryset.filter(responsavel=user)
            # Se for gestor e houver um ID na URL, filtra por aquele vendedor específico
            elif vendedor_id:
                queryset = queryset.filter(responsavel_id=vendedor_id)
                
            etapa.oportunidades_lista = queryset
            
        context['etapas'] = etapas
        return context

class OportunidadeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'tc_crm.view_oportunidade'
    model = Oportunidade
    template_name = 'crm/oportunidade_detail.html'
    context_object_name = 'oportunidade'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['atividades'] = self.object.atividade_set.all()
        context['propostas'] = self.object.proposta_set.all().order_by('-id_proposta')
        return context

class OportunidadeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'tc_crm.add_oportunidade'
    model = Oportunidade
    form_class = OportunidadeForm
    template_name = 'crm/partials/oportunidade_form_modal.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filtra apenas usuários do comercial e que estejam ativos
        form.fields['responsavel'].queryset = Usuario.objects.filter(
            departamento='comercial', 
            is_active=True
        )
        return form
    def get_initial(self):
        initial = super().get_initial()
        # Se um ID de cliente for passado via URL, pré-seleciona no formulário
        cliente_id = self.request.GET.get('cliente_id')
        if cliente_id:
            initial['cliente'] = get_object_or_404(Cliente, pk=cliente_id)
        return initial

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class OportunidadeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'tc_crm.change_oportunidade'
    model = Oportunidade
    form_class = OportunidadeForm
    template_name = 'crm/partials/oportunidade_form_modal.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['responsavel'].queryset = Usuario.objects.filter(
            departamento='comercial', 
            is_active=True
        )
        return form

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Se mudou para etapa Ganha, troca a modal pela de fechamento
            if self.object.etapa.e_etapa_ganha:
                response = HttpResponse(status=204)
                response['HX-Trigger'] = f'abrirFechamento-{self.object.pk}'
                return response
            
            # Caso contrário, apenas atualiza a página de detalhes
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

@require_POST
def oportunidade_duplicar(request, pk):
    """Cria uma nova oportunidade baseada em uma existente."""
    original = get_object_or_404(Oportunidade, pk=pk)
    
    # Cria a cópia limpando o ID para o banco gerar um novo
    nova_op = Oportunidade.objects.get(pk=pk)
    nova_op.pk = None
    nova_op.id = None
    nova_op.nome = f"{original.nome} (CÓPIA)"
    # Reseta campos de fechamento real se houver
    nova_op.data_fechamento_real = None
    nova_op.save()
    
    messages.success(request, f"Oportunidade duplicada como '{nova_op.nome}'")
    
    # Redireciona para a nova oportunidade criada
    return redirect('crm:oportunidade_detail', pk=nova_op.pk)

@csrf_exempt
@require_POST
def atualizar_etapa_oportunidade(request):
    opportunity_id = request.POST.get('opportunity_id')
    new_etapa_id = request.POST.get('new_etapa_id')
    oportunidade = get_object_or_404(Oportunidade, pk=opportunity_id)
    etapa = get_object_or_404(EtapaVenda, pk=new_etapa_id)
    
    oportunidade.etapa = etapa
    oportunidade.save()

    # Se a etapa for "Ganha", dispara o gatilho para o frontend abrir a modal de fechamento
    if etapa.e_etapa_ganha:
        response = HttpResponse(status=204)
        response['HX-Trigger'] = f'abrirFechamento-{oportunidade.pk}'
        return response
        
    return HttpResponse(status=204)

# Nova View para Renderizar a Modal de Escolha de Proposta
def oportunidade_fechamento_view(request, pk):
    oportunidade = get_object_or_404(Oportunidade, pk=pk)
    # Importante: usar o related_name 'proposta_set' se não houver um customizado
    propostas = oportunidade.proposta_set.all() 
    return render(request, 'crm/partials/oportunidade_fechamento_modal.html', {
        'oportunidade': oportunidade,
        'propostas': propostas
    })

# View de Conclusão de Negócio com atualização automática de valor
@login_required
def oportunidade_concluir(request, pk):
    oportunidade = get_object_or_404(Oportunidade, pk=pk)
    
    if request.method == 'POST':
        id_ganhadora = request.POST.get('proposta_vencedora')
        
        # 1. Busca a proposta selecionada para capturar o valor real
        proposta_vencedora = get_object_or_404(Proposta, pk=id_ganhadora)
        
        # 2. Marca a vencedora como ACEITA
        proposta_vencedora.status = 'aceita'
        proposta_vencedora.save()
        
        # 3. Marca todas as outras propostas desta oportunidade como RECUSADAS
        oportunidade.proposta_set.exclude(pk=id_ganhadora).update(status='recusada')
        
        # 4. Atualiza a Oportunidade com os dados reais do fechamento
        etapa_ganha = EtapaVenda.objects.filter(e_etapa_ganha=True).first()
        if etapa_ganha:
            oportunidade.etapa = etapa_ganha
            
        # AJUSTE SOLICITADO: Traz o valor total da proposta aprovada para a oportunidade
        # Assim, o KPI de "Vendas do Mês" refletirá o valor real do contrato/venda
        oportunidade.valor_estimado = proposta_vencedora.valor_total
        
        # Registra a data do fechamento real
        oportunidade.data_fechamento_real = timezone.now()
        
        # Salva todas as alterações na Oportunidade
        oportunidade.save()
            
        # 5. Retorna 204 para o HTMX fechar a modal e disparar o refresh
        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'oportunidadeAtualizada'
        return response
    
    return HttpResponse("Método não permitido", status=405)

#Listagem das oportunidade de todos os cliente
class OportunidadeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'tc_crm.view_oportunidade'
    model = Oportunidade
    template_name = 'crm/oportunidade_list.html'
    context_object_name = 'oportunidades'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        order_by = self.request.GET.get('order_by', '-data_fechamento_prevista')
        return queryset.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.now()
        
        # 1. Pipeline Total (Soma de tudo que NÃO é Ganha nem Perdida)
        context['pipeline_total'] = Oportunidade.objects.exclude(
            etapa__e_etapa_ganha=True
        ).exclude(
            etapa__nome__icontains='Perdida'
        ).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0

        # 2. Ganhos no Mês (Soma das oportunidades Ganhas no mês atual)
        context['total_ganho_mes'] = Oportunidade.objects.filter(
            etapa__e_etapa_ganha=True,
            data_fechamento_real__month=hoje.month,
            data_fechamento_real__year=hoje.year
        ).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0

        # 3. Quantidade de Negócios Ativos (Exclui Ganhos e Perdidos)
        context['qtd_oportunidades'] = Oportunidade.objects.exclude(
            etapa__e_etapa_ganha=True
        ).exclude(
            etapa__nome__icontains='Perdida'
        ).count()

        return context

# ############################################################################
# PROPOSTAS & ITENS REATIVOS
# ############################################################################

class PropostaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'tc_crm.add_proposta'
    model = Proposta
    form_class = PropostaForm
    template_name = 'crm/partials/proposta_form_modal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['oportunidade'] = get_object_or_404(Oportunidade, pk=self.kwargs['oportunidade_pk'])
        return context

    def form_valid(self, form):
        oportunidade = get_object_or_404(Oportunidade, pk=self.kwargs['oportunidade_pk'])
        form.instance.oportunidade = oportunidade
        form.instance.criado_por = self.request.user
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class PropostaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'tc_crm.change_proposta'
    model = Proposta
    form_class = PropostaForm
    template_name = 'crm/partials/proposta_form_modal.html'

    def form_invalid(self, form):
        # Isso imprimirá o motivo do erro no seu VS Code/Terminal
        print("ERRO DE VALIDAÇÃO NA PROPOSTA:", form.errors)
        return super().form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # IMPORTANTE: Passa a oportunidade dona da proposta para a modal
        context['oportunidade'] = self.object.oportunidade
        return context

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Retorna status 204 para fechar a modal e HX-Refresh para atualizar a lista
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class PropostaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'tc_crm.delete_proposta'
    model = Proposta
    template_name = 'crm/partials/confirm_delete_modal.html'

    def get_success_url(self):
        # Fallback para acessos não-HTMX
        return reverse('crm:oportunidade_detail', kwargs={'pk': self.object.oportunidade.pk})

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete()
        
        if self.request.htmx:
            # CORREÇÃO: Envia 204 para fechar a modal e Refresh para atualizar a tela
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
            
        messages.success(self.request, "Proposta excluída com sucesso.")
        return redirect(success_url)

class PropostaItensView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'tc_crm.change_proposta'
    model = Proposta
    template_name = 'crm/proposta_itens.html'
    context_object_name = 'proposta'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produtos_catalogo'] = apps.get_model('tc_produtos', 'Produto').objects.all()
        context['servicos_catalogo'] = apps.get_model('tc_servicos', 'Servico').objects.all()
        return context

@require_POST
def proposta_duplicar(request, pk):
    """Cria uma cópia da proposta e de todos os seus itens associados."""
    original = get_object_or_404(Proposta, pk=pk)
    oportunidade_id = original.oportunidade.id
    
    # 1. Clona a Proposta (Capa)
    nova_proposta = Proposta.objects.get(pk=pk)
    nova_proposta.pk = None
    nova_proposta.id = None
    # Limpa o ID antigo para o save() gerar um novo código (ex: 20251231T005)
    nova_proposta.id_proposta = "" 
    nova_proposta.status = 'elaboracao'
    nova_proposta.data_criacao = timezone.now()
    nova_proposta.save()
    
    # 2. Clona os Itens da Proposta original para a nova
    # Busca itens usando a relação correta 'itens' ou 'itemproposta_set'
    itens_originais = original.itens.all() if hasattr(original, 'itens') else original.itemproposta_set.all()
    
    for item in itens_originais:
        item.pk = None
        item.id = None
        item.proposta = nova_proposta
        item.save()
    
    messages.success(request, f"Proposta duplicada com sucesso!")
    return redirect('crm:oportunidade_detail', pk=oportunidade_id)

@require_POST
def atualizar_item_proposta(request, pk):
    item = get_object_or_404(ItemProposta, pk=pk)
    if 'qtd' in request.POST:
        item.quantidade = int(request.POST.get('qtd'))
    if 'preco' in request.POST:
        item.preco_unitario = Decimal(request.POST.get('preco').replace(',', '.'))
    item.save()

    # Identificação do Tipo idêntica ao Template Principal
    badge_html = ""
    if "SER-" in item.resumo_item or "MÃO DE OBRA" in item.resumo_item.upper():
        badge_html = '<span class="badge-type badge-servico">Serviço</span>'
    elif "CON-" in item.resumo_item or "SOFT" in item.resumo_item.upper():
        badge_html = '<span class="badge-type badge-software">Software</span>'
    else:
        badge_html = '<span class="badge-type badge-fisico">Físico</span>'

    # HTML Corrigido com as colunas <td> corretas para manter o alinhamento
    html = f"""
    <tr class="item-row" id="item-{item.pk}">
        <td class="px-4 align-middle">{badge_html}</td>
        <td class="align-middle"><strong>{item.resumo_item}</strong></td>
        <td class="align-middle">
            <input type="number" name="qtd" value="{item.quantidade}" 
                   class="form-control form-control-sm text-center input-edit"
                   hx-post="/crm/proposta/item/{item.pk}/atualizar/" 
                   hx-trigger="change" hx-target="#item-{item.pk}" hx-swap="outerHTML">
        </td>
        <td class="align-middle text-right">
            <input type="text" name="preco" value="{item.preco_unitario}" 
                   class="form-control form-control-sm text-right input-edit"
                   hx-post="/crm/proposta/item/{item.pk}/atualizar/" 
                   hx-trigger="change" hx-target="#item-{item.pk}" hx-swap="outerHTML">
        </td>
        <td class="align-middle text-right font-weight-bold text-dark">R$ {item.total}</td>
        <td class="align-middle text-center">
            <button class="btn btn-link text-danger p-0" hx-delete="/crm/proposta/item/{item.pk}/excluir/" 
                    hx-target="#item-{item.pk}" hx-swap="delete" hx-confirm="Remover item?">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    </tr>
    """
    response = HttpResponse(html)
    response['HX-Trigger'] = 'atualizarTotalGeral'
    return response

@require_POST
def item_proposta_add(request, pk):
    proposta = get_object_or_404(Proposta, pk=pk)
    catalogo_id = request.POST.get('catalogo_id')
    tipo, item_id = catalogo_id.split('-')
    
    if tipo == 'P':
        catalogo_item = get_object_or_404(apps.get_model('tc_produtos', 'Produto'), pk=item_id)
        preco_venda = catalogo_item.preco_venda_padrao
    else:
        catalogo_item = get_object_or_404(apps.get_model('tc_servicos', 'Servico'), pk=item_id)
        preco_venda = getattr(catalogo_item, 'preco_venda_padrao', Decimal('0.00'))

    item = ItemProposta.objects.create(proposta=proposta, quantidade=1, preco_unitario=preco_venda, resumo_item=catalogo_item.nome)
    return atualizar_item_proposta(request, item.pk)

def excluir_item_proposta(request, pk):
    if request.method in ['DELETE', 'POST']:
        item = get_object_or_404(ItemProposta, pk=pk)
        item.delete()
        response = HttpResponse("")
        response['HX-Trigger'] = 'atualizarTotalGeral'
        return response
    return HttpResponse(status=405)

def proposta_total_fragment(request, pk):
    proposta = get_object_or_404(Proposta, pk=pk)
    return HttpResponse(f"R$ {proposta.valor_total}")

#Lista de propostas
class PropostaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'tc_crm.view_proposta'
    model = Proposta
    template_name = 'crm/proposta_list.html'
    context_object_name = 'propostas'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        order_by = self.request.GET.get('order_by', '-data_criacao')
        return queryset.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Total Emitido (Soma da receita inicial + mensal de todas as propostas)
        # Ajustamos para usar os campos reais do banco: receita_inicial e receita_mensal
        propostas_todas = Proposta.objects.all()
        total = 0
        for p in propostas_todas:
            total += p.valor_total # Aqui usamos a propriedade que você já tem no model
        context['total_emitido'] = total

        # 2. Propostas Aceitas
        propostas_aceitas = Proposta.objects.filter(status='aceita')
        total_aceito = 0
        for p in propostas_aceitas:
            total_aceito += p.valor_total
        context['total_aceito'] = total_aceito

        # 3. Quantidade Em Aberto
        context['qtd_pendente'] = Proposta.objects.filter(status='elaboracao').count()
        
        return context
        
# ############################################################################
# PDF & ATIVIDADES
# ############################################################################

def proposta_pdf_view(request, oport_id, tipo='completa'):
    oportunidade = get_object_or_404(Oportunidade, pk=oport_id)
    proposta_id = request.GET.get('proposta_id')
    modelo_selecionado = request.GET.get('modelo', tipo)

    proposta = get_object_or_404(Proposta, id=proposta_id, oportunidade=oportunidade) if proposta_id else oportunidade.proposta_set.last()

    try:
        items_list = proposta.itens.all()
    except AttributeError:
        items_list = proposta.itemproposta_set.all()

    now = datetime.datetime.now()
    
    context = {
        'opportunity': oportunidade, 
        'proposal': proposta, 
        'items': items_list,
        'user': request.user, 
        'generation_time': now,
    }

    if modelo_selecionado == 'simples':
        template = 'crm/proposta_simples.html'
    elif modelo_selecionado == 'resumo':
        template = 'crm/proposta_resumo.html'
    else:
        template = 'crm/proposta_completa.html'

    html_string = render_to_string(template, context)
    response = HttpResponse(content_type='application/pdf')
    
    # CORREÇÃO: Usando proposal.id_proposta para nomear o arquivo baixado
    filename = f"Proposta_{proposta.id_proposta}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response

def proposta_comparativo_pdf_view(request, oport_id):
    """Necessária para a URL 'proposta_comparativo_pdf'"""
    oportunidade = get_object_or_404(Oportunidade, pk=oport_id)
    propostas = oportunidade.proposta_set.all()
    context = {'opportunity': oportunidade, 'proposals': propostas, 'generation_time': datetime.datetime.now(), 'user': request.user}
    html_string = render_to_string('crm/proposal_comparison_pdf.html', context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="comparativo_propostas.pdf"'
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response

class AtividadeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'tc_crm.add_atividade'
    model = Atividade
    form_class = AtividadeForm
    template_name = 'crm/partials/atividade_form_modal.html'

    def form_valid(self, form):
        oportunidade = get_object_or_404(Oportunidade, pk=self.kwargs['oportunidade_pk'])
        form.instance.oportunidade = oportunidade
        form.instance.cliente = oportunidade.cliente
        form.instance.responsavel = self.request.user
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class AtividadeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'tc_crm.change_atividade'
    model = Atividade
    form_class = AtividadeForm
    template_name = 'crm/partials/atividade_form_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

@login_required
def fornecedor_modal_create(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save()
            # O script abaixo fecha a modal secundária e injeta o novo fornecedor no select
            return HttpResponse(f'''
                <script>
                    $("#secondary-modal").modal("hide");
                    let newOption = new Option("{fornecedor.razao_social}", "{fornecedor.id}", true, true);
                    $("#id_fornecedor").append(newOption).trigger("change");
                </script>
            ''')
    else:
        form = FornecedorForm()
    
    # MUDANÇA AQUI: Apontando para a pasta financeiro
    return render(request, 'financeiro/partials/fornecedor_rapido_modal.html', {'form': form})

def atualizar_etapa(request):
    opportunity_id = request.POST.get('opportunity_id')
    new_etapa_id = request.POST.get('new_etapa_id')
    oportunidade = get_object_or_404(Oportunidade, pk=opportunity_id)
    etapa = get_object_or_404(EtapaVenda, pk=new_etapa_id)
    
    oportunidade.etapa = etapa
    oportunidade.save()

    # Se a etapa for marcada como "Etapa Ganha" no banco de dados
    if etapa.e_etapa_ganha:
        response = HttpResponse(status=204)
        response['HX-Trigger'] = f'abrirFechamento-{oportunidade.id}'
        return response
    
    return HttpResponse(status=204)


        
# ############################################################################
# PDASHBOARD CRM
# ############################################################################

@login_required
def dashboard_vendas_view(request):
    import json
    import locale
    from decimal import Decimal
    from django.db.models import Sum, Q
    from django.utils import timezone
    from tc_core.models import Usuario
    from .models import Oportunidade, MetaMensal, Cliente

    # Configuração de idioma para meses em Português
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
        except:
            pass # Caso o servidor não tenha o pacote de idiomas

    hoje = timezone.now()
    mes_atual = hoje.month
    ano_atual = hoje.year
    user = request.user
    is_gestor = user.is_superuser or user.departamento in ['diretoria', 'financeiro']

    # Lógica de Mês Anterior para Comparativo
    data_mes_anterior = hoje.replace(day=1) - timezone.timedelta(days=1)
    mes_ant = data_mes_anterior.month
    ano_ant = data_mes_anterior.year

    # --- 1. LÓGICA DO GRÁFICO E PERFORMANCE ---
    vendedores_performance = Usuario.objects.filter(
        departamento='comercial', is_active=True
    ).annotate(
        realizado_mes=Sum(
            'oportunidade__valor_estimado',
            filter=Q(
                oportunidade__etapa__e_etapa_ganha=True,
                oportunidade__data_fechamento_real__month=mes_atual,
                oportunidade__data_fechamento_real__year=ano_atual
            )
        )
    )

    labels, dados_meta, dados_realizado = [], [], []
    for v in vendedores_performance:
        labels.append(v.get_full_name() or v.username)
        meta_v = MetaMensal.objects.filter(vendedor=v, mes=mes_atual, ano=ano_atual).first()
        dados_meta.append(float(meta_v.valor_objetivo) if meta_v else 0.0)
        dados_realizado.append(float(v.realizado_mes) if v.realizado_mes else 0.0)

    # --- 2. TOTAIS E COMPARATIVO ---
    realizado_anterior = Decimal('0.00')
    if is_gestor:
        meta_global = MetaMensal.objects.filter(vendedor__isnull=True, mes=mes_atual, ano=ano_atual).first()
        valor_meta_topo = meta_global.valor_objetivo if meta_global else Decimal('0.00')
        valor_realizado_topo = sum(dados_realizado)
        realizado_anterior = Oportunidade.objects.filter(
            etapa__e_etapa_ganha=True, 
            data_fechamento_real__month=mes_ant,
            data_fechamento_real__year=ano_ant
        ).aggregate(total=Sum('valor_estimado'))['total'] or Decimal('0.00')
    else:
        try:
            idx = labels.index(user.get_full_name() or user.username)
            valor_meta_topo = Decimal(dados_meta[idx])
            valor_realizado_topo = Decimal(dados_realizado[idx])
        except (ValueError, IndexError):
            valor_meta_topo = Decimal('0.00')
            valor_realizado_topo = Decimal('0.00')
        
        realizado_anterior = Oportunidade.objects.filter(
            responsavel=user,
            etapa__e_etapa_ganha=True, 
            data_fechamento_real__month=mes_ant,
            data_fechamento_real__year=ano_ant
        ).aggregate(total=Sum('valor_estimado'))['total'] or Decimal('0.00')

    porcentagem = float(round((Decimal(valor_realizado_topo) / valor_meta_topo) * 100, 1)) if valor_meta_topo > 0 else 0
    crescimento_vs_anterior = 0
    if realizado_anterior > 0:
        crescimento_vs_anterior = float(round(((Decimal(valor_realizado_topo) - realizado_anterior) / realizado_anterior) * 100, 1))

    # --- 3. CONTAGEM PARA OS 6 CARDS (Novo pedido) ---
    opts_usuario = Oportunidade.objects.filter(responsavel=user)

    # Abertas: Não ganhas nem perdidas
    abertas = opts_usuario.exclude(etapa__e_etapa_ganha=True).exclude(etapa__nome__icontains='Perdida')
    qtd_abertas = abertas.count()
    vol_abertas = abertas.aggregate(total=Sum('valor_estimado'))['total'] or Decimal('0.00')

    # Fechadas (Ganhas) no mês
    fechadas = opts_usuario.filter(etapa__e_etapa_ganha=True, data_fechamento_real__month=mes_atual, data_fechamento_real__year=ano_atual)
    qtd_fechadas = fechadas.count()
    vol_fechadas = fechadas.aggregate(total=Sum('valor_estimado'))['total'] or Decimal('0.00')

    # Perdidas no mês
    perdidas = opts_usuario.filter(etapa__nome__icontains='Perdida', data_fechamento_real__month=mes_atual, data_fechamento_real__year=ano_atual)
    qtd_perdidas = perdidas.count()
    vol_perdidas = perdidas.aggregate(total=Sum('valor_estimado'))['total'] or Decimal('0.00')

    # Clientes
    qtd_clientes_total = Cliente.objects.count()
    qtd_clientes_meus = Cliente.objects.filter(oportunidade__responsavel=user).distinct().count()
    qtd_opts_total = Oportunidade.objects.exclude(etapa__e_etapa_ganha=True).exclude(etapa__nome__icontains='Perdida').count()

    # --- 4. MONTAGEM FINAL DO CONTEXTO ---
    context = {
        'is_gestor': is_gestor,
        'valor_meta': valor_meta_topo,
        'valor_realizado': valor_realizado_topo,
        'valor_realizado_anterior': realizado_anterior,
        'crescimento_vs_anterior': crescimento_vs_anterior,
        'porcentagem_meta': porcentagem,
        'mes_atual': hoje.strftime('%B').capitalize(),
        'grafico_labels': json.dumps(labels),
        'grafico_meta': json.dumps(dados_meta),
        'grafico_realizado': json.dumps(dados_realizado),
        'ranking_vendedores': vendedores_performance.order_by('-realizado_mes')[:5] if is_gestor else [],
        
        # Variáveis dos Cards
        'qtd_abertas': qtd_abertas, 'vol_abertas': vol_abertas,
        'qtd_fechadas': qtd_fechadas, 'vol_fechadas': vol_fechadas,
        'qtd_perdidas': qtd_perdidas, 'vol_perdidas': vol_perdidas,
        'qtd_clientes_total': qtd_clientes_total,
        'qtd_clientes_meus': qtd_clientes_meus,
        'qtd_opts_total': qtd_opts_total,
    }

    return render(request, 'crm/dashboard_vendas.html', context)