# tc_contratos/views.py

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from tc_core.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.views.generic import ListView
#from .models import Oportunidade

from tc_crm.models import Oportunidade
from .models import Contrato
from .forms import ContratoForm 

class ContratoListView(LoginRequiredMixin, ListView):
    model = Contrato
    template_name = 'contratos/contrato_list.html'
    context_object_name = 'contratos'
    ordering = ['-criado_em']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros de URL
        q = self.request.GET.get('q')
        tipo = self.request.GET.get('tipo')
        situacao = self.request.GET.get('situacao')
        renovando = self.request.GET.get('renovando')

        if q:
            queryset = queryset.filter(
                Q(numero_contrato__icontains=q) |
                Q(cliente__razao_social__icontains=q) |
                Q(fornecedor__razao_social__icontains=q) |
                Q(objeto_contrato__icontains=q)
            ).distinct()

        if tipo:
            queryset = queryset.filter(tipo_contrato=tipo)
        
        if situacao:
            queryset = queryset.filter(situacao=situacao)

        if renovando == '1':
            hoje = timezone.now().date()
            queryset = queryset.filter(
                data_proxima_renovacao__month=hoje.month,
                data_proxima_renovacao__year=hoje.year
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.now().date()
        proximos_30_dias = hoje + timedelta(days=30)

        # Dashboard
        context['total_receita'] = Contrato.objects.filter(
            tipo_contrato='REC', 
            situacao='ATIVO'
        ).aggregate(Sum('valor_mensal'))['valor_mensal__sum'] or 0

        context['alerta_renovacao'] = Contrato.objects.filter(
            data_proxima_renovacao__range=[hoje, proximos_30_dias]
        ).count()

        context['em_elaboracao'] = Contrato.objects.filter(
            situacao='ELABORACAO'
        ).count()

        context['filtros'] = {
            'q': self.request.GET.get('q', ''),
            'tipo': self.request.GET.get('tipo', ''),
            'situacao': self.request.GET.get('situacao', ''),
            'renovando': self.request.GET.get('renovando', ''),
        }
        return context

class ContratoDetailView(LoginRequiredMixin, DetailView):
    model = Contrato
    template_name = 'contratos/contrato_detail.html'
    context_object_name = 'contrato'

class ContratoCreateView(LoginRequiredMixin, CreateView):
    model = Contrato
    form_class = ContratoForm
    template_name = 'contratos/partials/contrato_form_modal.html'

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        self.object = form.save()
        return HttpResponse(status=204, headers={'HX-Refresh': 'true'})

class ContratoUpdateView(LoginRequiredMixin, UpdateView):
    model = Contrato
    form_class = ContratoForm
    template_name = 'contratos/partials/contrato_form_modal.html'

    def form_valid(self, form):
        form.instance.modificado_por = self.request.user
        self.object = form.save()
        return HttpResponse(status=204, headers={'HX-Refresh': 'true'})

# --- FUNÇÕES AJAX - Traz as Oportundiades Fechadas do Tipo Contrato ---

def carregar_oportunidades_disponiveis(request):
    cliente_id = request.GET.get('cliente')
    
    if not cliente_id:
        return HttpResponse('<option value="">Selecione o cliente...</option>')
    
    # Filtra oportunidades ganhas do cliente que ainda não possuem contrato
    oportunidades = Oportunidade.objects.filter(
        cliente_id=cliente_id,
        tipo_oportunidade='contrato',
        contrato_vinculado__isnull=True
    ).filter(
        Q(etapa__e_etapa_ganha=True) | Q(etapa__nome__icontains='Fechamento')
    ).distinct()
    
    # AJUSTE AQUI: Caminho atualizado conforme sua estrutura
    return render(request, 'contratos/partials/oportunidade_options.html', {
        'oportunidades': oportunidades
    })

def obter_valor_proposta(request):
    oportunidade_id = request.GET.get('oportunidade')
    valor = "0.00"
    if oportunidade_id and oportunidade_id.isdigit():
        opt = Oportunidade.objects.filter(id=oportunidade_id).first()
        if opt:
            proposta = opt.proposta_set.filter(status__icontains='Ganha').first()
            if not proposta:
                proposta = opt.proposta_set.order_by('-data_criacao').first()
            if proposta and proposta.receita_mensal:
                valor = "{:.2f}".format(float(proposta.receita_mensal))
    return HttpResponse(valor)

def calcular_renovacao(request):
    data_inicio_str = request.GET.get('data_inicio')
    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            data_renovacao = data_inicio + relativedelta(years=1)
            data_termino = data_renovacao - timedelta(days=1)
            return JsonResponse({
                'data_renovacao': data_renovacao.strftime('%Y-%m-%d'),
                'data_termino': data_termino.strftime('%Y-%m-%d'),
            })
        except (ValueError, TypeError):
            pass
    return JsonResponse({'error': 'Data inválida'}, status=400)

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
        
        # Pipeline Total (Soma o valor_estimado)
        context['pipeline_total'] = Oportunidade.objects.exclude(
            etapa__e_etapa_ganha=True
        ).exclude(
            etapa__nome__icontains='Perdida'
        ).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0

        # Ganhos no Mês
        context['total_ganho_mes'] = Oportunidade.objects.filter(
            etapa__e_etapa_ganha=True,
            data_fechamento_real__month=hoje.month,
            data_fechamento_real__year=hoje.year
        ).aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0

        # Quantidade de Negócios Ativos
        context['qtd_oportunidades'] = Oportunidade.objects.exclude(
            etapa__e_etapa_ganha=True
        ).exclude(
            etapa__nome__icontains='Perdida'
        ).count()

        return context