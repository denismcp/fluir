from django.db import models
from simple_history.models import HistoricalRecords
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

# ############################################################################
# 1. ENTIDADES MESTRAS DO MÓDULO MARKETING
# ############################################################################

class CanalMarketing(models.Model):
    """
    Define os canais de aquisição, campanhas ou plataformas para rastreamento de gastos.
    Ex: Google Ads, Mídias Sociais, Eventos, Cold Call.
    """
    nome = models.CharField(max_length=150, unique=True, verbose_name="Nome do Canal")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição e Objetivo")
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Canal de Marketing"
        verbose_name_plural = "Canais de Marketing"
        ordering = ['nome']

    def __str__(self):
        return self.nome

# ############################################################################
# 2. GASTOS DE MARKETING (Para Cálculo de CAC)
# ############################################################################

class GastoMarketing(models.Model):
    """
    Registra os gastos mensais por canal, utilizados para o cálculo do Custo de Aquisição de Cliente (CAC).
    """
    canal = models.ForeignKey(
        CanalMarketing, 
        on_delete=models.PROTECT, 
        verbose_name="Canal de Marketing"
    )
    
    # O rastreamento é feito por ano e mês para facilitar relatórios de tendência e CAC mensal.
    ano = models.PositiveIntegerField(verbose_name="Ano de Referência")
    mes = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 13)], 
        verbose_name="Mês de Referência"
    )
    
    valor_gasto = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'), 
        verbose_name="Valor Total Gasto (R$)"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Gasto de Marketing"
        verbose_name_plural = "Gastos de Marketing"
        # Regra CRUCIAL: Garante que não haja duplicidade de gastos para o mesmo canal/mês/ano
        unique_together = ('canal', 'ano', 'mes')
        ordering = ['-ano', '-mes', 'canal__nome']

    def __str__(self):
        return f"{self.canal.nome} - {self.mes}/{self.ano} ({self.valor_gasto} R$)"

    def clean(self):
        """ Validação extra para garantir que o mês está no intervalo correto. """
        if not 1 <= self.mes <= 12:
            raise ValidationError({'mes': _('O mês deve estar entre 1 e 12.')})