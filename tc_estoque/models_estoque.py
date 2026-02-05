from django.db import models
from django.conf import settings

class ItemEstoque(models.Model):
    # Alterado para OneToOneField para resolver o Warning (fields.W342)
    # E para garantir que cada produto tenha apenas um registro de saldo no estoque
    produto = models.OneToOneField(
        'tc_produtos.Produto', 
        on_delete=models.CASCADE, 
        related_name='estoque',
        verbose_name="Produto"
    )
    quantidade_atual = models.PositiveIntegerField(default=0, verbose_name="Quantidade em Estoque")
    quantidade_minima = models.PositiveIntegerField(default=1, verbose_name="Estoque Mínimo")
    localizacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Localização Física")
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item de Estoque"
        verbose_name_plural = "Itens de Estoque"

    def __str__(self):
        return f"{self.produto.nome} - Qtd: {self.quantidade_atual}"

class MovimentacaoEstoque(models.Model):
    TIPO_MOVIMENTACAO = [
        ('ENT', 'Entrada'),
        ('SAI', 'Saída (Venda/Uso)'),
        ('AJU', 'Ajuste de Inventário'),
    ]

    item = models.ForeignKey(
        ItemEstoque, 
        on_delete=models.CASCADE, 
        related_name='movimentacoes'
    )
    tipo = models.CharField(max_length=3, choices=TIPO_MOVIMENTACAO)
    quantidade = models.IntegerField()
    data_movimentacao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT
    )
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"

    def __str__(self):
        return f"{self.tipo} - {self.item.produto.nome} ({self.quantidade})"