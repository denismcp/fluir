from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory
from .models import Produto, CategoriaProduto, Fornecedor, FornecedorContato, FornecedorDocumento, KitMaterial, ItemKit 

# Conjunto de formulários para itens do Kit
ItemKitFormSet = inlineformset_factory(
    KitMaterial, 
    ItemKit,
    fields=['produto', 'quantidade'],
    extra=1,
    can_delete=True,
    widgets={
        'produto': forms.Select(attrs={'class': 'form-control'}),
        'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
    }
)

# ############################################################################
# PRODUTOS
# ############################################################################

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'nome', 'codigo_interno', 'ean_gtin',
            'categoria', 'tipo_produto',
            'custo_padrao', 'preco_venda_padrao', 
            'metodo_precificacao', 'markup_padrao', 
            'dias_garantia', 'lead_time_dias', 
            'descricao_curta', 'ativo'
        ]
        # ADICIONE ESTE BLOCO ABAIXO:
        labels = {
            'codigo_interno': 'Código Interno / SKU',
        }
        # MANTENHA O RESTANTE IGUAL:
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_interno': forms.TextInput(attrs={'class': 'form-control'}),
            'ean_gtin': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Código de Barras (13 ou 14 dígitos)',
                'maxlength': '14'
            }),
            'categoria': forms.Select(attrs={'class': 'form-control select2'}),
            'tipo_produto': forms.Select(attrs={'class': 'form-control'}),
            'custo_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_venda_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'metodo_precificacao': forms.Select(attrs={'class': 'form-control'}),
            'markup_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dias_garantia': forms.NumberInput(attrs={'class': 'form-control'}),
            'lead_time_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'descricao_curta': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_ean_gtin(self):
        ean = self.cleaned_data.get('ean_gtin')
        if ean:
            ean = ean.strip()
            if not ean.isdigit():
                raise forms.ValidationError("O código EAN deve conter apenas números.")
            if len(ean) not in [8, 12, 13, 14]:
                raise forms.ValidationError("O código de barras deve ter 8, 12, 13 ou 14 dígitos.")
        return ean

    def clean(self):
        cleaned_data = super().clean()
        metodo = cleaned_data.get('metodo_precificacao')
        custo = cleaned_data.get('custo_padrao')
        markup = cleaned_data.get('markup_padrao')
        preco_venda = cleaned_data.get('preco_venda_padrao')

        if metodo == 'MARC' and custo and markup:
            preco_sugerido = custo * (1 + (markup / Decimal('100')))
            if not preco_venda or preco_venda == 0:
                cleaned_data['preco_venda_padrao'] = preco_sugerido
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo_interno'].required = False

# ############################################################################
# IMPORTAÇÃO DE PRODUTOS E SERVIÇOS
# ############################################################################
class ProdutoInlineForm(forms.ModelForm):
    class Meta:
        model = Produto
        # Alterado 'codigo' para 'codigo_interno' 
        # Removido 'estoque_atual' pois não consta no seu models.py
        fields = ['codigo_interno', 'nome', 'preco_venda_padrao']

class ImportarCSVForm(forms.Form):
    arquivo = forms.FileField(
        label="Selecione o arquivo CSV",
        help_text="O arquivo deve conter as colunas: nome e preco_venda",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
# ############################################################################
# FORNECEDORES
# ############################################################################

class FornecedorForm(forms.ModelForm):
    # O campo isento_ie já está aqui como BooleanField
    isento_ie = forms.BooleanField(required=False, label="Isento de IE?", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Fornecedor
        fields = [
            'razao_social', 'nome_fantasia', 'cnpj', 
            'inscricao_estadual', 'isento_ie', 'regime_tributario',
            'tipo_fornecedor', 'cep', 'endereco', 'numero', 'complemento', 
            'bairro', 'cidade', 'uf', 'contato_principal', 
            'telefone', 'email', 'e_distribuidor',
            'categorias_fornecidas', 'dados_bancarios', 'informacoes_contrato',
            'comissionamento_regra', 'observacoes'
        ]
        widgets = {
            'regime_tributario': forms.Select(attrs={'class': 'form-control'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18', 'placeholder': '00.000.000/0000-00'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_fornecedor': forms.Select(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'uf': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '2'}),
            'contato_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do contato na empresa'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '15'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'e_distribuidor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'categorias_fornecidas': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'dados_bancarios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'comissionamento_regra': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        # Remove caracteres não numéricos (pontos, barra, traço)
        cnpj = ''.join(filter(str.isdigit, cnpj))

        if not cnpj or len(cnpj) != 14:
            raise forms.ValidationError("O CNPJ deve conter exatamente 14 números.")

        # Lista de CNPJs inválidos conhecidos
        if cnpj in [s * 14 for s in "0123456789"]:
            raise forms.ValidationError("CNPJ inválido.")

        # Validação dos Dígitos Verificadores
        def calcula_digito(cnpj, pesos):
            soma = sum(int(a) * b for a, b in zip(cnpj, pesos))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)

        # Pesos para o primeiro e segundo dígito
        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        digito_1 = calcula_digito(cnpj[:12], pesos_1)
        digito_2 = calcula_digito(cnpj[:13], pesos_2)

        if cnpj[-2:] != (digito_1 + digito_2):
            raise forms.ValidationError("CNPJ inválido. Verifique os números digitados.")

        return cnpj

#Fornecedor Contato
class FornecedorContatoForm(forms.ModelForm):
    class Meta:
        model = FornecedorContato
        fields = ['nome', 'cargo', 'email', 'telefone', 'categorias', 'eh_principal']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'categorias': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'eh_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# ############################################################################
# CATEGORIAS
# ############################################################################

class CategoriaProdutoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProduto
        fields = ['nome', 'descricao', 'slug']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }


# ############################################################################
# DOCUMENTOS
# ############################################################################

class FornecedorDocumentoForm(forms.ModelForm):
    class Meta:
        model = FornecedorDocumento
        fields = ['nome', 'arquivo', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Contrato Social, Proposta...'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control-file'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }