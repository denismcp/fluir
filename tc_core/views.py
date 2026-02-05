from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.apps import apps
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from tc_crm.models import Oportunidade, Proposta, Atividade, Cliente
from tc_contratos.models import Contrato
from datetime import timedelta


# Imports para Novos Cadastros de Usuários
from django.contrib.auth import get_user_model
from django import forms

# IMPORTAÇÃO CORRIGIDA PARA O NOVO NOME DO APP:
from tc_core.mixins import PermissionRequiredMixin 
from .models import Usuario, Regra
from tc_crm.models import Oportunidade, MetaMensal, EtapaVenda

logger = logging.getLogger(__name__)

# ############################################################################
# VIEWS DE AUTENTICAÇÃO (Login e Logout)
# ############################################################################

class LoginView(DjangoLoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context

class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy('tc_core:login') # Ajustado para tc_core

# ############################################################################
# VIEWS DE NAVEGAÇÃO E PRINCIPAIS
# ############################################################################

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        hoje = now.date()

        # 1. KPIs FINANCEIROS
        pipeline_query = Oportunidade.objects.exclude(etapa__nome__icontains='Ganho').exclude(etapa__nome__icontains='Perdido')
        context['total_pipeline'] = pipeline_query.aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
        
        contratos_ativos = Contrato.objects.filter(situacao='ATIVO')
        context['total_mrr'] = sum(c.valor_mensal for c in contratos_ativos)
        context['qtd_propostas_abertas'] = Proposta.objects.filter(status='elaboracao').count()
        
        limite_renovacao = hoje + timedelta(days=60)
        context['qtd_renovacoes'] = Contrato.objects.filter(situacao='ATIVO', data_fim__lte=limite_renovacao).count()

        # 2. NOVOS CADASTROS
        context['clientes_30_dias'] = Cliente.objects.count()
        
        try:
            context['oportunidades_7_dias'] = Oportunidade.objects.filter(id__gte=0).count()
        except:
            context['oportunidades_7_dias'] = 0

        # 3. PREVISÃO DE FECHAMENTO (TEMPORAL)
        opts_vendas = Oportunidade.objects.exclude(etapa__nome__icontains='Ganho').exclude(etapa__nome__icontains='Perdido')
        
        fim_semana = hoje + timedelta(days=(6 - hoje.weekday()))
        prox_semana_ini = fim_semana + timedelta(days=1)
        prox_semana_fim = prox_semana_ini + timedelta(days=6)
        
        context['fechamento_semana'] = opts_vendas.filter(data_fechamento_prevista__range=[hoje, fim_semana]).count()
        context['fechamento_prox_semana'] = opts_vendas.filter(data_fechamento_prevista__range=[prox_semana_ini, prox_semana_fim]).count()
        context['fechamento_mes'] = opts_vendas.filter(data_fechamento_prevista__month=hoje.month, data_fechamento_prevista__year=hoje.year).count()
        
        prox_mes = hoje.month + 1 if hoje.month < 12 else 1
        ano_prox_mes = hoje.year if hoje.month < 12 else hoje.year + 1
        context['fechamento_prox_mes'] = opts_vendas.filter(data_fechamento_prevista__month=prox_mes, data_fechamento_prevista__year=ano_prox_mes).count()
        
        context['fechamento_trimestre'] = opts_vendas.filter(data_fechamento_prevista__range=[hoje, hoje + timedelta(days=90)]).count()
        context['fechamento_semestre'] = opts_vendas.filter(data_fechamento_prevista__range=[hoje, hoje + timedelta(days=180)]).count()

        # 4. TIMELINE E CRÍTICOS
        context['ultimas_atividades'] = Atividade.objects.select_related('oportunidade').order_by('-data_hora')[:5]
        context['oportunidades_criticas'] = opts_vendas.order_by('data_fechamento_prevista')[:5]
        
        context['now'] = now
        return context

@login_required
def dashboard_vendas_view(request):
    import json
    from decimal import Decimal
    from django.db.models import Sum
    from django.utils import timezone
    from tc_crm.models import Oportunidade, MetaMensal
    from .models import Usuario

    hoje = timezone.now()
    
    # 1. Ranking e Performance Individual
    vendedores_performance = Usuario.objects.filter(
        departamento='comercial', 
        is_active=True
    ).annotate(
        total_realizado=Sum(
            'oportunidade__valor_estimado',
            filter=Q(
                oportunidade__etapa__e_etapa_ganha=True,
                oportunidade__data_fechamento_real__month=hoje.month,
                oportunidade__data_fechamento_real__year=hoje.year
            )
        )
    )

    labels = []
    dados_meta = []
    dados_realizado = []

    for v in vendedores_performance:
        labels.append(v.get_full_name() or v.username)
        
        # Busca a meta do vendedor para o mês atual
        meta_v = MetaMensal.objects.filter(
            vendedor=v, 
            mes=hoje.month, 
            ano=hoje.year
        ).first()
        
        val_meta = float(meta_v.valor_objetivo) if meta_v else 0.0
        val_realizado = float(v.total_realizado) if v.total_realizado else 0.0
        
        dados_meta.append(val_meta)
        dados_realizado.append(val_realizado)

    context = {
        'mes_atual': hoje.strftime('%B').capitalize(),
        'grafico_labels': json.dumps(labels),
        'grafico_meta': json.dumps(dados_meta),
        'grafico_realizado': json.dumps(dados_realizado),
        # ... manter as outras variáveis (is_gestor, ranking, etc)
    }
    return render(request, 'core/dashboard_vendas.html', context)

class UserProfileView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'tc_core.view_usuario' 
    template_name = 'core/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Meu Perfil'
        return context

@login_required
def search_results_view(request):
    query = request.GET.get('q', '').strip()
    resultados = []

    if len(query) >= 3:
        try:
            ClienteModel = apps.get_model('tc_crm', 'Cliente')
            clientes = ClienteModel.objects.filter(
                Q(razao_social__icontains=query) | Q(cnpj_cpf__icontains=query)
            )[:5]
        except LookupError:
            clientes = []

        try:
            ChamadoModel = apps.get_model('tc_operacoes', 'Chamado')
            chamados = ChamadoModel.objects.filter(
                Q(assunto__icontains=query) | Q(descricao_incidente__icontains=query)
            )[:5]
        except LookupError:
            chamados = []
        
        try:
            PedidoCompraModel = apps.get_model('tc_compras', 'PedidoCompra')
            pedidos = PedidoCompraModel.objects.filter(
                Q(pk__icontains=query)
            )[:5]
        except LookupError:
            pedidos = []

        if clientes:
            resultados.append({'tipo': 'Clientes', 'itens': clientes})
        if chamados:
            resultados.append({'tipo': 'Chamados ITSM', 'itens': chamados})
        if pedidos:
            resultados.append({'tipo': 'Pedidos de Compra', 'itens': pedidos})

    return render(request, 'partials/search_dropdown.html', {'resultados': resultados, 'query': query})

# ############################################################################
# GESTÃO DE USUÁRIOS E VENDEDORES (ADMINISTRAÇÃO GLOBAL)
# ############################################################################

User = get_user_model()

class UsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha", required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirmar Senha", required=False)

    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'username', 'email', 
            'departamento', 'regra', 'taxa_comissao', 'is_active', 
            'indice_vendedor'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and password != confirm_password:
            raise forms.ValidationError("As senhas não coincidem.")
        return cleaned_data

@login_required
def usuario_create_view(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            
            # Lógica para salvar a Meta Mensal se fornecida
            meta_valor = request.POST.get('meta_mensal_valor')
            if meta_valor and user.departamento == 'comercial':
                # Limpa a formatação de moeda se houver e converte para Decimal
                valor = Decimal(meta_valor.replace('R$', '').replace('.', '').replace(',', '.').strip())
                from django.utils import timezone
                hoje = timezone.now()
                MetaMensal.objects.update_or_create(
                    vendedor=user,
                    mes=hoje.month,
                    ano=hoje.year,
                    defaults={'valor_objetivo': valor}
                )
                
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = UsuarioForm()
    return render(request, 'core/partials/usuario_form_modal.html', {'form': form})

@login_required
def usuario_list_view(request):
    """ View para listagem global de usuários na Administração """
    usuarios = User.objects.all().select_related('regra').order_by('first_name')
    return render(request, 'core/usuario_list.html', {'usuarios': usuarios})

# ############################################################################
# GESTÃO DE REGRAS (PAPÉIS)
# ############################################################################

class RegraForm(forms.ModelForm):
    class Meta:
        model = Regra
        fields = ['nome', 'descricao', 'permissoes']
        widgets = {
            'permissoes': forms.SelectMultiple(attrs={'class': 'select2-premium'}),
        }

@login_required
def regra_list_view(request):
    """ Listagem de Regras/Papéis do Sistema """
    regras = Regra.objects.all().annotate(total_usuarios=models.Count('usuario'))
    return render(request, 'core/regra_list.html', {'regras': regras})

# No tc_core/views.py, altere a função regra_create_view:
@login_required
def regra_create_view(request):
    from django.contrib.auth.models import Permission
    
    if request.method == 'POST':
        form = RegraForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = RegraForm()

    # Buscamos as permissões e já limpamos o nome do módulo para exibição
    permissoes_raw = Permission.objects.filter(
        content_type__app_label__startswith='tc_'
    ).select_related('content_type')
    
    # Criamos uma lista de dicionários com nomes amigáveis
    permissoes_erp = []
    for p in permissoes_raw:
        permissoes_erp.append({
            'id': p.id,
            'name': p.name,
            'model': p.content_type.model.upper(),
            'app_label': p.content_type.app_label,
            'app_nome_limpo': p.content_type.app_label.replace('tc_', '').upper()
        })
    
    return render(request, 'core/partials/regra_form_modal.html', {
        'form': form,
        'permissoes_erp': permissoes_erp
    })

@login_required
def ajuda_acessos_view(request):
    """ Retorna o conteúdo educativo sobre Gestão de Acessos """
    return render(request, 'core/partials/ajuda_acessos_modal.html')

@login_required
def usuario_update_view(request, pk):
    user = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            
            # Atualiza a meta caso o campo na modal tenha sido preenchido
            meta_valor = request.POST.get('meta_mensal_valor')
            if meta_valor and user.departamento == 'comercial':
                try:
                    valor = Decimal(meta_valor.replace('R$', '').replace('.', '').replace(',', '.').strip())
                    from django.utils import timezone
                    hoje = timezone.now()
                    MetaMensal.objects.update_or_create(
                        vendedor=user,
                        mes=hoje.month,
                        ano=hoje.year,
                        defaults={'valor_objetivo': valor}
                    )
                except:
                    pass
                    
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = UsuarioForm(instance=user)
    return render(request, 'core/partials/usuario_form_modal.html', {'form': form})

@login_required
def regra_update_view(request, pk):
    from django.contrib.auth.models import Permission
    regra = get_object_or_404(Regra, pk=pk)
    
    if request.method == 'POST':
        form = RegraForm(request.POST, instance=regra)
        if form.is_valid():
            form.save()
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = RegraForm(instance=regra)

    # Capturamos os IDs das permissões que esta regra JÁ POSSUI
    permissoes_atuais_ids = list(regra.permissoes.values_list('id', flat=True))

    permissoes_raw = Permission.objects.filter(
        content_type__app_label__startswith='tc_'
    ).select_related('content_type')
    
    permissoes_erp = []
    for p in permissoes_raw:
        permissoes_erp.append({
            'id': p.id,
            'name': p.name,
            'model': p.content_type.model.upper(),
            'app_label': p.content_type.app_label,
            'app_nome_limpo': p.content_type.app_label.replace('tc_', '').upper(),
            # Marcamos se a permissão está na lista da regra
            'is_selected': p.id in permissoes_atuais_ids 
        })
    
    return render(request, 'core/partials/regra_form_modal.html', {
        'form': form,
        'permissoes_erp': permissoes_erp,
        'permissoes_atuais_ids': permissoes_atuais_ids
    })

# ############################################################################
# GESTÃO DE METAS GLOBAIS E POR VENDEDOR
# ############################################################################

class MetaForm(forms.ModelForm):
    class Meta:
        model = MetaMensal
        fields = ['vendedor', 'ano', 'mes', 'valor_objetivo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FILTRO INTELIGENTE: Só exibe usuários do departamento Comercial
        self.fields['vendedor'].queryset = User.objects.filter(
            departamento='comercial', 
            is_active=True
        )

@login_required
def dashboard_view(request):
    hoje = timezone.now()
    user = request.user
    
    # Define se o usuário tem visão total (ADM/Diretoria) ou restrita (Vendedor)
    is_gestor = user.is_superuser or user.departamento in ['diretoria', 'financeiro']

    # --- 1. LÓGICA DO TERMÔMETRO ---
    if is_gestor:
        # Gestor vê a Meta Global da Empresa
        meta = MetaMensal.objects.filter(vendedor__isnull=True, mes=hoje.month, ano=hoje.year).first()
        # Gestor vê o faturamento de todos
        realizado = Oportunidade.objects.filter(
            etapa__e_etapa_ganha=True,
            data_fechamento_real__month=hoje.month
        ).aggregate(total=Sum('valor_estimado'))['total'] or Decimal('0.00')
    else:
        # Vendedor vê apenas a SUA meta individual
        meta = MetaMensal.objects.filter(vendedor=user, mes=hoje.month, ano=hoje.year).first()
        # Vendedor vê apenas o SEU faturamento realizado
        realizado = Oportunidade.objects.filter(
            responsavel=user,
            etapa__e_etapa_ganha=True,
            data_fechamento_real__month=hoje.month
        ).aggregate(total=Sum('valor_estimado'))['total'] or Decimal('0.00')

    valor_meta = meta.valor_objetivo if meta else Decimal('0.00')
    porcentagem = float(round((realizado / valor_meta) * 100, 1)) if valor_meta > 0 else 0

    # --- 2. LÓGICA DO RANKING (Visível apenas para Gestores ou opcional para todos) ---
    ranking_vendedores = []
    if is_gestor:
        ranking_vendedores = Usuario.objects.filter(
            departamento='comercial',
            is_active=True,
            oportunidade__etapa__e_etapa_ganha=True,
            oportunidade__data_fechamento_real__month=hoje.month
        ).annotate(total_vendido=Sum('oportunidade__valor_estimado')).order_by('-total_vendido')[:5]

    context = {
        'valor_meta': valor_meta,
        'valor_realizado': realizado,
        'porcentagem_meta': porcentagem,
        'ranking_vendedores': ranking_vendedores,
        'is_gestor': is_gestor, # Passamos para o template decidir o que mostrar
        'mes_atual': hoje.strftime('%B').capitalize(),
    }
    
    return render(request, 'core/dashboard_vendas.html', context)

@login_required
def meta_list_view(request):
    """ Listagem de Metas Mensais """
    metas = MetaMensal.objects.all().order_by('-ano', '-mes', 'vendedor')
    return render(request, 'core/meta_list.html', {'metas': metas})

@login_required
def meta_create_view(request):
    """ Cadastro de nova Meta via HTMX """
    if request.method == 'POST':
        form = MetaForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = MetaForm()
    return render(request, 'core/partials/meta_form_modal.html', {'form': form})

@login_required
def meta_update_view(request, pk):
    """ Edição de meta existente via Modal/HTMX """
    meta = get_object_or_404(MetaMensal, pk=pk)
    if request.method == 'POST':
        form = MetaForm(request.POST, instance=meta)
        if form.is_valid():
            form.save()
            return HttpResponse('<script>window.location.reload();</script>')
    else:
        form = MetaForm(instance=meta)
    return render(request, 'core/partials/meta_form_modal.html', {'form': form})

@login_required
def meta_delete_view(request, pk):
    """ Exclusão de meta com confirmação HTMX """
    meta = get_object_or_404(MetaMensal, pk=pk)
    if request.method == 'POST':
        meta.delete()
        return HttpResponse('<script>window.location.reload();</script>')
    
    # Retorna uma modal simples de confirmação
    return render(request, 'core/partials/confirm_delete_modal.html', {
        'objeto': meta,
        'mensagem': f"Deseja realmente excluir a meta de {meta.get_mes_display()}/{meta.ano}?"
    })