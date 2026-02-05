from django import forms
from django.urls import reverse_lazy
from .models import Contrato
from tc_crm.models import Oportunidade

class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = [
            'tipo_contrato', 'situacao', 'oportunidade', 
            'cliente', 'fornecedor', 'objeto_contrato', 
            'valor_mensal', 'dia_vencimento', 'indice_reajuste',
            'data_inicio', 'data_fim', 'data_proxima_renovacao'
        ]
        widgets = {
            'tipo_contrato': forms.Select(attrs={'class': 'form-control'}),
            'situacao': forms.Select(attrs={'class': 'form-control'}),
            'oportunidade': forms.Select(attrs={'class': 'form-control select2'}),
            'cliente': forms.Select(attrs={'class': 'form-control select2'}),
            'fornecedor': forms.Select(attrs={'class': 'form-control select2'}),
            'objeto_contrato': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dia_vencimento': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '31'}),
            'indice_reajuste': forms.Select(attrs={'class': 'form-control'}),
            # CORREÇÃO: Adicionado format='%Y-%m-%d' para que o navegador reconheça o valor na edição
            'data_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'data_proxima_renovacao': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['data_inicio'].widget.attrs.update({
            'hx-get': reverse_lazy('contratos:calcular_renovacao'),
            'hx-trigger': 'input, change',
            'hx-swap': 'none', # O script JS cuida da distribuição dos valores
        })

        # Gatilhos HTMX
        self.fields['cliente'].widget.attrs.update({
            'hx-get': reverse_lazy('contratos:carregar_oportunidades'),
            'hx-target': '#id_oportunidade',
            # Escuta tanto a mudança padrão quanto o evento específico do Select2
            'hx-trigger': 'change, select2:select' 
        })
        
        self.fields['oportunidade'].widget.attrs.update({
            'hx-get': reverse_lazy('contratos:obter_valor_proposta'),
            'hx-target': '#id_valor_mensal',
            'hx-trigger': 'change',
            'hx-swap': 'none',
        })

        # Lógica para manter o QuerySet de Oportunidades ativo na edição ou erro de validação
        cliente_id = None
        if 'cliente' in self.data:
            cliente_id = self.data.get('cliente')
        elif self.instance.pk and self.instance.cliente:
            cliente_id = self.instance.cliente.pk

        if cliente_id:
            try:
                self.fields['oportunidade'].queryset = Oportunidade.objects.filter(cliente_id=cliente_id)
            except (ValueError, TypeError):
                self.fields['oportunidade'].queryset = Oportunidade.objects.none()
        else:
            if not self.instance.pk:
                self.fields['oportunidade'].queryset = Oportunidade.objects.none()

        # Configuração de campos opcionais
        self.fields['cliente'].required = False
        self.fields['fornecedor'].required = False
        self.fields['oportunidade'].required = False
        self.fields['data_fim'].required = False
        self.fields['data_proxima_renovacao'].required = False