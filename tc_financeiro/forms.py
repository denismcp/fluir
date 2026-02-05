from django import forms
from .models import Fatura, Despesa, MetaVenda
from tc_produtos.models import Fornecedor 
from tc_crm.models import Cliente
from django.utils.translation import gettext_lazy as _

class PremiumFormMixin:
    """Mixin para injetar classes Bootstrap automaticamente com design limpo"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                # Design Ultra Premium: Bordas leves e arredondadas
                current_class = field.widget.attrs.get('class', '')
                if 'select2' not in current_class:
                    field.widget.attrs['class'] = 'form-control rounded-12 shadow-none border-light'
                else:
                    # Garante que o select2 mantenha a classe de arredondamento
                    field.widget.attrs['class'] = 'form-control select2 rounded-12'

class FaturaForm(PremiumFormMixin, forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by('razao_social'),
        widget=forms.Select(attrs={'class': 'select2'})
    )

    class Meta:
        model = Fatura
        # numero_documento REMOVIDO: agora é automático via save() no Model
        fields = [
            'cliente', 'descricao', 'tipo_titulo', 
            'data_vencimento', 'data_competencia', 'valor_original', 
            'valor_desconto', 'forma_pagamento', 'observacoes'
        ]
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date', 'required': 'true'}),
            'data_competencia': forms.DateInput(attrs={'type': 'date', 'required': 'true'}),
            'valor_original': forms.NumberInput(attrs={'step': '0.01', 'style': 'font-weight: 800; color: #4e73df;'}),
            'valor_desconto': forms.NumberInput(attrs={'step': '0.01'}), 
            'observacoes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Estas notas aparecerão no recibo oficial...'}),
        }

class DespesaForm(PremiumFormMixin, forms.ModelForm):
    fornecedor = forms.ModelChoiceField(
        queryset=Fornecedor.objects.all().order_by('razao_social'),
        required=True,
        widget=forms.Select(attrs={'class': 'select2'})
    )
    
    class Meta:
        model = Despesa
        fields = [
            'descricao', 'fornecedor', 'numero_documento', 'data_vencimento', 
            'data_competencia', 'valor_original', 'valor_juros', 'valor_multa',
            'valor_acrescimo', 'valor_desconto', # <-- Sincronizados com a Model
            'forma_pagamento', 'observacoes', 'pago', 'data_liquidacao'
        ]
        widgets = {
            'data_vencimento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control rounded-12'}
            ),
            'data_competencia': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control rounded-12'}
            ),
            'data_liquidacao': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control rounded-12'}
            ),
            'valor_original': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'font-weight-bold'}),
            'valor_juros': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_multa': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_acrescimo': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_desconto': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
            'pago': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_numero_documento(self):
        nr = self.cleaned_data.get('numero_documento')
        if nr and nr.startswith('-'):
            raise forms.ValidationError("O número do documento não pode começar com valor negativo.")
        return nr

class ContratoForm(PremiumFormMixin, forms.ModelForm):
    class Meta:
        from tc_contratos.models import Contrato
        model = Contrato
        fields = '__all__'
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
        }