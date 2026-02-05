from django import forms
from .models import Cliente, Contato, Oportunidade, Atividade, Proposta, Fornecedor

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'cnpj_cpf', 'razao_social', 'nome_fantasia', 
            'email_corporativo', 'telefone_principal', # ADICIONADOS AQUI
            'cep', 'endereco', 'cidade', 'estado',
            'regime_tributario', 'tipo_contribuinte', 
            'limite_credito', 'bloquear_faturamento', 'etiquetas' 
        ]
        widgets = {
            'cnpj_cpf': forms.TextInput(attrs={'class': 'form-control cnpj-mask', 'autofocus': 'autofocus'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            # NOVOS WIDGETS
            'email_corporativo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'empresa@exemplo.com'}),
            'telefone_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 0000-0000'}),
            
            'cep': forms.TextInput(attrs={'class': 'form-control cep-mask'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'regime_tributario': forms.Select(attrs={'class': 'form-control'}),
            'tipo_contribuinte': forms.Select(attrs={'class': 'form-control'}),
            'limite_credito': forms.NumberInput(attrs={'class': 'form-control'}), 
            'bloquear_faturamento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'etiquetas': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        }

# --- FORMULÁRIO DE CONTATO CORRIGIDO ---
class ContatoForm(forms.ModelForm):
    class Meta:
        model = Contato
        # Inseridos todos os campos que existem no Model e no HTML
        # Removido 'cliente' pois a View trata o vínculo automaticamente
        fields = [
            'primeiro_nome', 'sobrenome', 'email', 
            'telefone', 'celular', 'departamento', 
            'e_whatsapp', 'e_principal', 'papel_na_decisao'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garante que campos não obrigatórios no banco não travem o form
        self.fields['email'].required = True
        self.fields['primeiro_nome'].required = True
        self.fields['celular'].required = False
        self.fields['telefone'].required = False
        self.fields['sobrenome'].required = False
        self.fields['departamento'].required = False

# --- FIM DA CORREÇÃO DO CONTATO ---

class OportunidadeForm(forms.ModelForm):
    class Meta:
        model = Oportunidade
        fields = [
            'nome', 'cliente', 'responsavel', 'etapa', 
            'valor_estimado', 'data_fechamento_prevista', 'tipo_oportunidade'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'responsavel': forms.Select(attrs={'class': 'form-control'}),
            'etapa': forms.Select(attrs={'class': 'form-control'}),
            'valor_estimado': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo_oportunidade': forms.Select(attrs={'class': 'form-control'}),
            'data_fechamento_prevista': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['tipo_atividade', 'assunto', 'descricao', 'data_hora', 'concluida']
        widgets = {
            'tipo_atividade': forms.Select(attrs={'class': 'form-control'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resumo da atividade'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data_hora': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'concluida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.data_hora:
            self.initial['data_hora'] = self.instance.data_hora.strftime('%Y-%m-%dT%H:%M')

class PropostaForm(forms.ModelForm):
    class Meta:
        model = Proposta
        fields = [
            'entendimento_necessidade', 'descricao_tecnica', 'descricao_comercial',
            'prazo_entrega', 'validade_dias', 'vigencia_contrato', 'forma_pagamento',
            'valor_frete', 'valor_desconto', 'status' # Campos sincronizados com o Model
        ]
        widgets = {
            'entendimento_necessidade': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'descricao_tecnica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'descricao_comercial': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prazo_entrega': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 30 dias'}),
            'validade_dias': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 05'}),
            'vigencia_contrato': forms.TextInput(attrs={'class': 'form-control'}),
            'forma_pagamento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            
            # NOVOS WIDGETS PARA VALORES FINANCEIROS
            'valor_frete': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0,00'
            }),
            'valor_desconto': forms.NumberInput(attrs={
                'class': 'form-control text-danger', 
                'step': '0.01', 
                'placeholder': '0,00'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define todos os campos como opcionais para evitar travamento de fluxo no CRM
        for field in self.fields:
            self.fields[field].required = False

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['cnpj', 'razao_social']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'