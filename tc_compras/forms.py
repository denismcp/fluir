from django import forms
from .models import CentroCusto, RequisicaoCompra, ItemRequisicao, PedidoCompra, RecebimentoItem
from django.apps import apps
from decimal import Decimal # Importar Decimal para valores monetários

# Acesso aos modelos de outros Apps
# É necessário garantir que estes imports funcionem (via app_label.Model)
try:
    ProdutoModel = apps.get_model('tc_produtos', 'Produto')
    ServicoModel = apps.get_model('tc_servicos', 'Servico')
    FornecedorModel = apps.get_model('tc_produtos', 'Fornecedor')
except LookupError:
    # Fallback para evitar erro na definição do Form se a App ainda não estiver pronta.
    ProdutoModel = None 
    ServicoModel = None
    FornecedorModel = None

# ############################################################################
# CENTRO DE CUSTO
# ############################################################################

class CentroCustoForm(forms.ModelForm):
    class Meta:
        model = CentroCusto
        fields = ['nome', 'codigo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
        }

# ############################################################################
# REQUISIÇÃO DE COMPRA (SOLICITAÇÃO)
# ############################################################################

class RequisicaoCompraForm(forms.ModelForm):
    class Meta:
        model = RequisicaoCompra
        # O campo 'solicitante' é preenchido automaticamente na view
        fields = ['centro_custo', 'data_limite', 'descricao_geral']
        widgets = {
            'centro_custo': forms.Select(attrs={'class': 'form-control custom-select'}),
            'data_limite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descricao_geral': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializa Select2 para CentroCusto
        self.fields['centro_custo'].widget.attrs.update({'class': 'form-control custom-select select2-centrocusto'})


# ############################################################################
# ITEM DA REQUISIÇÃO
# ############################################################################

class ItemRequisicaoForm(forms.ModelForm):
    class Meta:
        model = ItemRequisicao
        fields = ['produto', 'servico', 'nome_customizado', 'especificacao', 
                  'quantidade', 'preco_unitario_estimado']
        widgets = {
            # Classes Select2 para a interatividade HTMX/JS
            'produto': forms.Select(attrs={'class': 'form-control custom-select select2-produto'}),
            'servico': forms.Select(attrs={'class': 'form-control custom-select select2-servico'}),
            'nome_customizado': forms.TextInput(attrs={'class': 'form-control'}),
            'especificacao': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'preco_unitario_estimado': forms.TextInput(attrs={'class': 'form-control currency-mask', 'value': '0.00'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if ProdutoModel:
            self.fields['produto'].queryset = ProdutoModel.objects.all().order_by('nome')
        if ServicoModel:
            self.fields['servico'].queryset = ServicoModel.objects.all().order_by('nome')


# ############################################################################
# PEDIDO DE COMPRA (PO) & RECEBIMENTO
# ############################################################################

class PedidoCompraForm(forms.ModelForm):
    class Meta:
        model = PedidoCompra
        fields = ['fornecedor', 'custo_frete']
        widgets = {
            'fornecedor': forms.Select(attrs={'class': 'form-control custom-select select2-fornecedor'}),
            'custo_frete': forms.TextInput(attrs={'class': 'form-control currency-mask', 'value': '0.00'}),
        }

class RecebimentoItemForm(forms.ModelForm):
    class Meta:
        model = RecebimentoItem
        fields = ['quantidade_recebida', 'observacao'] 
        widgets = {
            'quantidade_recebida': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'observacao': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }