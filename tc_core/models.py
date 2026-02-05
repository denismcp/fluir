from django.db import models
from django.contrib.auth.models import AbstractUser, Permission # <-- VERIFIQUE ESTA LINHAfrom django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal

# Modelo para as Regras/Funções (Vendedor, Gestor, etc.)
class Regra(models.Model):
    """ Define os papéis/funções dos usuários no sistema. """
    permissoes = models.ManyToManyField(Permission, blank=True, verbose_name="Permissões Associadas")
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Regra")
    descricao = models.TextField(blank=True, verbose_name="Descrição do Papel") # <-- Adicionar ou confirmar a existência
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Regra (Papel)"
        verbose_name_plural = "Regras (Papéis)"

    def __str__(self):
        return self.nome

# Modelo de Usuário customizado, que herda do padrão Django.
class Usuario(AbstractUser):
    """ Modelo de Usuário estendido, usado em settings.AUTH_USER_MODEL. """
    regra = models.ForeignKey(
        Regra, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Regra/Papel"
    ) 
    
    indice_vendedor = models.PositiveIntegerField(
        default=0,
        verbose_name="Índice de Vendedor (para Iniciais Iguais)",
        help_text="Usado para o desempate na geração do ID da Proposta."
    ) 

    taxa_comissao = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Percentual de Comissão (%)",
        help_text="Ex: Digite 5.00 para 5%"
    ) 

    class Departamentos(models.TextChoices):
        COMERCIAL = 'comercial', 'Comercial / Vendas'
        FINANCEIRO = 'financeiro', 'Financeiro'
        OPERACIONAL = 'operacional', 'Operacional / Técnico'
        DIRETORIA = 'diretoria', 'Diretoria / ADM'
        OUTRO = 'outro', 'Outros'

    departamento = models.CharField(
        max_length=20, 
        choices=Departamentos.choices, 
        default=Departamentos.OUTRO,
        verbose_name="Departamento / Função"
    )
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['username']
        
    def __str__(self):
        return self.get_full_name() or self.username

class Vendedor(models.Model):
    """
    Novo objeto para Gestão Global. 
    Vincula um Usuário a um perfil comercial sem alterar o objeto Usuario legado.
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='perfil_vendedor'
    )
    telefone_comercial = models.CharField(max_length=20, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"
        ordering = ['usuario__first_name']

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

class MetaGlobal(models.Model):
    """
    Parametrização Global de Metas.
    """
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE, related_name='metas')
    mes_referencia = models.DateField(help_text="Primeiro dia do mês correspondente")
    valor_meta = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = "Meta de Venda"
        verbose_name_plural = "Metas de Vendas"
        unique_together = ['vendedor', 'mes_referencia']

    def __str__(self):
        return f"{self.vendedor} - {self.mes_referencia.strftime('%m/%Y')}"