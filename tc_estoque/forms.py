from django import forms
from .models import ItemEstoque, MovimentacaoEstoque
from django.apps import apps

# ############################################################################
# FORMS - ESTOQUE
# ############################################################################

class ItemEstoqueForm(forms.ModelForm):
    """ Formulário para cadastrar ou editar um ItemEstoque (local e produto). """
    class Meta:
        model = ItemEstoque
        # Saldo ('quantidade') é gerenciado apenas por MovimentacaoEstoque, não editado diretamente.
        fields = ['produto', 'localizacao']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-control custom-select'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra 'Produto' para mostrar apenas itens que não são Serviços (TipoProduto.ESTOQUE_PROPRIO)
        ProdutoModel = apps.get_model('produtos', 'Produto')
        self.fields['produto'].queryset = ProdutoModel.objects.filter(
            tipo_produto=ProdutoModel.TipoProduto.ESTOQUE_PROPRIO
        )
        # Aplica a classe padrão do Select2
        self.fields['produto'].widget.attrs.update({'class': 'form-control custom-select'})


class MovimentacaoEstoqueForm(forms.ModelForm):
    """ Formulário para registrar uma Movimentação (Entrada/Saída/Ajuste). """
    class Meta:
        model = MovimentacaoEstoque
        # Os campos 'item_estoque', 'responsavel' e 'data_movimentacao' são definidos na View.
        fields = ['tipo', 'quantidade', 'observacao'] 
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control custom-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }