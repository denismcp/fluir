from django import forms
from .models import Fabricante, TipoAtivo, Ativo, Chamado, InteracaoChamado, OrdemServico, CategoriaOperacao
from tc_contratos.models import Contrato

class FabricanteForm(forms.ModelForm):
    class Meta:
        model = Fabricante
        fields = ['nome', 'site']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'site': forms.URLInput(attrs={'class': 'form-control'}),
        }

class TipoAtivoForm(forms.ModelForm):
    class Meta:
        model = TipoAtivo
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        # Campos atualizados conforme o models.py restaurado
        fields = [
            'produto_catalogo', 'cliente', 'fabricante', 'tipo', 
            'identificador_unico', 'data_aquisicao', 
            'data_expiracao_garantia', 'observacoes'
        ]
        widgets = {
            'produto_catalogo': forms.Select(attrs={'class': 'form-control select2'}),
            'cliente': forms.Select(attrs={'class': 'form-control select2'}),
            'fabricante': forms.Select(attrs={'class': 'form-control select2'}),
            'tipo': forms.Select(attrs={'class': 'form-control select2'}),
            'identificador_unico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serial / Service Tag'}),
            'data_aquisicao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_expiracao_garantia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = [
            'numero_os', 'cliente', 'responsavel', 'oportunidade_origem',
            'contrato_vinculado', 'titulo', 'descricao', 'status',
            'data_previsao_fim', 'data_conclusao'
        ]
        widgets = {
            'numero_os': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control select2'}),
            'responsavel': forms.Select(attrs={'class': 'form-control select2'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'data_previsao_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_conclusao': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garante que o campo carregue os contratos do novo app
        self.fields['contrato_vinculado'].queryset = Contrato.objects.all()

class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = [
            'cliente', 'solicitante_contato', 'ativo_vinculado', 
            'categoria', 'assunto', 'descricao_incidente', 
            'prioridade', 'status', 'atendente_responsavel'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control select2'}),
            'solicitante_contato': forms.Select(attrs={'class': 'form-control select2'}),
            'ativo_vinculado': forms.Select(attrs={'class': 'form-control select2'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_incidente': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'atendente_responsavel': forms.Select(attrs={'class': 'form-control select2'}),
        }

class InteracaoChamadoForm(forms.ModelForm):
    class Meta:
        model = InteracaoChamado
        fields = ['mensagem', 'e_nota_interna']
        widgets = {
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'e_nota_interna': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }