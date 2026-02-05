from django.db import models
from django.conf import settings

class ItemEstoque(models.Model):
    # Ajustado para tc_crm.Produto (Nome real no seu arquivo)
    produto = models.OneToOneField(
        'tc_crm.Produto', 
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
    TIPO_MOVIMENTACAO = [('ENT', 'Entrada'), ('SAI', 'Saída'), ('AJU', 'Ajuste')]
    item = models.ForeignKey(ItemEstoque, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=3, choices=TIPO_MOVIMENTACAO)
    quantidade = models.IntegerField()
    data_movimentacao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Movimentação de Estoque"