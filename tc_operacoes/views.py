from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from tc_core.mixins import PermissionRequiredMixin

from .models import Fabricante, TipoAtivo, Ativo, Chamado, CategoriaOperacao, OrdemServico, InteracaoChamado, SolucaoChamado
from .forms import FabricanteForm, TipoAtivoForm, AtivoForm, ChamadoForm, InteracaoChamadoForm, OrdemServicoForm

# ############################################################################
# CHAMADOS (ITSM) - CRUD
# ############################################################################

class ChamadoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'operacoes.view_chamado'
    model = Chamado
    template_name = 'operacoes/chamado_list.html'
    context_object_name = 'chamados'
    ordering = ['-prioridade', '-data_criacao'] # Exemplo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Chamados de Suporte (ITSM)'
        return context

class ChamadoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'operacoes.add_chamado'
    model = Chamado
    form_class = ChamadoForm
    
    def form_valid(self, form):
        # Define o usuário logado como responsável inicial, se não for definido no form
        if not form.instance.responsavel:
            form.instance.responsavel = self.request.user
        return super().form_valid(form)
        
    def get_template_names(self):
        if self.request.htmx:
            return ['operacoes/partials/chamado_form_modal.html']
        return ['operacoes/chamado_form.html']
    
    def get_success_url(self):
        return reverse('operacoes:chamado_detail', kwargs={'pk': self.object.pk})

class ChamadoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'operacoes.view_chamado'
    model = Chamado
    template_name = 'operacoes/chamado_detail.html'
    context_object_name = 'chamado'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = f'Chamado # {self.object.pk}'
        context['interacao_form'] = InteracaoChamadoForm()
        context['interacoes'] = self.object.interacoes.all().order_by('data_criacao')
        # Adiciona a solução se existir
        try:
            context['solucao'] = self.object.solucao
        except SolucaoChamado.DoesNotExist:
            context['solucao'] = None
        return context

class ChamadoUpdateView(LoginRequiredMixin, UpdateView):
    model = Chamado
    form_class = ChamadoForm
    
    def get_template_names(self):
        if self.request.htmx:
            return ['operacoes/partials/chamado_form_modal.html']
        return ['operacoes/chamado_form.html']
    
    def get_success_url(self):
        return reverse('operacoes:chamado_detail', kwargs={'pk': self.object.pk})

class InteracaoChamadoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # Apenas quem pode interagir com chamados
    permission_required = 'operacoes.add_interacaochamado'
    model = InteracaoChamado
    form_class = InteracaoChamadoForm
    
    def form_valid(self, form):
        chamado = get_object_or_404(Chamado, pk=self.kwargs['chamado_pk'])
        form.instance.chamado = chamado
        form.instance.autor = self.request.user
        
        response = super().form_valid(form)
        
        # O HTMX espera um fragmento para substituir a lista de interações
        if self.request.htmx:
             # Retorna o template que renderiza a lista completa de interações atualizada
             return render(self.request, 'operacoes/partials/interacao_list_fragment.html', {'chamado': chamado, 'interacoes': chamado.interacoes.all().order_by('data_criacao')})
        
        return response

class SolucaoChamadoCreateView(LoginRequiredMixin, CreateView):
    model = SolucaoChamado
    fields = ['descricao_solucao']
    template_name = 'operacoes/partials/solucao_form_modal.html'
    
    def form_valid(self, form):
        chamado = get_object_or_404(Chamado, pk=self.kwargs['chamado_pk'])
        form.instance.chamado = chamado
        form.instance.autor = self.request.user
        
        # O save() do modelo SolucaoChamado se encarrega de mudar o status do Chamado para 'Resolvido'
        response = super().form_valid(form)
        
        if self.request.htmx:
             # Força o refresh da página Chamado Detail para carregar o bloco de solução
             return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
        return response

# ############################################################################
# ATIVOS (CMDB) - CRUD
# ############################################################################

class AtivoListView(LoginRequiredMixin, ListView):
    model = Ativo
    template_name = 'operacoes/ativo_list.html'
    context_object_name = 'ativos'
    ordering = ['nome']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Inventário de Ativos (CMDB)'
        return context

class AtivoCreateView(LoginRequiredMixin, CreateView):
    model = Ativo
    form_class = AtivoForm
    
    def get_template_names(self):
        if self.request.htmx:
            return ['operacoes/partials/ativo_form_modal.html']
        return ['operacoes/ativo_form.html']
    
    def get_success_url(self):
        return reverse_lazy('operacoes:ativo_list')

class AtivoUpdateView(LoginRequiredMixin, UpdateView):
    model = Ativo
    form_class = AtivoForm
    
    def get_template_names(self):
        if self.request.htmx:
            return ['operacoes/partials/ativo_form_modal.html']
        return ['operacoes/ativo_form.html']
    
    def get_success_url(self):
        return reverse('operacoes:ativo_detail', kwargs={'pk': self.object.pk})

class AtivoDetailView(LoginRequiredMixin, DetailView):
    model = Ativo
    template_name = 'operacoes/ativo_detail.html'
    context_object_name = 'ativo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = f'Ativo: {self.object.nome}'
        return context

# ############################################################################
# ORDEM DE SERVIÇO (OS) - CRUD
# ############################################################################

class OrdemServicoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'operacoes.view_ordemservico'
    model = OrdemServico
    template_name = 'operacoes/ordemservico_list.html'
    context_object_name = 'ordens_servico'
    ordering = ['-data_criacao']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Ordens de Serviço'
        return context

class OrdemServicoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'operacoes.add_ordemservico'
    model = OrdemServico
    form_class = OrdemServicoForm
    
    def get_template_names(self):
        if self.request.htmx:
            return ['operacoes/partials/ordemservico_form_modal.html']
        return ['operacoes/ordemservico_form.html']
    
    def get_success_url(self):
        return reverse_lazy('operacoes:ordemservico_list')

class OrdemServicoDetailView(LoginRequiredMixin, DetailView):
    model = OrdemServico
    template_name = 'operacoes/ordemservico_detail.html'
    context_object_name = 'ordem'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = f'OS-{self.object.pk}: {self.object.titulo}'
        return context
        
# ############################################################################
# CADASTROS MESTRES
# ############################################################################

class FabricanteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'operacoes.view_fabricante'
    model = Fabricante
    template_name = 'operacoes/fabricante_list.html'
    context_object_name = 'fabricantes'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Fabricantes de Ativos'
        return context

class CategoriaOperacaoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'operacoes.view_categoriaoperacao'
    model = CategoriaOperacao
    template_name = 'operacoes/categoria_operacao_list.html'
    context_object_name = 'categorias'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Categorias de Chamados/OS'
        return context