from django.db import models
from decimal import Decimal
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _

# --- CATEGORIAS DE SERVIÇOS ---

class CategoriaServico(models.Model):
    """
    Categorias para Serviços (Ex: Consultoria, Suporte, Implantação).
    """
    nome = models.CharField(max_length=150, unique=True, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    # Adicionando um campo para regras de negócio específicas de tributação, se houver
    aliquota_iss = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'), 
        verbose_name="Alíquota Padrão ISS (%)"
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Categoria de Serviço"
        verbose_name_plural = "Categorias de Serviços"
        ordering = ['nome']

    def __str__(self):
        return self.nome

# --- SERVIÇOS ---

class Servico(models.Model):
    """
    Itens de Serviço (mão de obra, suporte, licença de uso - sem estoque).
    """
    class TipoServico(models.TextChoices):
        RECORRENTE = 'recorrente', _('Recorrente (Mensal/Anual)')
        UNICO = 'unico', _('Único (Projeto/Hora)')
        
    # --- IDENTIFICAÇÃO ---
    nome = models.CharField(max_length=255, verbose_name="Nome do Serviço")
    codigo_servico = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Código do Serviço")
    descricao_curta = models.TextField(verbose_name="Descrição Curta (para Propostas)")
    
    # --- CLASSIFICAÇÃO E TIPO ---
    categoria = models.ForeignKey(CategoriaServico, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria")
    tipo_servico = models.CharField(
        max_length=20, 
        choices=TipoServico.choices, 
        default=TipoServico.UNICO, 
        verbose_name="Tipo de Serviço"
    )

    # --- PRECIFICAÇÃO ---
    preco_unitario_padrao = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'), 
        verbose_name="Preço Unitário Padrão (R$)"
    )
    unidade_medida = models.CharField(
        max_length=20, 
        default='un', 
        verbose_name="Unidade de Medida",
        help_text="Ex: H (hora), Mês, Un (unidade), Pj (projeto)"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ['nome']

    def __str__(self):
        return self.nome