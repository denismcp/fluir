from django import forms
from .models import Servico, CategoriaServico # Assumindo models.py já existe e contém Servico/CategoriaServico

# ############################################################################
# SERVIÇOS
# ############################################################################

class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = [
            'nome', 'codigo_servico', 'categoria', 'tipo_servico',
            'preco_unitario_padrao', 'unidade_medida', 'descricao_curta'
        ]
        widgets = {
            'descricao_curta': forms.Textarea(attrs={'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-control custom-select'}),
            'tipo_servico': forms.Select(attrs={'class': 'form-control custom-select'}),
            # Campos de valor (assumindo a classe 'currency-mask' para formatação em pt-BR)
            'preco_unitario_padrao': forms.TextInput(attrs={'class': 'form-control currency-mask'}), 
            'unidade_medida': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CategoriaServicoForm(forms.ModelForm):
    class Meta:
        model = CategoriaServico
        fields = ['nome', 'descricao', 'aliquota_iss']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'aliquota_iss': forms.TextInput(attrs={'class': 'form-control percent-mask'}),
        }