from django import forms
from .models import CanalMarketing, GastoMarketing
from django.utils.translation import gettext_lazy as _

# ############################################################################
# CADASTROS MESTRES
# ############################################################################

class CanalMarketingForm(forms.ModelForm):
    class Meta:
        model = CanalMarketing
        fields = ['nome', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

# ############################################################################
# GASTOS DE MARKETING
# ############################################################################

class GastoMarketingForm(forms.ModelForm):
    class Meta:
        model = GastoMarketing
        # O campo 'mes' e 'ano' são usados para rastreamento mensal
        fields = ['canal', 'ano', 'mes', 'valor_gasto']
        widgets = {
            'canal': forms.Select(attrs={'class': 'form-control custom-select select2-canal'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020}),
            # Select padrão para mês
            'mes': forms.Select(attrs={'class': 'form-control custom-select'}),
            # Campo de valor monetário
            'valor_gasto': forms.TextInput(attrs={'class': 'form-control currency-mask', 'value': '0.00'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sobrescreve as choices padrão do campo 'mes' para ter o nome dos meses
        MESES_CHOICES = [
            (1, _('Janeiro')), (2, _('Fevereiro')), (3, _('Março')), 
            (4, _('Abril')), (5, _('Maio')), (6, _('Junho')), 
            (7, _('Julho')), (8, _('Agosto')), (9, _('Setembro')), 
            (10, _('Outubro')), (11, _('Novembro')), (12, _('Dezembro'))
        ]
        self.fields['mes'].choices = MESES_CHOICES
        # Adiciona a classe Select2
        self.fields['canal'].widget.attrs.update({'class': 'form-control custom-select select2'})