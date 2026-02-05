import pandas as pd
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from tc_core.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils import processar_importacao_produtos


from .models import (
    Produto, Fornecedor, CategoriaProduto, KitMaterial, 
    ItemKit, FornecedorContato, FornecedorDocumento
)
from .forms import (
    ProdutoForm, FornecedorForm, CategoriaProdutoForm, 
    ItemKitFormSet, ImportarCSVForm, FornecedorContatoForm,
    FornecedorDocumentoForm
)
# ############################################################################
# PRODUTOS (Produto) - CRUD
# ############################################################################

class ProdutoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'tc_produtos.view_produto'
    model = Produto
    template_name = 'produtos/produto_list.html'
    context_object_name = 'produtos'

    def get_queryset(self):
        # Filtra apenas PRODUTOS físicos
        queryset = Produto.objects.exclude(tipo_produto='SERV')
        status = self.request.GET.get('status')
        if status == 'ativos':
            queryset = queryset.filter(ativo=True)
        elif status == 'inativos':
            queryset = queryset.filter(ativo=False)
        return queryset.order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # CORREÇÃO: Filtramos os totais para contar apenas PRODUTOS (não serviços)
        base_qs = Produto.objects.exclude(tipo_produto='SERV')
        context['total_todos'] = base_qs.count()
        context['total_ativos'] = base_qs.filter(ativo=True).count()
        context['total_inativos'] = base_qs.filter(ativo=False).count()
        
        context['current_status'] = self.request.GET.get('status', 'todos')
        context['page_heading'] = 'Catálogo de Produtos'
        return context

class ProdutoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'tc_produtos.add_produto'
    model = Produto
    form_class = ProdutoForm
    
    def get_success_url(self):
        return reverse_lazy('produtos:produto_list')

    def get_template_names(self):
        if self.request.htmx:
            return ['produtos/partials/produto_form_modal.html'] 
        return ['produtos/produto_form.html']

    def form_valid(self, form):
        # GARANTIA: Todo item criado por aqui nasce como Produto Físico
        form.instance.tipo_produto = 'PROD'
        self.object = form.save()
        
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form) 

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.htmx:
            # Se houver erro, retorna apenas o fragmento do form (com os erros)
            # para ser injetado na modal novamente
            return response 
        return response

class ProdutoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'tc_produtos.change_produto'
    model = Produto
    form_class = ProdutoForm
    
    # Define o sucesso para casos em que o HTMX não for usado
    def get_success_url(self):
        return reverse_lazy('produtos:produto_list')

    def get_template_names(self):
        # Se for HTMX, ele carrega o fragmento da modal. 
        # Se não for, ele procura a página full (que causa o erro 500 atual)
        if self.request.htmx:
            return ['produtos/partials/produto_form_modal.html']
        return ['produtos/produto_form.html']

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Resposta 204 indica sucesso sem conteúdo, 
            # e HX-Refresh força a atualização da lista ao fundo
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class ProdutoDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'tc_produtos.view_produto'
    model = Produto
    template_name = 'produtos/produto_detail.html'
    context_object_name = 'produto'

class ProdutoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'tc_produtos.delete_produto'
    model = Produto
    template_name = 'produtos/partials/produto_confirm_delete_modal.html'
    
    def get_success_url(self):
        return reverse_lazy('produtos:produto_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # --- TRAVA DE SEGURANÇA ---
        # Verifica se o produto está em algum Kit ou tem histórico de preços
        tem_vinculo_kit = self.object.itemkit_set.exists()
        tem_vinculo_preco = self.object.precos_fornecedores.exists()
        
        # Verifica se há movimentação no estoque (ajuste conforme seu app tc_estoque)
        # Nota: Se o modelo tc_estoque.ItemEstoque existe, verificamos aqui
        tem_estoque = False
        if hasattr(self.object, 'itemestoque'): 
            tem_estoque = True

        if tem_vinculo_kit or tem_vinculo_preco or tem_estoque:
            if self.request.htmx:
                # Se houver vínculo, recarrega a modal com uma mensagem de erro
                return render(request, self.template_name, {
                    'object': self.object,
                    'erro_integridade': True,
                    'motivo': "Este produto possui movimentação de estoque ou vínculos com Kits/Preços."
                })
        
        # Se não houver vínculos, procede com a exclusão
        return self.form_valid(None)

    def form_valid(self, form):
        self.object.delete()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return HttpResponseRedirect(self.get_success_url())

# ############################################################################
# IMPORTAÇÃO DE PRODUTOS E SERVIÇOS PARA O CRM
# ############################################################################
class ProdutoSheetView(LoginRequiredMixin, ListView):
    model = Produto
    template_name = 'produtos/produto_sheet.html'
    context_object_name = 'itens'

    def get_queryset(self):
        return Produto.objects.exclude(tipo_produto='SERV').order_by('nome')

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get('export')
        if export_format in ['xlsx', 'csv']:
            return self.export_data(export_format)
        return super().get(request, *args, **kwargs)

    def export_data(self, format):
        queryset = self.get_queryset()
        data = []
        for item in queryset:
            data.append({
                'id': item.id,
                'codigo_interno': item.codigo_interno,
                'nome': item.nome,
                'preco_venda_padrao': float(item.preco_venda_padrao or 0),
                'modificado_por': item.modificado_por.username if item.modificado_por else '',
                'modificado_em': item.atualizado_em.strftime('%d/%m/%Y %H:%M') if item.atualizado_em else '',
                'criado_por': item.criado_por.username if item.criado_por else '',
                'criado_em': item.criado_em.strftime('%d/%m/%Y %H:%M') if item.criado_em else '',
            })
        
        df = pd.DataFrame(data)
        
        if format == 'xlsx':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=produtos_export.xlsx'
            df.to_excel(response, index=False, engine='openpyxl')
        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=produtos_export.csv'
            df.to_csv(response, index=False, encoding='utf-8-sig')
            
        return response

class ServicoSheetView(ProdutoSheetView): # Herda a lógica de exportação
    template_name = 'produtos/produto_sheet.html'
    context_object_name = 'itens'

    def get_queryset(self):
        return Produto.objects.filter(tipo_produto='SERV').order_by('nome')

    def export_data(self, format):
        # Sobrescreve apenas o nome do arquivo para serviços
        response = super().export_data(format)
        filename = f"servicos_export.{format}"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

@login_required
@require_POST
def update_produto_cell(request):
    try:
        obj_id = request.POST.get('id')
        campo = request.POST.get('campo')
        valor = request.POST.get('valor')
        
        produto = get_object_or_404(Produto, id=obj_id)
        
        # Se for campo de texto, converte para maiúsculo antes de salvar
        campos_texto = ['nome', 'codigo_interno', 'descricao_curta']
        if campo in campos_texto:
            valor = str(valor).upper()
        
        if campo == 'preco_venda_padrao':
            valor = valor.replace('R$', '').replace(' ', '').replace(',', '.')
        
        setattr(produto, campo, valor)
        produto.modificado_por = request.user
        produto.save() # O save() do model também reforçará o upper()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def importar_arquivo_produto(request):
    """
    Recebe o arquivo de planilha e processa a importação de Produtos ou Serviços
    """
    if 'arquivo' not in request.FILES:
        messages.error(request, "Nenhum arquivo enviado para importação.")
        return redirect(request.META.get('HTTP_REFERER', 'produtos:produto_sheet'))

    arquivo = request.FILES['arquivo']
    is_servico = 'servico' in request.path
    
    sucesso, resultado = processar_importacao_produtos(arquivo, request.user, is_servico)
    
    if sucesso:
        # Renderiza a página de relatório detalhado
        return render(request, 'produtos/import_result.html', {
            'resultado': resultado,
            'is_servico': is_servico
        })
    else:
        messages.error(request, f"Falha crítica na importação: {resultado}")
        return redirect(request.META.get('HTTP_REFERER', 'produtos:produto_sheet'))

#Para gerar o modelo do arquivo de importação
def baixar_template_importacao(request):
    # Definimos as colunas que o nosso novo utils.py espera
    colunas = ['nome', 'preco_venda_padrao', 'categoria', 'codigo_interno', 'descricao_curta']
    df = pd.DataFrame(columns=colunas)
    
    # Criamos o arquivo Excel em memória
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=modelo_importacao.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    
    return response

class ImportarServicosView(LoginRequiredMixin, FormView):
    template_name = 'produtos/importar_servicos.html'
    form_class = ImportarCSVForm # Use o seu formulário de upload de arquivo
    success_url = reverse_lazy('produtos:servico_list')

    def form_valid(self, form):
        arquivo = self.request.FILES.get('arquivo')
        # Chamada para a função que processará o CSV especificamente como serviços
        resultado = processar_servicos_csv(arquivo, self.request.user)
        
        messages.success(self.request, f'Importação concluída: {resultado["sucesso"]} serviços criados.')
        return super().form_valid(form)


# ############################################################################
# FORNECEDORES (Fornecedor) - CRUD
# ############################################################################

class FornecedorListView(LoginRequiredMixin, ListView):
    model = Fornecedor
    template_name = 'produtos/fornecedor_list.html'
    context_object_name = 'fornecedores'
    ordering = ['razao_social']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Captura o termo de busca do GET
        q = self.request.GET.get('q')
        
        if q:
            # Filtra por Razão Social, Nome Fantasia, CNPJ ou nome da Categoria
            queryset = queryset.filter(
                Q(razao_social__icontains=q) |
                Q(nome_fantasia__icontains=q) |
                Q(cnpj__icontains=q) |
                Q(categorias_fornecidas__nome__icontains=q)
            ).distinct()
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Fornecedores'
        # Mantém o termo de busca no campo após o reload para UX
        context['search_term'] = self.request.GET.get('q', '')
        return context

class FornecedorCreateView(LoginRequiredMixin, CreateView):
    model = Fornecedor
    form_class = FornecedorForm
    # AJUSTE O CAMINHO ABAIXO:
    template_name = 'produtos/partials/fornecedor_form_modal.html' 
    success_url = reverse_lazy('produtos:fornecedor_list')

    def form_valid(self, form):
        if self.request.htmx:
            self.object = form.save()
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class FornecedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Fornecedor
    form_class = FornecedorForm
    # AJUSTE O CAMINHO ABAIXO:
    template_name = 'produtos/partials/fornecedor_form_modal.html'
    success_url = reverse_lazy('produtos:fornecedor_list')

    def form_valid(self, form):
        if self.request.htmx:
            self.object = form.save()
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class FornecedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Fornecedor
    form_class = FornecedorForm
    # Definimos a modal como template padrão para evitar o erro de "TemplateDoesNotExist"
    template_name = 'produtos/partials/fornecedor_form_modal.html'
    success_url = reverse_lazy('produtos:fornecedor_list')

    def get_template_names(self):
        # Independente de ser HTMX ou não, usamos a modal para evitar o erro 500
        return ['produtos/partials/fornecedor_form_modal.html']

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('HX-Request'):
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class FornecedorDetailView(LoginRequiredMixin, DetailView):
    model = Fornecedor
    template_name = 'produtos/fornecedor_detail.html'
    context_object_name = 'fornecedor'

class FornecedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Fornecedor
    success_url = reverse_lazy('produtos:fornecedor_list')
    template_name = 'produtos/fornecedor_confirm_delete.html'

def fornecedor_contato_add(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == "POST":
        form = FornecedorContatoForm(request.POST)
        if form.is_valid():
            contato = form.save(commit=False)
            contato.fornecedor = fornecedor
            contato.save()
            form.save_m2m() # Importante para as categorias ManyToMany
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = FornecedorContatoForm()
    
    # Caminho ajustado para a pasta partials
    return render(request, 'produtos/partials/fornecedor_contato_modal.html', {
        'form': form,
        'fornecedor': fornecedor
    })

def fornecedor_contato_edit(request, pk):
    contato = get_object_or_404(FornecedorContato, pk=pk)
    # Importante: O contexto deve conter 'contato' e o form com a instância
    if request.method == "POST":
        form = FornecedorContatoForm(request.POST, instance=contato)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = FornecedorContatoForm(instance=contato)
    
    return render(request, 'produtos/partials/fornecedor_contato_modal.html', {
        'form': form,
        'fornecedor': contato.fornecedor,
        'contato': contato # Sem isso, o formulário na modal não sabe quem editar
    })

def fornecedor_contato_delete(request, pk):
    contato = get_object_or_404(FornecedorContato, pk=pk)
    
    if request.method == "POST":
        contato.delete()
        # Após deletar, recarrega a página de detalhes
        return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    
    # Renderiza o novo template de confirmação profissional
    return render(request, 'produtos/partials/contato_confirm_delete_modal.html', {
        'contato': contato
    })

# ############################################################################
# CATEGORIA DE PRODUTOS (CategoriaProduto)
# ############################################################################

class CategoriaProdutoListView(LoginRequiredMixin, ListView):
    model = CategoriaProduto
    template_name = 'produtos/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['nome']

class CategoriaProdutoCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaProduto
    form_class = CategoriaProdutoForm
    template_name = 'produtos/categoria_form.html' # Fallback para não-HTMX

    def get_template_names(self):
        if self.request.htmx:
            return ['produtos/partials/categoria_form_modal.html']
        return [self.template_name]

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            # Envia o refresh para atualizar a lista de categorias ou produtos
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class CategoriaProdutoUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaProduto
    form_class = CategoriaProdutoForm
    success_url = reverse_lazy('produtos:categoria_list')
    template_name = 'produtos/categoria_form.html'

class CategoriaProdutoDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaProduto
    success_url = reverse_lazy('produtos:categoria_list')
    template_name = 'produtos/categoria_confirm_delete.html'

# ############################################################################
# KIT DE MATERIAIS (KITS)
# ############################################################################

class KitMaterialListView(LoginRequiredMixin, ListView):
    model = KitMaterial
    template_name = 'produtos/kit_list.html'
    context_object_name = 'kits'
    
    def get_queryset(self):
        # Usamos 'itens_kit' que é o related_name definido no seu models.py
        # O prefetch_related carrega kit + itens + produto em uma única leva
        return KitMaterial.objects.all().prefetch_related('itens_kit__produto')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_heading'] = 'Kits de Materiais / Combos'
        return context

class KitMaterialCreateView(LoginRequiredMixin, CreateView):
    model = KitMaterial
    fields = ['nome', 'descricao']
    template_name = 'produtos/partials/kit_form_modal.html'
    success_url = reverse_lazy('produtos:kit_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['produtos_com_preco'] = Produto.objects.filter(ativo=True).only('id', 'custo_padrao', 'preco_venda_padrao')
        if self.request.POST:
            data['itens'] = ItemKitFormSet(self.request.POST)
        else:
            data['itens'] = ItemKitFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        itens = context['itens']
        if itens.is_valid():
            self.object = form.save()
            itens.instance = self.object
            itens.save()
            
            if self.request.headers.get('HX-Request'):
                response = HttpResponse(status=204)
                response['HX-Refresh'] = 'true'
                return response
            return super().form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Impede o cache para garantir que o script de cálculo sempre rode do zero
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

class KitMaterialUpdateView(LoginRequiredMixin, UpdateView):
    model = KitMaterial
    fields = ['nome', 'descricao']
    template_name = 'produtos/partials/kit_form_modal.html'
    success_url = reverse_lazy('produtos:kit_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        # Injetamos custo e venda para o novo painel de lucro
        data['produtos_com_preco'] = Produto.objects.filter(ativo=True).only('id', 'custo_padrao', 'preco_venda_padrao')
        
        # CORREÇÃO DA INDENTAÇÃO ABAIXO:
        if self.request.POST:
            data['itens'] = ItemKitFormSet(self.request.POST, instance=self.object)
        else:
            data['itens'] = ItemKitFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        itens = context['itens']
        if itens.is_valid():
            self.object = form.save()
            itens.save()
            
            if self.request.headers.get('HX-Request'):
                response = HttpResponse(status=204)
                response['HX-Refresh'] = 'true'
                return response
            return super().form_valid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Impede o cache para garantir que o script de cálculo sempre rode do zero
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

# ############################################################################
# SERVIÇOS
# ############################################################################

class ServicoListView(LoginRequiredMixin, ListView):
    model = Produto
    template_name = 'produtos/servico_list.html' # Aponta para o novo template
    context_object_name = 'servicos'

    def get_queryset(self):
        # Filtra apenas o que é SERVIÇO para a lista de serviços
        queryset = Produto.objects.filter(tipo_produto='SERV')
        status = self.request.GET.get('status')
        if status == 'ativos':
            queryset = queryset.filter(ativo=True)
        elif status == 'inativos':
            queryset = queryset.filter(ativo=False)
        return queryset.order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = Produto.objects.filter(tipo_produto='SERV')
        context['total_todos'] = base_qs.count()
        context['total_ativos'] = base_qs.filter(ativo=True).count()
        context['total_inativos'] = base_qs.filter(ativo=False).count()
        context['current_status'] = self.request.GET.get('status', 'todos')
        return context

class ServicoDetailView(LoginRequiredMixin, DetailView):
    model = Produto
    template_name = 'produtos/servico_detail.html' # Template independente
    context_object_name = 'servico'

class ServicoCreateView(LoginRequiredMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/partials/servico_form_modal.html' # Partial independente
    success_url = reverse_lazy('produtos:servico_list')

    def form_valid(self, form):
        form.instance.tipo_produto = 'SERV' # Garante que salve como serviço
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

class ServicoUpdateView(LoginRequiredMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/partials/servico_form_modal.html'
    success_url = reverse_lazy('produtos:servico_list')

    def form_valid(self, form):
        self.object = form.save()
        if self.request.htmx:
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        return super().form_valid(form)

# --- VIEWS DE PLANILHA E IMPORTAÇÃO ---
class ProdutoImportView(LoginRequiredMixin, FormView):
    template_name = 'produtos/produto_import.html'
    form_class = ImportarCSVForm
    success_url = reverse_lazy('produtos:produto_list')

    def form_valid(self, form):
        arquivo = self.request.FILES.get('arquivo')
        # Chama a função unificada com is_servico_context=False
        sucesso, logs = processar_importacao_produtos(arquivo, self.request.user, is_servico_context=False)
        
        if sucesso:
            return render(self.request, 'produtos/import_result.html', {
                'resultado': logs, 
                'contexto': 'Produtos'
            })
        
        messages.error(self.request, logs)
        return self.form_invalid(form)

class ServicoSheetView(ServicoListView):
    template_name = 'produtos/servico_sheet.html' # Template de planilha independente

class ServicoImportView(LoginRequiredMixin, FormView):
    template_name = 'produtos/servico_import.html'
    form_class = ImportarCSVForm
    success_url = reverse_lazy('produtos:servico_list')

    def form_valid(self, form):
        arquivo = self.request.FILES.get('arquivo')
        # Chama a MESMA função unificada, mas com is_servico_context=True
        sucesso, logs = processar_importacao_produtos(arquivo, self.request.user, is_servico_context=True)
        
        if sucesso:
            return render(self.request, 'produtos/import_result.html', {
                'resultado': logs, 
                'contexto': 'Serviços',
                'is_servico': True
            })
        
        messages.error(self.request, logs)
        return self.form_invalid(form)


# ############################################################################
# DOCUMENTOS
# ############################################################################

def fornecedor_documento_add(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == "POST":
        form = FornecedorDocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.fornecedor = fornecedor
            doc.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = FornecedorDocumentoForm()
    return render(request, 'produtos/partials/documento_upload_modal.html', {'form': form, 'fornecedor': fornecedor})

def fornecedor_documento_delete(request, pk):
    doc = get_object_or_404(FornecedorDocumento, pk=pk)
    if request.method == "POST":
        doc.delete()
        return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    return render(request, 'produtos/partials/contato_confirm_delete_modal.html', {'contato': doc})

def fornecedor_documento_delete(request, pk):
    documento = get_object_or_404(FornecedorDocumento, pk=pk)
    if request.method == "POST":
        documento.delete()
        return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    return render(request, 'produtos/partials/documento_confirm_delete_modal.html', {'documento': documento})