from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from django.db.models import F, Sum, DecimalField
from decimal import Decimal
from django.conf import settings
from django.utils.text import slugify

import os
from django.utils import timezone

# O App tc_core contém o modelo Usuario
Usuario = settings.AUTH_USER_MODEL 

# ############################################################################
# GRUPO 1: Fornecedores e Categorias
# ############################################################################

class Fornecedor(models.Model):
    TIPO_CHOICES = [
        ('FORN', _('Fornecedor Padrão')),
        ('DIST', _('Distribuidor/Atacadista')),
    ]

    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=255, verbose_name="Nome Fantasia", blank=True, null=True)
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    inscricao_estadual = models.CharField(max_length=20, blank=True, null=True)
    isento_ie = models.BooleanField(default=False, verbose_name="Isento de IE")
    regime_tributario = models.CharField(max_length=50, 
        choices=[('simples', 'Simples Nacional'), ('real', 'Lucro Real'), ('presumido', 'Lucro Presumido'), ('mei', 'MEI')
        ],
        blank=True, null=True,
        verbose_name="Regime Tributário"
    )
    cep = models.CharField(max_length=9, verbose_name="CEP", blank=True, null=True)
    endereco = models.CharField(max_length=255, verbose_name="Endereço", blank=True, null=True)
    numero = models.CharField(max_length=20, verbose_name="Número", blank=True, null=True)
    complemento = models.CharField(max_length=100, verbose_name="Complemento", blank=True, null=True)
    bairro = models.CharField(max_length=100, verbose_name="Bairro", blank=True, null=True)
    cidade = models.CharField(max_length=100, verbose_name="Cidade", blank=True, null=True)
    uf = models.CharField(max_length=2, verbose_name="UF", blank=True, null=True)
    contato_principal = models.CharField(max_length=100, blank=True, null=True, verbose_name="Contato Principal")
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    tipo_fornecedor = models.CharField(max_length=4, choices=TIPO_CHOICES, default='FORN', verbose_name="Tipo de Fornecedor")
    e_distribuidor = models.BooleanField(default=False, verbose_name="É Distribuidor?")
    categorias_fornecidas = models.ManyToManyField('CategoriaProduto', blank=True, verbose_name="Categorias Atendidas")
    dados_bancarios = models.TextField(blank=True, null=True, verbose_name="Dados Bancários")
    informacoes_contrato = models.TextField(blank=True, null=True, verbose_name="Informações de Contrato")
    comissionamento_regra = models.TextField(blank=True, null=True, verbose_name="Regra de Comissionamento (Distribuidores)")
    
    # Notas Gerais
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações Gerais")
    # O campo history já existe no seu código
    avaliacao_pontualidade = models.IntegerField(default=5, verbose_name="Nota Pontualidade (1-5)")
    avaliacao_preco = models.IntegerField(default=5, verbose_name="Nota Preço (1-5)")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome_fantasia if self.nome_fantasia else self.razao_social

class FornecedorContato(models.Model):
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE, related_name='contatos')
    nome = models.CharField(max_length=255)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    categorias = models.ManyToManyField('CategoriaProduto', blank=True, verbose_name="Categorias que atende")
    eh_principal = models.BooleanField(default=False, verbose_name="Contato Principal")

    def __str__(self):
        return f"{self.nome} ({self.fornecedor})"

class CategoriaProduto(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=150, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Categoria de Produto"
        verbose_name_plural = "Categorias de Produtos"

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


# ############################################################################
# GRUPO 2: Cadastro de Produtos e Serviços
# ############################################################################

class Produto(models.Model):
    TIPO_PRODUTO_CHOICES = [
        ('PROD', _('Produto Físico')),
        ('SERV', _('Serviço/Mão de Obra')),
        ('SOFT', _('Software/Licença')),
    ]

    METODO_PRECIFICACAO_CHOICES = [
        ('MARC', _('Markup sobre Custo')),
        ('FIXO', _('Preço Fixo')),
    ]

    nome = models.CharField(max_length=255, verbose_name="Nome do Produto/Serviço")
    codigo_interno = models.CharField(max_length=50, unique=True, verbose_name="Código Interno/SKU")
    ean_gtin = models.CharField(max_length=14, blank=True, null=True, verbose_name="EAN/GTIN")
    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.SET_NULL, null=True, related_name='produtos')
    tipo_produto = models.CharField(max_length=4, choices=TIPO_PRODUTO_CHOICES, default='PROD')
    
    custo_padrao = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Custo Padrão")
    preco_venda_padrao = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Preço de Venda")
    metodo_precificacao = models.CharField(max_length=4, choices=METODO_PRECIFICACAO_CHOICES, default='MARC')
    markup_padrao = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Ex: 30.00 para 30%")

    descricao_curta = models.TextField(blank=True, null=True)
    dias_garantia = models.IntegerField(default=0, verbose_name="Dias de Garantia")
    lead_time_dias = models.IntegerField(default=0, verbose_name="Lead Time (Dias)")
    
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True, null=True, blank=True)

    history = HistoricalRecords()

    # INFORMAÇÕES PARA IMPORTAÇÃO E RASTREABILIDADE:
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='produtos_criados'
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='produtos_modificados'
    )

    class Meta:
        verbose_name = "Produto/Serviço"
        verbose_name_plural = "Produtos e Serviços"

    def __str__(self):
        return f"{self.codigo_interno} - {self.nome}"

    def save(self, *args, **kwargs):
        # Força campos de texto para MAIÚSCULO
        if self.nome:
            self.nome = self.nome.upper()
        if self.codigo_interno:
            self.codigo_interno = self.codigo_interno.upper()
        if self.descricao_curta:
            self.descricao_curta = self.descricao_curta.upper()

        # Geração Automática de Código Interno (SKU)
        if not self.codigo_interno:
            if self.categoria:
                prefixo = self.categoria.nome[:3].upper()
            else:
                # Define prefixo padrão baseado no tipo
                if self.tipo_produto == 'SERV':
                    prefixo = "SER"
                elif self.tipo_produto == 'SOFT':
                    prefixo = "SFT"
                else:
                    prefixo = "PRD"
            
            ultimo_item = Produto.objects.filter(
                codigo_interno__startswith=prefixo
            ).order_by('codigo_interno').last()

            if ultimo_item and ultimo_item.codigo_interno[-3:].isdigit():
                ultimo_numero = int(ultimo_item.codigo_interno[-3:])
                novo_numero = str(ultimo_numero + 1).zfill(3)
            else:
                novo_numero = "001"

            self.codigo_interno = f"{prefixo}-{novo_numero}"
        
        # Gera slug apenas se não existir
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nome)
            
        super().save(*args, **kwargs)


class PrecoFornecedor(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='precos_fornecedores')
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE)
    preco_custo = models.DecimalField(max_digits=12, decimal_places=2)
    moeda = models.CharField(max_length=3, default='BRL')

    class Meta:
        verbose_name = "Preço por Fornecedor"
        verbose_name_plural = "Preços por Fornecedor"

    def __str__(self):
        return f"{self.produto.nome} - {self.fornecedor.razao_social}"

# ############################################################################
# GRUPO 3: Kit de Materiais
# ############################################################################

class KitMaterial(models.Model):
    nome = models.CharField(max_length=150, unique=True, verbose_name="Nome do Kit")
    descricao = models.TextField(blank=True, null=True)
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Kit de Material"
        verbose_name_plural = "Kits de Materiais"

    @property
    def custo_total_estimado(self):
        total = self.itens_kit.aggregate(
            total_custo=Sum(F('produto__custo_padrao') * F('quantidade'), output_field=DecimalField())
        )['total_custo']
        return total.quantize(Decimal("0.01")) if total else Decimal('0.00')

    def __str__(self):
        return self.nome

class ItemKit(models.Model):
    kit = models.ForeignKey(KitMaterial, on_delete=models.CASCADE, related_name='itens_kit')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)

    # ADICIONE ESTE BLOCO:
    @property
    def subtotal_custo(self):
        if self.produto and self.quantidade:
            return (self.produto.custo_padrao * self.quantidade).quantize(Decimal("0.01"))
        return Decimal("0.00")

    def __str__(self):
        return f"{self.quantidade} x {self.produto.nome}"



# ############################################################################
# GRUPO 4: Gestão de Documentos
# ############################################################################
def path_documento_fornecedor(instance, filename):
    ext = filename.split('.')[-1]
    novo_nome = f"DOC_{slugify(instance.fornecedor.razao_social)}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('fornecedores/documentos/', novo_nome)
    
class FornecedorDocumento(models.Model):
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE, related_name='documentos')
    nome = models.CharField(max_length=255, verbose_name="Nome do Documento")
    arquivo = models.FileField(upload_to='fornecedores/documentos/', verbose_name="Arquivo")
    data_upload = models.DateTimeField(auto_now_add=True)
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")

    def __str__(self):
        return f"{self.nome} - {self.fornecedor}"