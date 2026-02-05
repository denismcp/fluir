import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from datetime import timedelta
from decimal import Decimal

from .models import Fatura, Despesa, MetaVenda
from .forms import FaturaForm, DespesaForm, ContratoForm
from .services import XMLInvoiceService
from tc_contratos.models import Contrato

class FinancialDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'financeiro/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.now().date()
        
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')

        if not data_inicio or not data_fim:
            data_inicio = hoje.replace(day=1)
            data_fim = (data_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            data_inicio = timezone.datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = timezone.datetime.strptime(data_fim, '%Y-%m-%d').date()

        context['data_inicio'] = data_inicio.strftime('%Y-%m-%d')
        context['data_fim'] = data_fim.strftime('%Y-%m-%d')

        # KPIs Corrigidos: Somando valor_saldo do novo models.py
        context['total_receber'] = Fatura.objects.filter(
            data_vencimento__range=[data_inicio, data_fim]
        ).exclude(status='pago').aggregate(total=Sum('valor_saldo'))['total'] or 0

        context['total_pagar'] = Despesa.objects.filter(
            data_vencimento__range=[data_inicio, data_fim]
        ).exclude(status='pago').aggregate(total=Sum('valor_saldo'))['total'] or 0

        context['total_vencido'] = Fatura.objects.filter(
            status='atrasado'
        ).aggregate(total=Sum('valor_saldo'))['total'] or 0
        
        context['saldo_liquido'] = context['total_receber'] - context['total_pagar']

        # Gráficos de Fluxo
        labels_fluxo, receitas_data, despesas_data = [], [], []
        meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        for i in range(5, -1, -1):
            data_alvo = hoje - timedelta(days=i*30)
            mes_ref = data_alvo.month
            labels_fluxo.append(meses_nomes[mes_ref - 1])
            rec = Fatura.objects.filter(data_competencia__month=mes_ref, data_competencia__year=data_alvo.year).aggregate(s=Sum('valor_original'))['s'] or 0
            desp = Despesa.objects.filter(data_competencia__month=mes_ref, data_competencia__year=data_alvo.year).aggregate(s=Sum('valor_original'))['s'] or 0
            receitas_data.append(float(rec))
            despesas_data.append(float(desp))

        context['chart_labels'] = json.dumps(labels_fluxo)
        context['chart_receitas'] = json.dumps(receitas_data)
        context['chart_despesas'] = json.dumps(despesas_data)

        # Mapeamento do Donut para Tipo de Título do novo models.py
        dados_tipo = Despesa.objects.filter(data_vencimento__range=[data_inicio, data_fim]).values('tipo_titulo').annotate(total=Sum('valor_original'))
        context['donut_labels'] = json.dumps([item['tipo_titulo'] or 'Outros' for item in dados_tipo])
        context['donut_data'] = json.dumps([float(item['total']) for item in dados_tipo])

        context['receitas_7_dias'] = Fatura.objects.filter(data_vencimento__range=[hoje, hoje + timedelta(days=7)]).exclude(status='pago').order_by('data_vencimento')[:5]
        context['despesas_7_dias'] = Despesa.objects.filter(data_vencimento__range=[hoje, hoje + timedelta(days=7)]).exclude(status='pago').order_by('data_vencimento')[:5]
        context['hoje'] = hoje
        return context

# --- FATURAS ---

@login_required
def fatura_receber_agora(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    # Liquida o valor_total calculado no save() do modelo
    fatura.valor_pago = fatura.valor_total
    fatura.data_liquidacao = timezone.now().date()
    fatura.save()
    response = render(request, 'financeiro/partials/fatura_sidebar_detail.html', {'fatura': fatura})
    response['HX-Trigger'] = 'faturaAtualizada'
    return response

class FaturaListView(LoginRequiredMixin, ListView):
    model = Fatura
    template_name = 'financeiro/fatura_list.html'
    context_object_name = 'faturas'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('data_vencimento')
        hoje = timezone.now().date()
        
        # Filtro de busca textual
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(numero_documento__icontains=q) | Q(cliente__razao_social__icontains=q) | Q(cliente__nome_fantasia__icontains=q))
        
        # FILTRO POR CARD (KPI)
        f = self.request.GET.get('f')
        if f == 'hoje':
            queryset = queryset.filter(data_vencimento=hoje).exclude(status='pago')
        elif f == 'atrasado':
            queryset = queryset.filter(status='atrasado')
        elif f == 'pago':
            queryset = queryset.filter(status='pago', data_liquidacao__month=hoje.month)
            
        return queryset

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            hoje = timezone.now().date()
            
            # KPIs usando valor_original como referência de "valor da conta"
            context['total_receber'] = Fatura.objects.exclude(status='pago').aggregate(
                total=Sum('valor_original'))['total'] or 0
                
            context['total_recebido_mes'] = Fatura.objects.filter(
                status='pago', 
                data_liquidacao__month=hoje.month
            ).aggregate(total=Sum('valor_original'))['total'] or 0
            
            context['total_vencido'] = Fatura.objects.filter(
                status='atrasado'
            ).aggregate(total=Sum('valor_original'))['total'] or 0
            
            context['total_hoje'] = Fatura.objects.filter(
                data_vencimento=hoje
            ).exclude(status='pago').aggregate(total=Sum('valor_original'))['total'] or 0
            
            return context

class FaturaCreateView(LoginRequiredMixin, CreateView):
    model = Fatura
    form_class = FaturaForm
    template_name = 'financeiro/fatura_form.html'
    
    def form_valid(self, form):
        # 1. Atribui o usuário logado
        form.instance.criado_por = self.request.user
        
        # 2. Garante a competência se estiver vazia
        if not form.instance.data_competencia:
            form.instance.data_competencia = timezone.now().date()
        
        # 3. Salva o objeto (Gera o número 2026-0000X)
        self.object = form.save()
        
        # --- ALTERAÇÃO CRÍTICA AQUI ---
        if self.request.headers.get('HX-Request'):
            # Retornamos o 204 mas avisamos ao Front-end para fechar e atualizar
            response = HttpResponse(status=204)
            response['HX-Trigger'] = 'faturaAtualizada' # Este gatilho limpa a tela
            return response
        
        return redirect('financeiro:fatura_list')

class FaturaUpdateView(LoginRequiredMixin, UpdateView):
    model = Fatura
    form_class = FaturaForm
    template_name = 'financeiro/fatura_form.html'

    def form_valid(self, form):
        form.instance.alterado_por = self.request.user
        self.object = form.save()
        if self.request.headers.get('HX-Request'):
            # Retornar 204 faz o script da base.html fechar o modal automaticamente
            response = HttpResponse(status=204)
            response['HX-Trigger'] = 'faturaAtualizada'
            return response
        return redirect('financeiro:fatura_list')

class FaturaDetailView(LoginRequiredMixin, DetailView):
    model = Fatura
    def get_template_names(self):
        if self.request.GET.get('layout') == 'sidebar':
            return ['financeiro/partials/fatura_sidebar_detail.html']
        return ['financeiro/fatura_detail.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hoje'] = timezone.now().date()
        return context

class FaturaPlanilhaView(LoginRequiredMixin, ListView):
    model = Fatura
    template_name = 'financeiro/partials/fatura_planilha.html'
    context_object_name = 'faturas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from tc_crm.models import Cliente
        context['clientes'] = Cliente.objects.all().order_by('razao_social')
        return context

    def post(self, request, *args, **kwargs):
        clientes, numeros, vencimentos, valores = request.POST.getlist('cliente[]'), request.POST.getlist('numero[]'), request.POST.getlist('vencimento[]'), request.POST.getlist('valor[]')
        for i in range(len(clientes)):
            if clientes[i] and valores[i] and vencimentos[i]:
                Fatura.objects.create(
                    cliente_id=clientes[i], numero_documento=numeros[i],
                    data_vencimento=timezone.datetime.strptime(vencimentos[i], '%Y-%m-%d').date(),
                    data_competencia=timezone.now().date(),
                    valor_original=Decimal(valores[i].replace(',', '.')),
                    criado_por=request.user, origem="IMPORTACAO"
                )
        return redirect('financeiro:fatura_list')

@login_required
def fatura_confirm_liquidar(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    return render(request, 'financeiro/partials/fatura_confirm_liquidar.html', {'fatura': fatura})
# --- DESPESAS ---

class DespesaListView(LoginRequiredMixin, ListView):
    model = Despesa
    template_name = 'financeiro/despesa_list.html'
    context_object_name = 'despesas'

    def get_queryset(self):
        return Despesa.objects.all().order_by('-data_vencimento')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.localtime(timezone.now()).date()
        context['hoje'] = hoje
        amanha = hoje + timedelta(days=1)
        set7_dias = hoje + timedelta(days=7)

        # Base: Apenas o que NÃO foi pago e NÃO foi cancelado
        # Usamos o campo 'pago' (Booleano) que é mais confiável que a string 'status'
        despesas_abertas = Despesa.objects.exclude(pago=True).exclude(status='cancelada')

        # 1. Vencendo Hoje (Filtro exato para hoje)
        vencendo_hoje = despesas_abertas.filter(data_vencimento=hoje)
        context['vencendo_hoje_valor'] = vencendo_hoje.aggregate(Sum('valor_original'))['valor_original__sum'] or Decimal('0.00')
        context['vencendo_hoje_qtd'] = vencendo_hoje.count()

        # 2. Vencidas (Atraso) - Tudo que venceu antes de hoje
        vencidas = despesas_abertas.filter(data_vencimento__lt=hoje)
        context['vencidas_valor'] = vencidas.aggregate(Sum('valor_original'))['valor_original__sum'] or Decimal('0.00')
        context['vencidas_qtd'] = vencidas.count()

        # 3. Próximos 7 Dias (Começa de AMANHÃ até daqui a 7 dias para não repetir o 'Hoje')
        prox_7 = despesas_abertas.filter(data_vencimento__range=[amanha, set7_dias])
        context['prox_7_valor'] = prox_7.aggregate(Sum('valor_original'))['valor_original__sum'] or Decimal('0.00')
        context['prox_7_qtd'] = prox_7.count()
        
        # 4. Total do Mês (Baseado no vencimento dentro do mês atual)
        mes_atual = despesas_abertas.filter(data_vencimento__month=hoje.month, data_vencimento__year=hoje.year)
        context['total_mes_valor'] = mes_atual.aggregate(Sum('valor_original'))['valor_original__sum'] or Decimal('0.00')

        return context

class DespesaCreateView(LoginRequiredMixin, CreateView):
    model = Despesa
    form_class = DespesaForm
    template_name = 'financeiro/partials/despesa_form_modal.html'
    
    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['financeiro/partials/despesa_form_modal.html'] 
        return ['financeiro/despesa_form.html']

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('HX-Request'):
            response = HttpResponse(status=204)
            response['HX-Trigger'] = 'despesaAtualizada'
            return response
        return super().form_valid(form)

class DespesaUpdateView(LoginRequiredMixin, UpdateView):
    model = Despesa
    form_class = DespesaForm
    template_name = 'financeiro/partials/despesa_form_modal.html'
    
    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['financeiro/partials/despesa_form_modal.html']
        return ['financeiro/despesa_form.html']

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('HX-Request'):
            response = HttpResponse(status=204)
            response['HX-Trigger'] = 'despesaAtualizada'
            return response
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('financeiro:despesa_list')

class DespesaPlanilhaView(LoginRequiredMixin, ListView):
    model = Despesa
    template_name = 'financeiro/partials/despesa_planilha.html'
    context_object_name = 'despesas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from tc_produtos.models import Fornecedor
        context['fornecedores'] = Fornecedor.objects.all().order_by('razao_social')
        return context

    def post(self, request, *args, **kwargs):
        fornecedores, numeros, vencimentos, valores = request.POST.getlist('fornecedor[]'), request.POST.getlist('numero[]'), request.POST.getlist('vencimento[]'), request.POST.getlist('valor[]')
        for i in range(len(fornecedores)):
            if fornecedores[i] and valores[i] and vencimentos[i]:
                Despesa.objects.create(
                    fornecedor_id=fornecedores[i], numero_documento=numeros[i],
                    data_vencimento=timezone.datetime.strptime(vencimentos[i], '%Y-%m-%d').date(),
                    data_competencia=timezone.now().date(),
                    valor_original=Decimal(valores[i].replace(',', '.')),
                    criado_por=request.user, origem="IMPORTACAO"
                )
        return redirect('financeiro:despesa_list')

class DespesaDetailView(LoginRequiredMixin, DetailView):
    model = Despesa
    template_name = 'financeiro/despesa_detail.html'
    context_object_name = 'despesa'

# --- OUTROS (CONTRATOS, XML, METAS) ---

class ContratoListView(LoginRequiredMixin, ListView):
    model = Contrato
    template_name = 'financeiro/contrato_list.html'
    context_object_name = 'contratos'

class ContratoCreateView(LoginRequiredMixin, CreateView):
    model = Contrato
    form_class = ContratoForm
    template_name = 'financeiro/contrato_form.html'
    success_url = reverse_lazy('financeiro:contrato_list')

@login_required
def importar_xml(request):
    if request.method == 'POST' and request.FILES.get('xml_file'):
        try:
            xml_file = request.FILES['xml_file']
            despesa, created = XMLInvoiceService.process_nfe(xml_file)
            return HttpResponse('<div class="alert alert-success">Importado!</div><script>location.reload();</script>')
        except Exception as e:
            return HttpResponse(f'<div class="alert alert-danger">Erro: {str(e)}</div>')
    return render(request, 'financeiro/importar_xml.html')

class MetaVendaListView(LoginRequiredMixin, ListView):
    model = MetaVenda
    template_name = 'financeiro/metavenda_list.html'

@login_required
def fatura_recibo(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    html_string = render_to_string('financeiro/partials/fatura_recibo_pdf.html', {'fatura': fatura, 'hoje': timezone.now()})
    return HttpResponse(html_string)

@login_required
def fatura_delete(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    
    if request.method == 'POST':
        fatura.delete()
        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'faturaAtualizada'
        return response
        
    # Retorna o partial de confirmação para o HTMX carregar no modal
    return render(request, 'financeiro/partials/fatura_confirm_delete.html', {'object': fatura})

# Adicione também a view de Delete caso não esteja completa
@login_required
def despesa_delete(request, pk):
    despesa = get_object_or_404(Despesa, pk=pk)
    if request.method == 'POST':
        despesa.delete()
        # Retorna um corpo vazio com o gatilho para atualizar a lista se necessário
        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'despesaExcluida'
        return response
    
    # Se for GET, renderiza o modal de confirmação que você enviou
    return render(request, 'financeiro/partials/confirm_delete_despesa.html', {'object': despesa})