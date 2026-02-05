from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q # Necessário para constraints
import logging

# Configuração de logging (opcional, mas boa prática)
logger = logging.getLogger(__name__)

# ############################################################################
# 1. CMDB / INVENTÁRIO DE ATIVOS
# ############################################################################

class Fabricante(models.Model):
    """
    Fabricantes de hardware, software ou qualquer ativo rastreado no CMDB.
    Afastado do App PRODUTOS para manter a granularidade.
    """
    nome = models.CharField(max_length=150, unique=True, verbose_name="Nome do Fabricante")
    site = models.URLField(max_length=255, blank=True, null=True, verbose_name="Website")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Fabricante"
        verbose_name_plural = "Fabricantes"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class TipoAtivo(models.Model):
    """
    Tipos de Ativos (Ex: Servidor, Notebook, Switch, Licença)
    """
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Tipo de Ativo"
        verbose_name_plural = "Tipos de Ativos"

    def __str__(self):
        return self.nome

class Ativo(models.Model):
    """
    Instâncias reais dos ativos (Ex: O Notebook com Serial X).
    Este modelo conecta o Catálogo de Produtos à realidade operacional do cliente.
    """
    # Relacionamento com o Catálogo de Produtos
    # CORREÇÃO APLICADA ABAIXO: Adicionado related_name para evitar conflito com 'tc_produtos.Produto.ativo'
    produto_catalogo = models.ForeignKey(
        'tc_produtos.Produto', 
        on_delete=models.CASCADE,
        related_name='ativos_operacionais',
        verbose_name="Produto no Catálogo"
    )
    
    cliente = models.ForeignKey(
        'tc_crm.Cliente', # Ref: crm.Cliente (ou Account)
        on_delete=models.CASCADE,
        related_name='ativos_instalados',
        verbose_name="Cliente/Conta"
    )

    fabricante = models.ForeignKey(Fabricante, on_delete=models.SET_NULL, null=True)
    tipo = models.ForeignKey(TipoAtivo, on_delete=models.PROTECT)
    
    identificador_unico = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Serial/Service Tag/ID"
    )
    
    data_aquisicao = models.DateField(null=True, blank=True)
    data_expiracao_garantia = models.DateField(null=True, blank=True)
    
    observacoes = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Ativo (CMDB)"
        verbose_name_plural = "Ativos (CMDB)"

    def __str__(self):
        return f"{self.identificador_unico} - {self.produto_catalogo.nome}"

# ############################################################################
# 2. GESTÃO DE ORDENS DE SERVIÇO (OS)
# ############################################################################

class StatusOS(models.TextChoices):
    RASCUNHO = 'RAS', _('Rascunho')
    ABERTO = 'ABE', _('Aberto / Aguardando Atendimento')
    EM_ANDAMENTO = 'AND', _('Em Atendimento')
    AGUARDANDO_CLIENTE = 'AG_CLI', _('Aguardando Cliente')
    AGUARDANDO_TERCEIRO = 'AG_TER', _('Aguardando Peça/Terceiro')
    CONCLUIDO = 'CON', _('Concluído')
    CANCELADO = 'CAN', _('Cancelado')

class OrdemServico(models.Model):
    """
    O coração do módulo operacional. 
    Trabalha com Monolito Modular referenciando tc_crm e tc_financeiro.
    """
    # Identificação básica
    numero_os = models.CharField(max_length=20, unique=True, verbose_name="Nº da OS")
    cliente = models.ForeignKey(
        'tc_crm.Cliente', 
        on_delete=models.CASCADE,
        related_name='ordens_servico'
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Ref: core.Usuario
        on_delete=models.PROTECT,
        verbose_name="Responsável Operacional"
    )
    
    # Relações de Venda/Contrato de Origem
    oportunidade_origem = models.ForeignKey(
        'tc_crm.Oportunidade', # Ref: crm.Oportunidade
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Oportunidade de Origem"
    )
    contrato_vinculado = models.ForeignKey(
        'tc_contratos.Contrato', # Ref: financeiro.Contrato
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Contrato Recorrente"
    )

    # Detalhes da OS
    titulo = models.CharField(max_length=255, verbose_name="Título da Ordem de Serviço")
    descricao = models.TextField(verbose_name="Escopo do Trabalho")
    status = models.CharField(max_length=30, choices=StatusOS.choices, default=StatusOS.RASCUNHO, verbose_name="Status da OS")

    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_previsao_fim = models.DateField(null=True, blank=True, verbose_name="Previsão de Conclusão")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Fechamento Real")

    # Registros e Auditoria
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"OS {self.numero_os} - {self.cliente.razao_social}"

    def clean(self):
        # Regra SaaS: Não permite concluir OS sem data de conclusão
        if self.status == StatusOS.CONCLUIDO and not self.data_conclusao:
            from django.utils import timezone
            self.data_conclusao = timezone.now()

# ############################################################################
# 3. SERVICE DESK / GESTÃO DE CHAMADOS (TICKET SYSTEM)
# ############################################################################

class CategoriaOperacao(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoria de Operação"
        verbose_name_plural = "Categorias de Operações"

    def __str__(self):
        return self.nome

class Chamado(models.Model):
    PRIORIDADE_CHOICES = [\
        ('1', _('Crítica / Parada Total')),\
        ('2', _('Alta')),\
        ('3', _('Média / Normal')),\
        ('4', _('Baixa')),\
    ]

    STATUS_CHAMADO_CHOICES = [\
        ('NEW', _('Novo')),\
        ('ASS', _('Atribuído')),\
        ('PEN', _('Pendente / Aguardando')),\
        ('RES', _('Resolvido')),\
        ('CLO', _('Fechado')),\
    ]

    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    cliente = models.ForeignKey('tc_crm.Cliente', on_delete=models.CASCADE, related_name='chamados')
    solicitante_contato = models.ForeignKey('tc_crm.Contato', on_delete=models.SET_NULL, null=True, blank=True)
    
    ativo_vinculado = models.ForeignKey(Ativo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ativo com Problema")
    categoria = models.ForeignKey(CategoriaOperacao, on_delete=models.PROTECT)
    
    assunto = models.CharField(max_length=200)
    descricao_incidente = models.TextField()
    
    prioridade = models.CharField(max_length=1, choices=PRIORIDADE_CHOICES, default='3')
    status = models.CharField(max_length=3, choices=STATUS_CHAMADO_CHOICES, default='NEW')
    
    atendente_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='chamados_atribuidos')

    data_abertura = models.DateTimeField(auto_now_add=True)
    data_ultima_interacao = models.DateTimeField(auto_now=True)
    data_fechamento = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Chamado / Ticket"
        verbose_name_plural = "Chamados / Tickets"
        ordering = ['prioridade', '-data_abertura']

    def __str__(self):
        return f"#{self.ticket_id} - {self.assunto}"

class InteracaoChamado(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='interacoes')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    mensagem = models.TextField()
    data_registro = models.DateTimeField(auto_now_add=True)
    e_nota_interna = models.BooleanField(default=False, help_text="Se marcado, o cliente não visualiza esta interação.")

    class Meta:
        verbose_name = "Interação de Chamado"
        verbose_name_plural = "Interações de Chamados"

class SolucaoChamado(models.Model):
    chamado = models.OneToOneField(Chamado, on_delete=models.CASCADE, related_name='solucao')
    descricao_solucao = models.TextField()
    data_resolucao = models.DateTimeField(auto_now_add=True)
    tempo_gasto_minutos = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Solução de Chamado"
        verbose_name_plural = "Soluções de Chamados"