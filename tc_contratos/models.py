# tc_contratos/models.py
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords

class Contrato(models.Model):
    TIPO_CONTRATO_CHOICES = [
        ('REC', 'Receita (Cliente)'),
        ('DESP', 'Despesa (Consumo/Fornecedor)'),
    ]

    SITUACAO_CHOICES = [
        ('ELAB', 'Em Elaboração'),
        ('ASSIN', 'Aguardando Assinatura'),
        ('ATIVO', 'Ativo'),
        ('SUSP', 'Suspenso'),
        ('ENCER', 'Encerrado/Finalizado'),
    ]

    INDICE_REAJUSTE_CHOICES = [
        ('IGPM', 'IGP-M'),
        ('IPCA', 'IPCA'),
        ('FIXO', 'Sem Reajuste (Fixo)'),
    ]

    numero_contrato = models.CharField(max_length=50, unique=True, editable=False, verbose_name="Número do Contrato")
    tipo_contrato = models.CharField(max_length=5, choices=TIPO_CONTRATO_CHOICES, default='REC', verbose_name="Tipo de Contrato")

    # Vínculos
    oportunidade = models.OneToOneField('tc_crm.Oportunidade', on_delete=models.SET_NULL, null=True, blank=True, related_name='contrato_vinculado')
    cliente = models.ForeignKey('tc_crm.Cliente', on_delete=models.PROTECT, null=True, blank=True, related_name='contratos_receita')
    fornecedor = models.ForeignKey('tc_crm.Fornecedor', on_delete=models.PROTECT, null=True, blank=True, related_name='contratos_despesa')

    # Especificações e Vigência
    objeto_contrato = models.TextField(verbose_name="Objeto e Especificações")
    valor_mensal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Mensal")
    dia_vencimento = models.PositiveIntegerField(default=10, verbose_name="Dia de Vencimento")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(null=True, blank=True, verbose_name="Data de Término")
    indice_reajuste = models.CharField(max_length=10, choices=INDICE_REAJUSTE_CHOICES, default='IPCA', verbose_name="Índice")
    data_proxima_renovacao = models.DateField(null=True, blank=True, verbose_name="Próxima Renovação")
    
    situacao = models.CharField(max_length=10, choices=SITUACAO_CHOICES, default='ELAB', verbose_name="Situação")
    
    # Auditoria
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='contratos_criados')
    modificado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='contratos_modificados')
    criado_em = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Contrato"
        ordering = ['-criado_em']

    def save(self, *args, **kwargs):
        # 1. Lógica de Nomeação Automática (CTR- + CÓDIGO DA PROPOSTA)
        if not self.numero_contrato and self.oportunidade:
            # Busca a proposta com status 'Aceita/Ganha' conforme os logs do CRM
            proposta = self.oportunidade.proposta_set.filter(status='Aceita/Ganha').first()
            
            if not proposta:
                # Fallback para a última proposta gerada caso não haja uma marcada como ganha
                proposta = self.oportunidade.proposta_set.order_by('-data_criacao').first()
            
            if proposta:
                # Captura o id_proposta (ex: 20260105T001) para rastreabilidade
                codigo = proposta.id_proposta if hasattr(proposta, 'id_proposta') else proposta.id
                self.numero_contrato = f"CTR-{codigo}"
            else:
                self.numero_contrato = f"CTR-OPT-{self.oportunidade.id}"
        
        # 2. Auto-preenchimento do cliente via Oportunidade
        if self.tipo_contrato == 'REC' and not self.cliente and self.oportunidade:
            self.cliente = self.oportunidade.cliente
            
        # 3. Herança automática da Data de Início (se estiver vazio)
        if not self.data_inicio and self.oportunidade and self.oportunidade.data_fechamento_real:
            self.data_inicio = self.oportunidade.data_fechamento_real

        super().save(*args, **kwargs)

    def __str__(self):
    # Correção: Cliente usa razao_social, não nome
        entidade = self.cliente.razao_social if self.cliente else (self.fornecedor.razao_social if self.fornecedor else "S/N")
        return f"{self.id} - {self.tipo_contrato}"