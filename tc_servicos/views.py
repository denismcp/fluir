from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from tc_core.mixins import PermissionRequiredMixin

from .models import Servico, CategoriaServico 
from .forms import ServicoForm, CategoriaServicoForm

# ############################################################################
# SERVIÇOS (Servico) - CRUD
# ############################################################################

class ServicoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'servicos.view_servico'
    model = Servico
    template_name = 'servicos/servico_list.html'
    context_object_name = 'servicos'
    ordering = ['nome']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Catálogo de Serviços'
        return context

class ServicoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'servicos.add_servico'
    model = Servico
    form_class = ServicoForm
    
    def get_success_url(self):
        # Redireciona para a listagem após o CRUD via HTMX
        return reverse('servicos:servico_list')

    def get_template_names(self):
        # Utiliza o template modal para requisições HTMX
        if self.request.htmx:
            return ['servicos/partials/servico_form_modal.html'] 
        return ['servicos/servico_form.html']

class ServicoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'servicos.change_servico'
    model = Servico
    form_class = ServicoForm
    
    def get_success_url(self):
        return reverse('servicos:servico_list')

    def get_template_names(self):
        if self.request.htmx:
            return ['servicos/partials/servico_form_modal.html'] 
        return ['servicos/servico_form.html']

class ServicoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'servicos.view_servico'
    model = Servico
    template_name = 'servicos/servico_detail.html'
    context_object_name = 'servico'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = f'Detalhes: {self.object.nome}'
        return context

class ServicoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'servicos.delete_servico'
    model = Servico
    success_url = reverse_lazy('servicos:servico_list')
    template_name = 'servicos/partials/servico_confirm_delete_modal.html'

# ############################################################################
# CATEGORIAS DE SERVIÇOS (CategoriaServico) - Listagem
# ############################################################################

class CategoriaServicoListView(LoginRequiredMixin, ListView):
    model = CategoriaServico
    template_name = 'servicos/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['nome']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Categorias de Serviços'
        return context