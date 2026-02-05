from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import render
from django.db.models import Sum, DecimalField
from django.db.models.functions import ExtractYear, ExtractMonth
from tc_core.mixins import PermissionRequiredMixin

from .models import CanalMarketing, GastoMarketing
from .forms import CanalMarketingForm, GastoMarketingForm

# ############################################################################
# GASTOS DE MARKETING (GastoMarketing) - CRUD
# ############################################################################

class GastoMarketingListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'marketing.view_gastomarketing'
    model = GastoMarketing
    template_name = 'marketing/gastomarketing_list.html'
    context_object_name = 'gastos'
    ordering = ['-ano', '-mes', 'canal__nome']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Rastreamento de Gastos (CAC)'
        
        # Agrupa os gastos por Mês/Ano para exibir um total no dashboard
        gastos_agregados = GastoMarketing.objects.values('ano', 'mes').annotate(
            total_mensal=Sum('valor_gasto', output_field=DecimalField())
        ).order_by('-ano', '-mes')
        
        context['gastos_agregados'] = gastos_agregados[:12] # Últimos 12 meses
        return context

class GastoMarketingCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'marketing.add_gastomarketing'
    model = GastoMarketing
    form_class = GastoMarketingForm
    
    def get_template_names(self):
        if self.request.htmx:
            return ['marketing/partials/gasto_form_modal.html'] 
        return ['marketing/gasto_form.html']
    
    def get_success_url(self):
        return reverse_lazy('marketing:gastomarketing_list')

class GastoMarketingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'marketing.change_gastomarketing'
    model = GastoMarketing
    form_class = GastoMarketingForm
    
    def get_template_names(self):
        if self.request.htmx:
            return ['marketing/partials/gasto_form_modal.html'] 
        return ['marketing/gasto_form.html']
    
    def get_success_url(self):
        return reverse_lazy('marketing:gastomarketing_list')

# ############################################################################
# CADASTRO MESTRE: CANAIS DE MARKETING (CanalMarketing)
# ############################################################################

class CanalMarketingListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'marketing.view_canalmarketing'
    model = CanalMarketing
    template_name = 'marketing/canalmarketing_list.html'
    context_object_name = 'canais'
    ordering = ['nome']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Canais de Marketing'
        return context

class CanalMarketingCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'marketing.add_canalmarketing'
    model = CanalMarketing
    form_class = CanalMarketingForm
    
    def get_template_names(self):
        if self.request.htmx:
            return ['marketing/partials/canal_form_modal.html'] 
        return ['marketing/canal_form.html']
    
    def get_success_url(self):
        return reverse_lazy('marketing:canalmarketing_list')